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
        "tonatiuh_exe", "tonatiuh_script", "energy_exe", "directions_file"
    ]

    def run_task(self, fw_spec):
        project_root = Path(self["project_root"]).resolve()
        generation_id = self["generation_id"]
        parameters = self["parameters"]
        layout_file = Path(self["layout_file"]).resolve()

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

        script_file = population_dir / f"{file_prefix}.tnhpps"
        efficiency_file = population_dir / f"{file_prefix}_efficiency.csv"
        energy_output_file = population_dir / f"{file_prefix}_fitness.csv"

        tn_exe = Path(self["tonatiuh_exe"]).resolve()
        tn_template_script = Path(self["tonatiuh_script"]).resolve()
        energy_exe = Path(self["energy_exe"]).resolve()

        directions_file = Path(self["directions_file"]).resolve()

        simulate_script_text = tn_template_script.read_text()

        # Compute relative paths for portability
        relative_layout_path = layout_file.relative_to(population_dir).as_posix()
        relative_output_path = efficiency_file.relative_to(population_dir).as_posix()
        directions_file = (project_root / self["directions_file"]).resolve()
        relative_directions_file = os.path.relpath(directions_file, start=population_dir).replace("\\", "/")


        # Replace all placeholders in the template
        simulate_script_text = simulate_script_text.replace(
            "LAYOUT_PATH_PLACEHOLDER", f"{relative_layout_path}"
        ).replace(
            "OUTPUT_PATH_PLACEHOLDER", f"{relative_output_path}"
        ).replace(
            "INPUT_DIRECTIONS_PATH_PLACEHOLDER", f"{relative_directions_file}"
        )

        script_file.write_text(simulate_script_text)
        print(f"Tonatiuh++ script written to: {script_file}")

        # Run Tonatiuh++
        subprocess.run([str(tn_exe), "-i", str(script_file)], cwd=str(script_file.parent), check=True)

        # Run annual energy computation
        subprocess.run([str(energy_exe), str(efficiency_file), str(energy_output_file)],
                       cwd=str(project_root), check=True)

        # Read fitness value from last line of output file
        with open(energy_output_file, 'r') as f:
            last_line = f.readlines()[-1].strip()
            if last_line.startswith("average_optical_efficiency"):
                fitness_value = float(last_line.split(",")[1])
            else:
                raise ValueError(f"Unexpected format in fitness file: {last_line}")

        # Log parameter set and fitness value
        param_sets_file = project_root / "results" / "parameter_sets.csv"
        with open(param_sets_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([generation_id, a0, b, delta, fitness_value])

        return FWAction()