from pathlib import Path
from fireworks import Workflow
from firetasks.generate_sampling import get_generate_sampling_firework
from project_manager import ProjectManager

def get_generate_sampling_workflow(config_path):
    # Ensure config_path is a Path object
    config_path = Path(config_path).resolve()

    # Get project root as the parent directory of the JSON file
    project_root = config_path.parent

    # Initialize project manager with project root
    project_manager = ProjectManager(project_root)

    # Get path to sampling executable from project manager
    sampling_exe = project_manager.sampling_exe

    # Create firework
    fw = get_generate_sampling_firework(project_manager, sampling_exe)

    # Create and return workflow
    return Workflow([fw], name=f"{project_manager.project_name}_generate_sampling")