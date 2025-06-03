from fireworks import Workflow
from firetasks.run_tonatiuh import get_run_tonatiuh_firework
from firetasks.compute_annual_energy import get_compute_annual_energy_firework
from project_manager import ProjectManager

def get_annual_energy_workflow(project_root):
    # Load project
    project_manager = ProjectManager(project_root)

    # Get file paths
    tn_script = project_manager.tonatiuh_script
    tn_exe = project_manager.tonatiuh_exe
    energy_exe = project_manager.energy_exe

    # Define I/O file paths
    efficiency_file = project_manager.results_dir / "directions_with_weights_and_efficiency_tarancon_spain.csv"
    annual_output_file = project_manager.results_dir / f"{project_manager.result_file_prefix}_annual_energy.csv"

    # Create FireWorks
    fw1 = get_run_tonatiuh_firework(project_manager)
    fw2 = get_compute_annual_energy_firework(
        efficiency_file=efficiency_file,
        output_file=annual_output_file,
        executable=energy_exe
    )

    # Return workflow
    return Workflow([fw1, fw2], {fw1: [fw2]}, name=f"{project_manager.project_name}_annual_energy")