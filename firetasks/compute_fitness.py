from pathlib import Path
from fireworks import FiretaskBase, explicit_serialize, Firework, FWAction
import subprocess
import shutil
import os

@explicit_serialize
class ComputeFitnessFiretask(FiretaskBase):
    required_params = ["project_root", "generation_id", "a0", "b", "delta"]

    def run_task(self, fw_spec):
        # Extract parameters
        project_root = Path(self["project_root"]).resolve()
        generation_id = self["generation_id"]
        a0 = self["a0"]
        b = self["b"]
        delta = self["delta"]

        # Construct layout_id based on generation_id and rounded parameters
        layout_id = f"{generation_id}_{a0:.2f}_{b:.2f}_{delta:.2f}".replace('.', 'p')

        # Define file paths
        layout_file = project_root / "layouts" / f"layout_{layout_id}.csv"
        efficiency_file = project_root / "results" / f"efficiency_{layout_id}.csv"
        energy_output_file = project_root / "results" / f"fitness_{layout_id}.csv"

        # Get paths from fw_spec
        tn_exe = Path(fw_spec["tonatiuh_exe"]).resolve()
        tn_script = Path(fw_spec["tonatiuh_script"]).resolve()
        energy_exe = Path(fw_spec["energy_exe"]).resolve()

        # Generate modified Tonatiuh++ script
        simulate_script_text = tn_script.read_text()
        simulate_script_text = simulate_script_text.replace(
            "../layouts/layout_initial.csv", f"../layouts/layout_{layout_id}.csv"
        )
        temp_script_path = project_root / "scripts" / f"simulate_{layout_id}.tnhpps"
        temp_script_path.write_text(simulate_script_text)

        # Run Tonatiuh++
        subprocess.run(
            [str(tn_exe), "-i", str(temp_script_path)],
            cwd=str(temp_script_path.parent),
            check=True
        )

        # Run annual energy tool
        subprocess.run(
            [str(energy_exe), str(efficiency_file), str(energy_output_file)],
            cwd=str(project_root),
            check=True
        )

        # Clean up temp script
        try:
            os.remove(temp_script_path)
        except Exception:
            pass

        return FWAction()