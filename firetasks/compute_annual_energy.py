from fireworks import FiretaskBase, explicit_serialize, Firework, FWAction
from pathlib import Path
import subprocess
import os
import shutil

@explicit_serialize
class ComputeAnnualEnergyFiretask(FiretaskBase):
    required_params = ["input_file", "output_file", "executable"]

    def run_task(self, fw_spec):
        input_file = Path(self["input_file"]).resolve()
        output_file = Path(self["output_file"]).resolve()
        exe = Path(self["executable"]).resolve()

        if not exe.exists():
            raise FileNotFoundError(f"AnnualEnergy executable not found: {exe}")
        if not input_file.exists():
            raise FileNotFoundError(f"Tonatiuh++ result file not found: {input_file}")

        print(f"[AnnualEnergy] Running: {exe} {input_file} {output_file}")
        subprocess.run(
            [str(exe), str(input_file), str(output_file)],
            check=True
        )

        current_dir = Path.cwd()
        if current_dir.name.startswith("launcher_"):
            os.chdir(current_dir.parent)
            shutil.rmtree(current_dir)

        return FWAction()

def get_compute_annual_energy_firework(project_manager, executable_path):
    input_file = project_manager.results_dir / f"{project_manager.result_file_prefix}.csv"
    output_file = project_manager.results_dir / "annual_energy.csv"

    return Firework(
        ComputeAnnualEnergyFiretask(
            input_file=str(input_file),
            output_file=str(output_file),
            executable=str(executable_path)
        ),
        name="Compute Annual Energy"
    )