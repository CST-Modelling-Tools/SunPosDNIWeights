from project_manager import ProjectManager
from fireworks import LaunchPad

if __name__ == "__main__":
    # Path to the root folder of the project (i.e., the folder containing project_config.json)
    project_root = "projects/tarancon"

    # Initialize project manager (this modifies sys.path if needed)
    manager = ProjectManager(project_root)

    # Import workflow AFTER manager modifies sys.path
    from workflow_annual_energy import get_annual_energy_workflow

    # Build the workflow
    wf = get_annual_energy_workflow(manager.root_dir)

    # Connect to LaunchPad and add the workflow
    launchpad = LaunchPad.auto_load()
    launchpad.add_wf(wf)

    print(f"Workflow for '{manager.project_name}' submitted successfully.")