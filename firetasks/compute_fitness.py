from pathlib import Path
from fireworks import FiretaskBase, explicit_serialize, Firework, FWAction
import subprocess
import shutil
import os

@explicit_serialize
class ComputeFitnessFiretask(FiretaskBase):
    required_params = ["layout_id", "project_root"]

    def run_task(self, fw_spec):
        layout_id = self["layout_id"]
        project_root = Path(self["project_root"]).resolve()

        # Construct file paths based on layout_id
        layout_file = project_root / "layouts" / f"layout_{layout_id}.csv"
        efficiency_file = project_root / "results" / f"efficiency_{layout_id}.csv"
        energy_output_file = project_root / "results" / f"fitness_{layout_id}.csv"

        # Retrieve Tonatiuh and energy executables from spec
        tn_exe = Path(fw_spec["tonatiuh_exe"]).resolve()
        tn_script = Path(fw_spec["tonatiuh_script"]).resolve()
        energy_exe = Path(fw_spec["energy_exe"]).resolve()

        # Replace layout path in simulate_layout.tnhpps
        simulate_script_path = tn_script
        simulate_script_text = simulate_script_path.read_text()
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

        # Run annual energy executable
        subprocess.run(
            [str(energy_exe), str(efficiency_file), str(energy_output_file)],
            cwd=str(project_root),
            check=True
        )

        # Clean up temporary files if needed
        try:
            os.remove(temp_script_path)
        except Exception:
            pass

        return FWAction()