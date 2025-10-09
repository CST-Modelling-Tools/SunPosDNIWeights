# File: firetasks/compute_fitness.py

from pathlib import Path
from fireworks import FiretaskBase, explicit_serialize, FWAction
import subprocess
import os
import csv
from utils.project_manager import ProjectManager


@explicit_serialize
class ComputeFitnessFiretask(FiretaskBase):
    required_params = [
        "project_root",
        "generation_id",
        "candidate_id",
        "candidate_tag",
        "parameters",
        "layout_file",
        "tnhpps_file",
        "efficiency_file",
        "fitness_file",
        "tonatiuh_exe",
        "tonatiuh_script",
        "energy_exe",
        "directions_file",
    ]

    optional_params = ["generator_type", "project_acronym"]

    def run_task(self, fw_spec):
        project_root = Path(self["project_root"]).resolve()
        generation_id = self["generation_id"]
        candidate_id = self["candidate_id"]
        candidate_tag = self["candidate_tag"]
        parameters = self["parameters"]

        layout_file = Path(self["layout_file"]).resolve()
        tnhpps_file = Path(self["tnhpps_file"]).resolve()
        efficiency_file = Path(self["efficiency_file"]).resolve()
        fitness_file = Path(self["fitness_file"]).resolve()

        if not layout_file.exists():
            print(f"[WARNING] Skipping fitness computation: layout file not found → {layout_file}")
            return FWAction()

        tn_exe = Path(self["tonatiuh_exe"]).resolve()
        tn_template_script = (project_root / self["tonatiuh_script"]).resolve()
        energy_exe = Path(self["energy_exe"]).resolve()

        # Relative paths (Tonatiuh++ expects relative to .tnhpps location)
        directions_file = (project_root / self["directions_file"]).resolve()
        rel_directions = os.path.relpath(directions_file, start=tnhpps_file.parent).replace("\\", "/")
        rel_layout = layout_file.relative_to(tnhpps_file.parent).as_posix()
        rel_efficiency = efficiency_file.relative_to(tnhpps_file.parent).as_posix()

        # 🔹 Generate Tonatiuh++ script
        if not tn_template_script.exists():
            raise FileNotFoundError(f"Tonatiuh++ template script not found: {tn_template_script}")

        script_text = tn_template_script.read_text()
        script_text = (
            script_text
            .replace("LAYOUT_PATH_PLACEHOLDER", rel_layout)
            .replace("OUTPUT_PATH_PLACEHOLDER", rel_efficiency)
            .replace("INPUT_DIRECTIONS_PATH_PLACEHOLDER", rel_directions)
        )
        tnhpps_file.write_text(script_text)
        print(f"[INFO] Tonatiuh++ input script created: {tnhpps_file}")

        # 🔹 Run Tonatiuh++
        try:
            subprocess.run(
                [str(tn_exe), "-i", str(tnhpps_file)],
                cwd=str(tnhpps_file.parent),
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Tonatiuh++ simulation failed for {candidate_tag}")
            print(e.stderr)
            return FWAction()

        # 🔹 Run Annual Energy computation
        try:
            subprocess.run(
                [str(energy_exe), str(efficiency_file), str(fitness_file)],
                cwd=str(project_root),
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] AnnualEnergy computation failed for {candidate_tag}")
            print(e.stderr)
            return FWAction()

        # 🔹 Validate fitness file
        if not fitness_file.exists() or fitness_file.stat().st_size == 0:
            raise FileNotFoundError(f"Fitness file missing or empty: {fitness_file}")

        # 🔹 Parse fitness metric
        fitness_value = None
        metric_name = None
        with open(fitness_file, "r") as f:
            for line in f:
                if line.strip().startswith("average_optical_efficiency"):
                    metric_name = "average_optical_efficiency"
                    try:
                        fitness_value = float(line.split(",")[1])
                    except (IndexError, ValueError):
                        raise ValueError(f"Invalid fitness line in {fitness_file}: {line.strip()}")

        if fitness_value is None:
            raise ValueError(f"No valid fitness metric found in {fitness_file}")

        print(f"[INFO] Candidate {candidate_tag} fitness ({metric_name}): {fitness_value:.6f}")

        # 🔹 Append results to parameter_sets.csv
        pm = ProjectManager(project_root / "project_config.json")
        param_sets_file = project_root / "results" / "parameter_sets.csv"
        file_exists = param_sets_file.exists()

        ordered_param_keys = pm.get_all_parameter_keys()

        with open(param_sets_file, "a", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                header = (
                    ["generation_id", "candidate_id", "candidate_tag"]
                    + ordered_param_keys
                    + ["fitnessValue"]
                )
                writer.writerow(header)

            # Force consistent ordering
            param_values = []
            for k in ordered_param_keys:
                if k not in parameters:
                    raise KeyError(f"[ERROR] Missing parameter '{k}' in candidate {candidate_tag}")
                val = parameters[k]
                param_values.append(f"{float(val):.6f}" if isinstance(val, (float, int)) else str(val))

            row = [generation_id, candidate_id, candidate_tag] + param_values + [f"{fitness_value:.6f}"]
            writer.writerow(row)

        print(f"[INFO] Candidate {candidate_tag} fitness logged successfully.")
        return FWAction()