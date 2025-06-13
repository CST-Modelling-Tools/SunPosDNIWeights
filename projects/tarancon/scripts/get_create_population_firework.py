from fireworks import Firework
from firetasks.create_population_folder import CreateNextPopulationFolderFiretask
from firetasks.generate_parameter_sets import GenerateParameterSetsFiretask

def get_create_population_firework(project_root: str):
    """
    Creates a Firework that generates a new population folder and parameter sets.

    Parameters:
        project_root: Path to the root of the project (str)

    Returns:
        Firework: The composed Firework
    """
    return Firework(
        tasks=[
            CreateNextPopulationFolderFiretask(project_root=project_root),
            GenerateParameterSetsFiretask(project_root=project_root)
        ],
        name="Create Population"
    )