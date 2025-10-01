# File: workflows/workflow_optimize_generation.py

from fireworks import Workflow, Firework
from firetasks.compute_fitness import ComputeFitnessFiretask
from firetasks.generate_layout_from_parameters import GenerateLayoutFromParametersFiretask
from pathlib import Path


def get_optimize_generation_workflow(
    project_root: Path,
    parameter_population: list[dict],
    project_manager
) -> Workflow:
    """
    Build a FireWorks workflow to evaluate a population of layout parameters.

    Args:
        project_root (Path): Path to the root of the project.
        parameter_population (list): List of dicts with
            - generation_id
            - candidate_id
            - candidate_tag
            - parameters
        project_manager: Instance of ProjectManager to access configuration.

    Returns:
        Workflow: A FireWorks Workflow object containing layout generation and fitness evaluation steps.
    """
    assert parameter_population, "Empty parameter_population passed to workflow builder."

    fireworks = []

    generator_type = project_manager.get_layout_generator_type()
    fixed_params = project_manager.get_fixed_parameters()
    num_heliostats = fixed_params["num_heliostats"]
    bubble_radius = fixed_params["bubble_radius"]

    for param_set in parameter_population:
        gen_id = param_set["generation_id"]
        cand_id = param_set["candidate_id"]
        cand_tag = param_set["candidate_tag"]
        full_parameters = param_set["parameters"]

        # Directory for this generation
        population_dir = project_root / "results" / f"population_{gen_id}"
        population_dir.mkdir(parents=True, exist_ok=True)

        # File names follow new convention
        layout_file = population_dir / f"{cand_tag}_layout.csv"
        tnhpps_file = population_dir / f"{cand_tag}.tnhpps"
        efficiency_file = population_dir / f"{cand_tag}_efficiency.csv"
        fitness_file = population_dir / f"{cand_tag}_fitness.csv"

        # 🔹 Spec for layout generation
        generate_spec = {
            "generator_type": generator_type,
            "parameters": full_parameters,
            "layout_file": str(layout_file),
            "num_heliostats": num_heliostats,
            "bubble_radius": bubble_radius,
        }

        # 🔹 Spec for fitness computation
        compute_spec = {
            "project_root": str(project_root),
            "generation_id": gen_id,
            "candidate_id": cand_id,
            "candidate_tag": cand_tag,
            "parameters": full_parameters,
            "layout_file": str(layout_file),
            "tnhpps_file": str(tnhpps_file),
            "efficiency_file": str(efficiency_file),
            "fitness_file": str(fitness_file),
            "tonatiuh_exe": str(project_manager.get_tonatiuh_exe()),
            "tonatiuh_script": str(project_manager.get_script_path()),
            "energy_exe": str(project_manager.get_energy_exe()),
            "directions_file": str(project_manager.get_directions_file()),
            "generator_type": generator_type,
        }

        firework = Firework(
            [
                GenerateLayoutFromParametersFiretask(generate_spec),
                ComputeFitnessFiretask(compute_spec),
            ],
            name=f"Evaluate {cand_tag}",
            spec={"_generation_id": gen_id},
        )

        fireworks.append(firework)

    return Workflow(
        fireworks,
        name=f"Evaluate Generation {parameter_population[0]['generation_id']}"
    )