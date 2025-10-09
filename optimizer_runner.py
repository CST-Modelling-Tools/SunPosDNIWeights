# File: optimizer_runner.py

import sys
import csv
import subprocess
import shutil
import time
from pathlib import Path
from fireworks import LaunchPad
from firetasks.create_population_folder import CreateNextPopulationFolderFiretask
from workflows.workflow_optimize_generation import get_optimize_generation_workflow
from utils.project_manager import ProjectManager
import logging

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


# -------------------- Dynamic Optimizer Loader --------------------

def load_optimizer(optimizer_type, config):
    """Dynamically load optimizer class from optimizers package."""
    from importlib import import_module

    module_name = f"optimizers.{optimizer_type}_optimizer"
    class_name = f"{optimizer_type.replace('_', ' ').title().replace(' ', '')}Optimizer"

    try:
        module = import_module(module_name)
        return getattr(module, class_name)(**config)
    except Exception as e:
        raise ImportError(f"Failed to load optimizer '{optimizer_type}': {e}")


# -------------------- FireWorks Utilities --------------------

def check_generation_status(launchpad: LaunchPad, generation_id: str):
    fw_ids = launchpad.get_fw_ids({"spec._generation_id": generation_id})
    return [launchpad.get_fw_by_id(fw_id).state for fw_id in fw_ids]


def run_rapidfire_until_complete(launchpad: LaunchPad, generation_id: str, max_nlaunches=1, wait_s=5):
    """Run FireWorks rapidfire loop until all jobs in the generation are complete."""
    logging.info(f"Processing generation {generation_id} with repeated rapidfire launches...")

    while True:
        states = check_generation_status(launchpad, generation_id)
        total = len(states)
        completed = states.count("COMPLETED")
        fizzled = states.count("FIZZLED")
        running = states.count("RUNNING")

        logging.info(f"Status: {completed}/{total} COMPLETED | {fizzled} FIZZLED | {running} RUNNING")

        if fizzled > 0:
            raise RuntimeError(f"{fizzled} FireWorks FIZZLED in generation {generation_id}.")

        if completed == total and total > 0:
            logging.info(f"Generation {generation_id} fully completed.")
            break

        try:
            subprocess.run(
                ["rlaunch", "rapidfire", "--nlaunches", str(max_nlaunches)],
                check=True
            )
        except subprocess.CalledProcessError as e:
            logging.warning(f"Rapidfire execution failed (retrying in {wait_s}s): {e}")
            time.sleep(wait_s)


def cleanup_launcher_folders():
    """Delete FireWorks temporary launcher_* folders to keep workspace clean."""
    current_dir = Path.cwd()
    for folder in current_dir.glob("launcher_*"):
        try:
            shutil.rmtree(folder)
            logging.info(f"Deleted launcher folder: {folder}")
        except Exception as e:
            logging.warning(f"Could not delete launcher folder {folder}: {e}")


# -------------------- Parameter File Management --------------------

def ensure_param_file(pm: ProjectManager):
    """Ensure parameter_sets.csv exists with proper header (all params)."""
    param_file = pm.parameter_sets_file
    expected_header = (
        ["generation_id", "candidate_id", "candidate_tag"]
        + pm.get_all_parameter_keys()
        + ["fitnessValue"]
    )

    if not param_file.exists():
        param_file.parent.mkdir(parents=True, exist_ok=True)
        with open(param_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(expected_header)
        logging.info(f"Created new parameter_sets.csv with header: {expected_header}")
    else:
        with open(param_file, newline="") as f:
            reader = csv.reader(f)
            try:
                current_header = next(reader)
                # Allow same columns in any order
                if set(current_header) != set(expected_header):
                    raise ValueError(
                        f"Header mismatch in {param_file}.\n"
                        f"Expected (unordered): {expected_header}\n"
                        f"Found: {current_header}"
                    )
            except StopIteration:
                # empty file → write header
                with open(param_file, "w", newline="") as fw:
                    writer = csv.writer(fw)
                    writer.writerow(expected_header)
                logging.info(f"Fixed empty parameter_sets.csv with header: {expected_header}")

    return param_file


def load_fitness_values(parameter_sets_file, generation_id):
    """Load fitness values for a given generation."""
    fitness = []
    with open(parameter_sets_file, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["generation_id"] == f"{generation_id:03d}":
                try:
                    fitness.append(float(row["fitnessValue"]))
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid fitness value in row: {row}")
    return fitness


# -------------------- Main Optimization Loop --------------------

def run_optimization_cycle(config_path_str):
    """Main driver loop for running the DE optimization workflow."""
    config_path = Path(config_path_str).resolve()

    # Load ProjectManager
    pm = ProjectManager(config_path)
    generator_type = pm.get_layout_generator_type()
    optimizer_type = pm.get_optimizer_type()
    project_acronym = pm.config["project_acronym"]["value"]

    logging.info(f"Starting optimization for project '{project_acronym}'")
    logging.info(f"Layout generator: {generator_type}")
    logging.info(f"Optimizer type: {optimizer_type}")

    # Ensure parameter_sets.csv exists
    param_file = ensure_param_file(pm)

    # Load optimizer
    optimizer = load_optimizer(
        optimizer_type,
        {
            "bounds": pm.get_bounds_dict(),
            **pm.get_optimization_parameters(),
        },
    )

    # Initialize FireWorks LaunchPad
    launchpad = LaunchPad.auto_load()
    generation_id = 0

    while not optimizer.is_done():
        generation_str = f"{generation_id:03d}"
        logging.info(f">>> Generation {generation_id} started")

        # Create population folder
        CreateNextPopulationFolderFiretask({"project_root": str(pm.root_dir)}).run_task({})

        # Suggest next generation parameter sets
        suggestions = optimizer.suggest()
        logging.debug(f"Parameter suggestions for generation {generation_str}: {suggestions}")

        parameter_population = []
        for idx, p in enumerate(suggestions, start=1):
            candidate_id = f"{idx:04d}"
            candidate_tag = f"{project_acronym}_{generation_str}_{candidate_id}"
            param_dict = pm.build_parameter_dict(p)

            parameter_population.append({
                "generation_id": generation_str,
                "candidate_id": candidate_id,
                "candidate_tag": candidate_tag,
                "parameters": param_dict,
            })

        # Create workflow
        wf = get_optimize_generation_workflow(
            pm.root_dir,
            parameter_population,
            pm,
            generator_type=generator_type  # explicitly pass generator name
        )
        launchpad.add_wf(wf)

        # Run until complete
        run_rapidfire_until_complete(launchpad, generation_str)

        # Cleanup FireWorks launcher folders
        cleanup_launcher_folders()

        # Gather fitness results
        fitness_values = load_fitness_values(param_file, generation_id)
        parameter_sets = pm.read_parameters_for_generation(generation_str)

        evaluated_population = []
        for params, fitness in zip(parameter_sets, fitness_values):
            evaluated_population.append({
                "generation_id": params["generation_id"],
                "candidate_id": params["candidate_id"],
                "candidate_tag": params["candidate_tag"],
                "parameters": {
                    k: v for k, v in params.items()
                    if k not in ("generation_id", "candidate_id", "candidate_tag")
                },
                "fitness": fitness,
            })

        optimizer.update(evaluated_population)
        logging.info(f"Generation {generation_id} completed and optimizer updated.")
        generation_id += 1

    logging.info(">>> Optimization finished successfully.")


# -------------------- CLI Entry Point --------------------

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python optimizer_runner.py path/to/project_config.json")
        sys.exit(1)
    run_optimization_cycle(sys.argv[1])