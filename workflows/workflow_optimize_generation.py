# File: workflows/workflow_optimize_generation.py

from fireworks import Workflow, Firework
from firetasks.compute_fitness import ComputeFitnessFiretask
from firetasks.generate_layout_from_parameters import GenerateLayoutFromParametersFiretask
from pathlib import Path


def get_optimize_generation_workflow(
    project_root: Path,
    parameter_population: list[dict],
    project_manager,
    generator_type: str | None = None
) -> Workflow:
    """
    Build a FireWorks workflow to evaluate a generation of layout parameters.

    Each candidate is evaluated through:
        GenerateLayoutFromParametersFiretask → ComputeFitnessFiretask

    Args:
        project_root (Path): Root of the project directory.
        parameter_population (list[dict]): Each entry contains
            - generation_id
            - candidate_id
            - candidate_tag
            - parameters (dict of numerical values)
        project_manager (ProjectManager): Provides paths and configuration.
        generator_type (str, optional): Layout generator type override.

    Returns:
        Workflow: A FireWorks Workflow object representing this generation.
    """
    assert parameter_population, "Empty parameter_population passed to workflow builder."

    # Layout generator name (explicit override or from config)
    generator_type = generator_type or project_manager.get_layout_generator_type()

    # Physical parameters (non-optimizable values)
    physical_params = project_manager.get_flat_physical_parameters()
    num_heliostats = physical_params.get("num_heliostats")
    bubble_radius = physical_params.get("bubble_radius")
    min_tower_clearance = physical_params.get("min_tower_clearance")
    receiver_height = physical_params.get("receiver_height", None)

    # Project acronym for consistent tagging
    project_acronym = project_manager.config["project_acronym"]["value"]

    fireworks = []

    for param_set in parameter_population:
        gen_id = param_set["generation_id"]
        cand_id = param_set["candidate_id"]
        cand_tag = param_set["candidate_tag"]
        full_parameters = param_set["parameters"]

        # Create generation directory if missing
        population_dir = project_root / "results" / f"population_{gen_id}"
        population_dir.mkdir(parents=True, exist_ok=True)

        # File naming consistent with new convention
        layout_file = population_dir / f"{cand_tag}_layout.csv"
        tnhpps_file = population_dir / f"{cand_tag}.tnhpps"
        efficiency_file = population_dir / f"{cand_tag}_efficiency.csv"
        fitness_file = population_dir / f"{cand_tag}_fitness.csv"

        # -------------------- Layout Generation Step --------------------
        generate_spec = {
            "generator_type": generator_type,
            "parameters": full_parameters,
            "layout_file": str(layout_file),
            "num_heliostats": num_heliostats,
            "bubble_radius": bubble_radius,
            "receiver_height": receiver_height,
            "min_tower_clearance": min_tower_clearance,
            "project_root": str(project_root),
            "candidate_tag": cand_tag,
        }

        # -------------------- Fitness Evaluation Step --------------------
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
            "project_acronym": project_acronym,
        }

        firework = Firework(
            [
                GenerateLayoutFromParametersFiretask(generate_spec),
                ComputeFitnessFiretask(compute_spec),
            ],
            name=f"Evaluate {cand_tag}",
            spec={"_generation_id": gen_id, "_generator_type": generator_type},
        )

        fireworks.append(firework)

    return Workflow(
        fireworks,
        name=f"Evaluate Generation {parameter_population[0]['generation_id']}",
    )