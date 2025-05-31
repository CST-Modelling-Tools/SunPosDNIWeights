from pathlib import Path
from project_manager import ProjectManager
from evaluators.workflow_evaluator import evaluate_layout
from optimizers.de_blackbox_optimizer import DifferentialEvolutionOptimizer

# === Configuration ===

project_root = Path("projects/tarancon")
pm = ProjectManager(project_root)

parameter_bounds = {
    "num_rows": (5, 20),
    "num_cols": (5, 20),
    "spacing_x": (8.0, 20.0),
    "spacing_y": (8.0, 20.0),
    "receiver_height": (40.0, 120.0)
}

# Create the layouts directory if it doesn't exist
layouts_dir = pm.root_dir / "layouts"
layouts_dir.mkdir(exist_ok=True)

# === Objective function ===

def objective_function(params: dict, generation: int, individual: int) -> float:
    try:
        layout_file = layouts_dir / f"gen{generation}_ind{individual}.csv"
        result = evaluate_layout(params, layout_file, pm)
        return result
    except Exception as e:
        print(f"Evaluation failed for {params}: {e}")
        return 0.0  # Penalize failed runs

# === Optimization ===

optimizer = DifferentialEvolutionOptimizer(
    parameter_bounds=parameter_bounds,
    max_generations=10,
    population_size=8,
    mutation=0.8,
    crossover=0.7
)

print("Starting run_de_optimization.py...")

generation = 1
while not optimizer.is_done():
    print(f"\n=== Generation {generation} ===")
    suggestions = optimizer.suggest()

    for i, params in enumerate(suggestions, 1):
        result = objective_function(params, generation, i)
        optimizer.update(params, result)

    generation += 1

# === Output ===

best = optimizer.best_solution()
print("\n=== Optimization Finished ===")
print(f"Best parameters: {best['parameters']}")
print(f"Best result (annual energy): {best['result']:.2f} MWh")