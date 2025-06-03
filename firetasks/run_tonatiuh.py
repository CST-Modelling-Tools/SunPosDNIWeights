from fireworks import FiretaskBase, explicit_serialize, Firework, FWAction
from pathlib import Path
import subprocess
import os
import shutil

@explicit_serialize
class RunTonatiuhSimulationFiretask(FiretaskBase):
    required_params = ["tn_script", "tn_executable"]

    def run_task(self, fw_spec):
        tn_script = Path(self["tn_script"]).resolve()
        tn_exe = Path(self["tn_executable"]).resolve()

        if not tn_exe.exists():
            raise FileNotFoundError(f"Tonatiuh++ executable not found: {tn_exe}")
        if not tn_script.exists():
            raise FileNotFoundError(f"Tonatiuh++ script file not found: {tn_script}")

        print(f"[Tonatiuh++] Running {tn_exe} with script {tn_script}")

        # Save current launcher directory before changing
        current_launcher_dir = Path.cwd()

        subprocess.run(
            [str(tn_exe), "-i", str(tn_script)],
            cwd=str(tn_script.parent),
            check=True
        )

        # Safe cleanup of launcher directory only if applicable
        if current_launcher_dir.name.startswith("launcher_") and current_launcher_dir.is_dir():
            try:
                os.chdir(current_launcher_dir.parent)
                shutil.rmtree(current_launcher_dir)
            except Exception as e:
                print(f"[Tonatiuh++] Warning: Failed to remove launcher directory {current_launcher_dir}: {e}")

        return FWAction()

def get_run_tonatiuh_firework(project_manager):
    return Firework(
        RunTonatiuhSimulationFiretask(
            tn_script=str(project_manager.tonatiuh_script),
            tn_executable=str(project_manager.tonatiuh_exe)
        ),
        name="Run Tonatiuh++ Simulation"
    )