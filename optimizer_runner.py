# File: optimizer_runner.py

import sys
import json
import csv
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

    # LaunchPad connection
    launchpad = LaunchPad.auto_load()

    generation_id = 0
    while not optimizer.is_done():
        generation_str = f"{generation_id:03d}"
        print(f">>> Generation {generation_id} started")

        # Create layout folder
        CreateNextPopulationFolderFiretask({"project_root": str(pm.root_dir)}).run_task({})

        parameter_population = [
            {
                "generation_id": generation_str,
                "parameters": p  # p is a dict: {"a0": ..., "b": ..., "delta": ...}
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
        print("Workflow launched. Stopping for now to avoid infinite loop.")
        break

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python optimizer_runner.py path/to/project_config.json")
        sys.exit(1)
    run_optimization_cycle(sys.argv[1])