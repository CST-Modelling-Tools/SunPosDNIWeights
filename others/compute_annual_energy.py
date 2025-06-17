from fireworks import FiretaskBase, explicit_serialize, Firework, FWAction
from pathlib import Path
import subprocess
import shutil
import os

@explicit_serialize
class ComputeAnnualEnergyFiretask(FiretaskBase):
    required_params = ["efficiency_file", "output_file", "executable"]

    def run_task(self, fw_spec):
        efficiency_file = Path(self["efficiency_file"]).resolve()
        output_file = Path(self["output_file"]).resolve()
        exe = Path(self["executable"]).resolve()

        if not exe.exists():
            raise FileNotFoundError(f"AnnualEnergy executable not found at: {exe}")
        if not efficiency_file.exists():
            raise FileNotFoundError(f"Efficiency file not found at: {efficiency_file}")

        print(f"[AnnualEnergy] Running: {exe} {efficiency_file} {output_file}")
        subprocess.run(
            [str(exe), str(efficiency_file), str(output_file)],
            check=True
        )

        # Cleanup launcher dir if inside one
        current_dir = Path.cwd()
        if current_dir.name.startswith("launcher_"):
            os.chdir(current_dir.parent)
            shutil.rmtree(current_dir)

        return FWAction()

def get_compute_annual_energy_firework(efficiency_file, output_file, executable):
    return Firework(
        ComputeAnnualEnergyFiretask(
            efficiency_file=efficiency_file,
            output_file=output_file,
            executable=executable
        ),
        name="Compute Annual Energy"
    )