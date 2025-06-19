# File: firetasks/compute_fitness.py

from pathlib import Path
from fireworks import FiretaskBase, explicit_serialize, FWAction
import subprocess
import shutil
import os

@explicit_serialize
class ComputeFitnessFiretask(FiretaskBase):
    required_params = ["project_root", "generation_id", "parameters", "layout_file", "script_file",
                       "tonatiuh_exe", "tonatiuh_script", "energy_exe"]

    def run_task(self, fw_spec):
        project_root = Path(self["project_root"]).resolve()
        generation_id = self["generation_id"]
        parameters = self["parameters"]
        layout_file = Path(self["layout_file"]).resolve()
        script_file = Path(self["script_file"]).resolve()

        a0 = parameters["a0"]
        b = parameters["b"]
        delta = parameters["delta"]

        layout_id = f"{generation_id}_{a0:.2f}_{b:.2f}_{delta:.2f}".replace('.', 'p')

        efficiency_file = project_root / "results" / f"efficiency_{layout_id}.csv"
        energy_output_file = project_root / "results" / f"fitness_{layout_id}.csv"

        tn_exe = Path(self["tonatiuh_exe"]).resolve()
        tn_template_script = Path(self["tonatiuh_script"]).resolve()
        energy_exe = Path(self["energy_exe"]).resolve()

        simulate_script_text = tn_template_script.read_text()

        # Replace layout path with correct relative path
        relative_layout_path = layout_file.relative_to(script_file.parent).as_posix()
        simulate_script_text = simulate_script_text.replace(
            "generateHeliostatFieldFromCSV(field, \"../layouts/layout_initial.csv\");",
            f"generateHeliostatFieldFromCSV(field, \"{relative_layout_path}\");"
        )

        # Replace output path placeholder
        simulate_script_text = simulate_script_text.replace(
            'const outputPath = "OUTPUT_PATH_PLACEHOLDER";',
            f'const outputPath = "{efficiency_file.as_posix()}";'
        )


        script_file.write_text(simulate_script_text)
        print(f"Writing to: {script_file}")
        # print("Modified script content:")
        # print(simulate_script_text)

        # Run Tonatiuh++
        subprocess.run(
            [str(tn_exe), "-i", str(script_file)],
            cwd=str(script_file.parent),
            check=True
        )

        # Run AnnualEnergy
        subprocess.run(
            [str(energy_exe), str(efficiency_file), str(energy_output_file)],
            cwd=str(project_root),
            check=True
        )

        if not fw_spec.get("skip_cleanup", False):
            try:
                os.remove(script_file)
            except Exception:
                pass

        return FWAction()