import importlib.util
import time
from pathlib import Path
from fireworks import LaunchPad
from workflows.workflow_optimize_generation import get_optimize_generation_workflow

def load_project_manager(project_root: Path):
    project_root = Path(project_root).resolve()
    manager_path = project_root / "project_manager.py"
    spec = importlib.util.spec_from_file_location("project_manager", str(manager_path))
    project_manager_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(project_manager_module)
    return project_manager_module.ProjectManager()

def get_optimizer(manager):
    optimizer_type = manager.optimizer_type.lower()
    if optimizer_type == "differential_evolution":
        from optimizer.differential_evolution import DifferentialEvolutionOptimizer
        return DifferentialEvolutionOptimizer(
            bounds=manager.parameter_bounds,
            population_size=manager.population_size,
            mutation_factor=manager.mutation_factor,
            crossover_rate=manager.crossover_rate,
            max_generations=manager.max_generations
        )
    else:
        raise ValueError(f"Unsupported optimizer type: {optimizer_type}")

def run_optimizer(project_root: Path):
    manager = load_project_manager(project_root)
    optimizer = get_optimizer(manager)

    launchpad = LaunchPad.auto_load()

    while not optimizer.is_done():
        generation = optimizer.generation
        print(f"🔁 Generation {generation}")

        population = optimizer.suggest()
        wf = get_optimize_generation_workflow(manager.root_dir, population)
        launchpad.add_wf(wf)

        print(f"🚀 Launched workflow for generation {generation}")
        print("⏳ Waiting for completion...")

        while launchpad.get_fw_ids(query={"state": {"$nin": ["COMPLETED", "FIZZLED"]}}):
            time.sleep(10)

        print("✅ Completed generation. Updating...")
        optimizer.update()

    print("🎯 Optimization finished.")

if __name__ == "__main__":
    run_optimizer(Path("projects/tarancon"))