from fireworks import Workflow, Firework
from firetasks.compute_fitness import ComputeFitnessFiretask
from pathlib import Path

def get_optimize_generation_workflow(project_root: Path, parameter_population: list):
    """
    Creates a FireWorks workflow that evaluates all layout parameter sets in a generation.

    Args:
        project_root (Path): Path to the root of the optimization project.
        parameter_population (list): List of dictionaries with keys:
            - "generation_id": str (e.g. "000", "001", etc.)
            - "a0": float
            - "b": float
            - "delta": float

    Returns:
        Workflow: A FireWorks Workflow to evaluate the generation in parallel.
    """
    fireworks = []

    for params in parameter_population:
        firework = Firework(
            ComputeFitnessFiretask(
                project_root=str(project_root),
                generation_id=params["generation_id"],
                a0=params["a0"],
                b=params["b"],
                delta=params["delta"]
            ),
            name=f"Evaluate layout {params['generation_id']}_{params['a0']:.2f}_{params['b']:.2f}_{params['delta']:.2f}"
        )
        fireworks.append(firework)

    return Workflow(fireworks, name=f"Evaluate Generation {parameter_population[0]['generation_id']}")