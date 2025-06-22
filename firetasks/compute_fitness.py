# File: firetasks/compute_fitness.py

from pathlib import Path
from fireworks import FiretaskBase, explicit_serialize, FWAction
import subprocess
import os
import csv

@explicit_serialize
class ComputeFitnessFiretask(FiretaskBase):
    required_params = [
        "project_root", "generation_id", "parameters", "layout_file",
        "tonatiuh_exe", "tonatiuh_script", "energy_exe"
    ]

    def run_task(self, fw_spec):
        project_root = Path(self["project_root"]).resolve()
        generation_id = self["generation_id"]
        parameters = self["parameters"]
        layout_file = Path(self["layout_file"]).resolve()

        # Skip computation if layout file does not exist
        if not layout_file.exists():
            print(f"[WARNING] Skipping fitness computation because layout file does not exist: {layout_file}")
            return FWAction()

        a0 = parameters["a0"]
        b = parameters["b"]
        delta = parameters["delta"]

        layout_id = f"{generation_id}_{a0:.2f}_{b:.2f}_{delta:.2f}".replace('.', 'p')
        file_prefix = f"ps_{layout_id}"

        population_dir = project_root / "results" / f"population_{generation_id}"
        population_dir.mkdir(parents=True, exist_ok=True)

        # Define the final .tnhpps script file (unique per parameter set)
        script_file = population_dir / f"{file_prefix}.tnhpps"
        efficiency_file = population_dir / f"{file_prefix}_efficiency.csv"
        energy_output_file = population_dir / f"{file_prefix}_fitness.csv"

        # Get executables and template script
        tn_exe = Path(self["tonatiuh_exe"]).resolve()
        tn_template_script = Path(self["tonatiuh_script"]).resolve()
        energy_exe = Path(self["energy_exe"]).resolve()

        # Read template and replace placeholders
        simulate_script_text = tn_template_script.read_text()

        relative_layout_path = layout_file.relative_to(population_dir).as_posix()

        simulate_script_text = simulate_script_text.replace(
            'generateHeliostatFieldFromCSV(field, "LAYOUT_PATH_PLACEHOLDER");',
            f'generateHeliostatFieldFromCSV(field, "{relative_layout_path}");'
        )

        simulate_script_text = simulate_script_text.replace(
            'const outputPath = "OUTPUT_PATH_PLACEHOLDER";',
            f'const outputPath = "{efficiency_file.as_posix()}";'
        )

        # Write the final .tnhpps script
        script_file.write_text(simulate_script_text)
        print(f"Writing to: {script_file}")

        # Run Tonatiuh++
        subprocess.run([str(tn_exe), "-i", str(script_file)], cwd=str(script_file.parent), check=True)

        # Run AnnualEnergy
        subprocess.run([str(energy_exe), str(efficiency_file), str(energy_output_file)],
                       cwd=str(project_root), check=True)

        # Read and extract fitness value
        with open(energy_output_file, 'r') as f:
            last_line = f.readlines()[-1].strip()
            if last_line.startswith("average_optical_efficiency"):
                fitness_value = float(last_line.split(",")[1])
            else:
                raise ValueError(f"Unexpected format in fitness file: {last_line}")

        # Append to parameter_sets.csv
        param_sets_file = project_root / "results" / "parameter_sets.csv"
        with open(param_sets_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([generation_id, a0, b, delta, fitness_value])

        # Delete all launcher folders created by FireWorks (after each layout eval)
        for folder in project_root.glob("launcher_*"):
            try:
                shutil.rmtree(folder)
                print(f"[INFO] Deleted launcher folder: {folder}")
            except Exception as e:
                print(f"[WARNING] Could not delete launcher folder {folder}: {e}")            

        return FWAction()