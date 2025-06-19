# File: workflows/workflow_optimize_generation.py

from fireworks import Workflow, Firework
from firetasks.compute_fitness import ComputeFitnessFiretask
from firetasks.generate_layout_from_parameters import GenerateLayoutFromParametersFiretask
from pathlib import Path


def get_optimize_generation_workflow(project_root: Path, parameter_population: list, config: dict):
    """
    Creates a FireWorks workflow that evaluates all layout parameter sets in a generation.

    Args:
        project_root (Path): Path to the root of the optimization project.
        parameter_population (list): List of dictionaries with:
            - "generation_id": str
            - "parameters": dict {"a0", "b", "delta"}
        config (dict): Must include:
            - "layout_generator_type"
            - "num_heliostats"
            - "bubble_radius"
            - "receiver_height"
            - "tonatiuh_exe"
            - "tonatiuh_script"
            - "energy_exe"

    Returns:
        Workflow: A FireWorks workflow evaluating the generation in parallel.
    """
    fireworks = []

    for params in parameter_population:
        gen_id = params["generation_id"]
        p = params["parameters"]

        layout_id = f"{gen_id}_{p['a0']:.2f}_{p['b']:.2f}_{p['delta']:.2f}".replace('.', 'p')

        population_dir = project_root / "layouts" / f"population_{gen_id}"
        population_dir.mkdir(parents=True, exist_ok=True)

        layout_file = population_dir / f"layout_{layout_id}.csv"
        script_file = population_dir / f"simulate_{layout_id}.tnhpps"

        firework = Firework(
            [
                GenerateLayoutFromParametersFiretask(
                    {
                        "generator_type": config["layout_generator_type"],
                        "parameters": p,
                        "output_layout_file": str(layout_file),
                        "num_heliostats": config["num_heliostats"],
                        "bubble_radius": config["bubble_radius"],
                        "receiver_height": config["receiver_height"]
                    }
                ),
                ComputeFitnessFiretask(
                    {
                        "project_root": str(project_root),
                        "generation_id": gen_id,
                        "parameters": p,
                        "layout_file": str(layout_file),
                        "script_file": str(script_file),
                        "tonatiuh_exe": config["tonatiuh_exe"],
                        "tonatiuh_script": config["tonatiuh_script"],
                        "energy_exe": config["energy_exe"]
                    }
                )
            ],
            name=f"Evaluate layout {layout_id}"
        )

        fireworks.append(firework)

    return Workflow(fireworks, name=f"Evaluate Generation {parameter_population[0]['generation_id']}")