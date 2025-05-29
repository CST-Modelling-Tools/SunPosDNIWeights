from fireworks import FiretaskBase, explicit_serialize, Firework
from pathlib import Path
import subprocess

@explicit_serialize
class RunTonatiuhSimulationFiretask(FiretaskBase):
    """
    Firetask that runs a Tonatiuh++ simulation using a .tnhpps script.

    Required parameters:
        - tn_script: Path to the .tnhpps simulation script
        - tn_executable: Path to the Tonatiuh++ executable
    """

    required_params = ["tn_script", "tn_executable"]

    def run_task(self, fw_spec):
        tn_script = Path(self["tn_script"]).resolve()
        tn_exe = Path(self["tn_executable"]).resolve()

        if not tn_exe.exists():
            raise FileNotFoundError(f"Tonatiuh++ executable not found at: {tn_exe}")
        if not tn_script.exists():
            raise FileNotFoundError(f"Tonatiuh++ script file not found at: {tn_script}")

        print(f"Running Tonatiuh++ simulation...")
        print(f"Executable: {tn_exe}")
        print(f"Script:     {tn_script}")

        script_dir = tn_script.parent

        result = subprocess.run(
            [str(tn_exe), "-i", str(tn_script)],
            cwd=str(script_dir),
            check=True
        )

        print("Tonatiuh++ simulation completed.")


def get_run_tonatiuh_firework(project_manager, tn_executable):
    """
    Helper function to create a Firework that runs the Tonatiuh++ simulation.

    Args:
        project_manager: ProjectManager instance
        tn_executable: Full path to Tonatiuh++ binary

    Returns:
        A Firework object ready to insert into a FireWorks workflow
    """
    return Firework(
        RunTonatiuhSimulationFiretask(
            tn_script=str(project_manager.tonatiuh_script),
            tn_executable=str(tn_executable)
        ),
        name="Run Tonatiuh++ Simulation"
    )