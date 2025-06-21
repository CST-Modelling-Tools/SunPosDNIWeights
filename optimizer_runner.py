# File: optimizer_runner.py

import sys
import json
import csv
import time
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
from importlib import import_module
from fireworks import LaunchPad
from firetasks.create_population_folder import CreateNextPopulationFolderFiretask
from workflows.workflow_optimize_generation import get_optimize_generation_workflow


def load_module_from_path(name, path):
    spec = spec_from_file_location(name, path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_optimizer(class_path, config):
    module_path, class_name = class_path.rsplit(".", 1)
    module = import_module(module_path)
    return getattr(module, class_name)(**config)


def wait_for_generation_completion(launchpad, generation_id, timeout_sec=600, check_interval=10):
    print(f"Waiting for generation {generation_id} to complete...")
    waited = 0
    while waited < timeout_sec:
        fw_states = launchpad.get_fw_ids(query={"name": {"$regex": f".*{generation_id}.*"}})
        states = [launchpad.get_fw_by_id(fw_id).state for fw_id in fw_states]
        if all(state in ("FIZZLED", "COMPLETED") for state in states):
            print(f"All FireWorks for generation {generation_id} completed.")
            return
        time.sleep(check_interval)
        waited += check_interval
    raise TimeoutError(f"Timeout while waiting for generation {generation_id} to complete.")


def load_fitness_values(parameter_sets_file, generation_id):
    fitness = []
    with open(parameter_sets_file, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["generation_id"] == f"{generation_id:03d}":
                fitness.append(float(row["fitnessValue"]))
    return fitness


def run_optimization_cycle(config_path_str):
    config_path = Path(config_path_str).resolve()
    project_root = config_path.parent

    # Dynamically import ProjectManager from project folder
    pm_module = load_module_from_path("project_manager", str(project_root / "project_manager.py"))
    ProjectManager = getattr(pm_module, "ProjectManager")
    pm = ProjectManager(config_path)

    # Prepare parameter_sets.csv
    param_file = pm.parameter_sets_file
    if not param_file.exists():
        param_file.parent.mkdir(parents=True, exist_ok=True)
        with open(param_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["generation_id", "a0", "b", "delta", "fitnessValue"])

    # Load optimizer
    optimizer_type = pm.optimizer_type
    class_path = f"optimizers.{optimizer_type}_optimizer.{optimizer_type.replace('_', ' ').title().replace(' ', '')}Optimizer"
    optimizer = load_optimizer(class_path, {
        "bounds": pm.parameter_bounds,
        "population_size": pm.population_size,
        "mutation_factor": pm.mutation_factor,
        "crossover_rate": pm.crossover_rate,
        "max_generations": pm.max_generations
    })

    launchpad = LaunchPad.auto_load()
    generation_id = 0

    while not optimizer.is_done():
        generation_str = f"{generation_id:03d}"
        print(f">>> Generation {generation_id} started")

        # Create layout folder
        CreateNextPopulationFolderFiretask({"project_root": str(pm.root_dir)}).run_task({})

        # Suggest parameter sets
        parameter_population = [
            {
                "generation_id": generation_str,
                "parameters": p
            }
            for p in optimizer.suggest(generation_id)
        ]

        # Launch FireWorks workflow
        wf = get_optimize_generation_workflow(
            project_root=pm.root_dir,
            parameter_population=parameter_population,
            config={
                "layout_generator_type": pm.layout_generator_type,
                "num_heliostats": pm.num_heliostats,
                "bubble_radius": pm.bubble_radius,
                "receiver_height": pm.receiver_height,
                "tonatiuh_exe": str(pm.tonatiuh_exe),
                "tonatiuh_script": str(pm.tonatiuh_script),
                "energy_exe": str(pm.energy_exe)
            }
        )

        launchpad.add_wf(wf)

        # Wait for all FireWorks to complete
        wait_for_generation_completion(launchpad, generation_str)

        # Collect fitness values from CSV
        fitness_values = load_fitness_values(param_file, generation_id)

        # Update optimizer
        parameter_sets = pm.read_parameters_for_generation(generation_str)
        evaluated_population = [
            {**params, "fitness": fitness}
            for params, fitness in zip(parameter_sets, fitness_values)
        ]
        optimizer.update(evaluated_population)

        generation_id += 1

    print(">>> Optimization finished.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python optimizer_runner.py path/to/project_config.json")
        sys.exit(1)
    run_optimization_cycle(sys.argv[1])