# File: optimizer_runner.py

import sys
import json
import csv
import time
import subprocess
import signal
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

def wait_for_generation_completion(launchpad: LaunchPad, generation_id: str, poll_interval=10):
    print(f"Waiting for generation {generation_id} to complete...")
    while True:
        all_fws = launchpad.get_fw_ids({"spec._generation_id": generation_id})
        states = [launchpad.get_fw_by_id(fw_id).state for fw_id in all_fws]

        completed = states.count("COMPLETED")
        fizzled = states.count("FIZZLED")
        total = len(states)

        print(f"    Status: {completed}/{total} COMPLETED | {fizzled} FIZZLED | {states.count('RUNNING')} RUNNING")

        if fizzled > 0:
            print(f"[ERROR] {fizzled} FireWorks FIZZLED in generation {generation_id}.")
            raise RuntimeError("Some FireWorks fizzled. Aborting optimization.")

        if completed == total:
            print(f"All FireWorks for generation {generation_id} completed.")
            break

        time.sleep(poll_interval)

def load_fitness_values(parameter_sets_file, generation_id):
    fitness = []
    with open(parameter_sets_file, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["generation_id"] == f"{generation_id:03d}":
                fitness.append(float(row["fitnessValue"]))
    return fitness

def start_rapidfire_worker():
    print("[INFO] Starting FireWorks rapidfire worker in background...")
    return subprocess.Popen(["rlaunch", "rapidfire"])

def run_optimization_cycle(config_path_str):
    config_path = Path(config_path_str).resolve()
    project_root = config_path.parent

    sys.path.insert(0, str(Path(__file__).parent))  # Add root folder to PYTHONPATH
    from projects.tarancon.project_manager import ProjectManager
    pm = ProjectManager(config_path)

    param_file = pm.parameter_sets_file
    if not param_file.exists():
        param_file.parent.mkdir(parents=True, exist_ok=True)
        with open(param_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["generation_id", "a0", "b", "delta", "fitnessValue"])

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

    rapidfire_process = start_rapidfire_worker()

    try:
        while not optimizer.is_done():
            generation_str = f"{generation_id:03d}"
            print(f">>> Generation {generation_id} started")

            CreateNextPopulationFolderFiretask({"project_root": str(pm.root_dir)}).run_task({})

            parameter_population = [
                {
                    "generation_id": generation_str,
                    "parameters": p
                }
                for p in optimizer.suggest(generation_id)
            ]

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

            wait_for_generation_completion(launchpad, generation_str)

            fitness_values = load_fitness_values(param_file, generation_id)
            parameter_sets = pm.read_parameters_for_generation(generation_str)
            evaluated_population = [
                {**params, "fitness": fitness}
                for params, fitness in zip(parameter_sets, fitness_values)
            ]
            optimizer.update(evaluated_population)
            generation_id += 1

        print(">>> Optimization finished.")

    finally:
        if rapidfire_process:
            print("[INFO] Terminating FireWorks rapidfire worker...")
            rapidfire_process.terminate()
            rapidfire_process.wait()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python optimizer_runner.py path/to/project_config.json")
        sys.exit(1)
    run_optimization_cycle(sys.argv[1])