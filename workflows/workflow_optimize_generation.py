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
        generation_id = params["generation_id"]
        a0 = params["a0"]
        b = params["b"]
        delta = params["delta"]

        firework = Firework(
            ComputeFitnessFiretask(
                project_root=str(project_root),
                generation_id=generation_id,
                a0=a0,
                b=b,
                delta=delta
            ),
            name=f"Evaluate layout {generation_id}_{a0:.2f}_{b:.2f}_{delta:.2f}"
        )
        fireworks.append(firework)

    return Workflow(fireworks, name="Evaluate Generation")