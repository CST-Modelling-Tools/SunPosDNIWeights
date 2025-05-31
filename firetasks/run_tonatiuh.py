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
        subprocess.run(
            [str(tn_exe), "-i", str(tn_script)],
            cwd=str(tn_script.parent),
            check=True
        )

        # Cleanup
        current_dir = Path.cwd()
        if current_dir.name.startswith("launcher_"):
            os.chdir(current_dir.parent)
            shutil.rmtree(current_dir)

        return FWAction()

def get_run_tonatiuh_firework(project_manager, tn_executable):
    return Firework(
        RunTonatiuhSimulationFiretask(
            tn_script=str(project_manager.tonatiuh_script),
            tn_executable=str(tn_executable)
        ),
        name="Run Tonatiuh++ Simulation"
    )