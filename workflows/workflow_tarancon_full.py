from fireworks import Workflow, LaunchPad
from firetasks.generate_sampling import get_generate_sampling_firework
from firetasks.run_tonatiuh import get_run_tonatiuh_firework
from firetasks.compute_annual_energy import get_compute_annual_energy_firework
from project_manager import ProjectManager
from pathlib import Path

def main():
    # Path to the tarancon project folder
    project_root = Path("projects/tarancon")
    pm = ProjectManager(project_root)

    # Extract executable paths from config
    sampling_exe = (project_root / pm.config["executables"]["sampling_exe"]).resolve()
    tonatiuh_exe = Path(pm.config["executables"]["tonatiuh_exe"])  # Absolute path
    energy_exe = (project_root / pm.config["executables"]["energy_exe"]).resolve()

    # Configure the FireWorks LaunchPad (default localhost)
    lpad = LaunchPad(
        host="localhost",
        port=27017,
        name="fireworks",
        username=None,
        password=None
    )

    # Create the three FireWorks
    fw_sampling = get_generate_sampling_firework(pm, sampling_exe)
    fw_tonatiuh = get_run_tonatiuh_firework(pm, tonatiuh_exe)
    fw_energy = get_compute_annual_energy_firework(pm, energy_exe)

    # Create workflow with explicit dependencies
    wf = Workflow(
        [fw_sampling, fw_tonatiuh, fw_energy],
        links_dict={
            fw_sampling.fw_id: [fw_tonatiuh.fw_id],
            fw_tonatiuh.fw_id: [fw_energy.fw_id],
        },
        name=f"Tarancon_Full_Optimization_{pm.project_name}"
    )

    # Add workflow to LaunchPad
    lpad.add_wf(wf)

    print("Tarancon full workflow added to LaunchPad.")

if __name__ == "__main__":
    main()