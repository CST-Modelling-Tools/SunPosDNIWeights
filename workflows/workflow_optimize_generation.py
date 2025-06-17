from fireworks import Workflow, Firework
from firetasks.compute_fitness import ComputeFitnessFiretask
from firetasks.generate_layout_from_parameters import GenerateLayoutFromParametersFiretask
from pathlib import Path

def get_optimize_generation_workflow(project_root: Path, parameter_population: list, config: dict):
    """
    Creates a FireWorks workflow that evaluates all layout parameter sets in a generation.

    Args:
        project_root (Path): Path to the root of the optimization project.
        parameter_population (list): List of dictionaries with keys:
            - "generation_id": str
            - "a0": float
            - "b": float
            - "delta": float
        config (dict): Project configuration values used by the layout generator.
            Must include:
                - "generator_type": str (e.g., "biomimetic_spiral")
                - "num_heliostats": int
                - "bubble_radius": float
                - "receiver_height": float

    Returns:
        Workflow: A FireWorks Workflow to evaluate the generation in parallel.
    """
    fireworks = []

    for params in parameter_population:
        layout_id = f"{params['generation_id']}_{params['a0']:.2f}_{params['b']:.2f}_{params['delta']:.2f}".replace('.', 'p')
        layout_file = project_root / "layouts" / f"layout_{layout_id}.csv"

        firework = Firework(
            [
                GenerateLayoutFromParametersFiretask(
                    {
                        "generator_type": config["generator_type"],
                        "parameters": [params["a0"], params["b"], params["delta"]],
                        "output_layout_file": str(layout_file),
                        "num_heliostats": config["num_heliostats"],
                        "bubble_radius": config["bubble_radius"],
                        "receiver_height": config["receiver_height"]
                    }
                ),
                ComputeFitnessFiretask(
                    {
                        "project_root": str(project_root),
                        "generation_id": params["generation_id"],
                        "a0": params["a0"],
                        "b": params["b"],
                        "delta": params["delta"]
                    }
                )
            ],
            name=f"Evaluate layout {layout_id}"
        )

        fireworks.append(firework)

    return Workflow(fireworks, name=f"Evaluate Generation {parameter_population[0]['generation_id']}")