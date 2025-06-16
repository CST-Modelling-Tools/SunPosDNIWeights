from pathlib import Path
from fireworks import FiretaskBase, explicit_serialize, FWAction
import subprocess
import shutil
import os
import csv
from layout_generators.biomimetic_spiral_layout_generator import generate_biomimetic_spiral_layout

@explicit_serialize
class ComputeFitnessFiretask(FiretaskBase):
    required_params = ["project_root", "generation_id", "a0", "b", "delta"]

    def run_task(self, fw_spec):
        project_root = Path(self["project_root"]).resolve()
        generation_id = self["generation_id"]
        a0 = float(self["a0"])
        b = float(self["b"])
        delta = float(self["delta"])

        manager_path = project_root / "project_manager.py"
        import importlib.util
        spec = importlib.util.spec_from_file_location("project_manager", str(manager_path))
        project_manager_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(project_manager_module)
        manager = project_manager_module.ProjectManager(project_root)

        # Define layout ID
        layout_id = f"{generation_id}_{a0:.3f}_{b:.3f}_{delta:.3f}".replace(".", "p")
        layout_file = manager.layouts_dir / f"layout_{layout_id}.csv"

        # Generate layout
        generate_biomimetic_spiral_layout(
            output_file=layout_file,
            num_heliostats=manager.num_heliostats,
            a0=a0,
            b=b,
            delta=delta,
            receiver_height=manager.receiver_height,
            bubble_radius=manager.bubble_radius
        )

        # Replace layout path in simulate_layout script
        simulate_template = manager.tonatiuh_script.read_text()
        simulate_custom = simulate_template.replace(
            "../layouts/layout_initial.csv",
            f"../layouts/layout_{layout_id}.csv"
        )
        temp_script = manager.root_dir / "scripts" / f"simulate_{layout_id}.tnhpps"
        temp_script.write_text(simulate_custom)

        efficiency_file = manager.results_dir / f"efficiency_{layout_id}.csv"
        fitness_output_file = manager.results_dir / f"fitness_{layout_id}.csv"

        subprocess.run(
            [str(manager.tonatiuh_exe), "-i", str(temp_script)],
            cwd=str(temp_script.parent),
            check=True
        )

        subprocess.run(
            [str(manager.energy_exe), str(efficiency_file), str(fitness_output_file)],
            cwd=str(manager.root_dir),
            check=True
        )

        # Read fitness value
        with open(fitness_output_file) as f:
            fitness_line = f.readline().strip()
            fitness_value = float(fitness_line.split(",")[-1])

        # Append parameters and fitness to parameter_sets.csv
        with open(manager.parameter_sets_file, mode="a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([generation_id, a0, b, delta, fitness_value])

        # Clean up
        try:
            os.remove(temp_script)
        except Exception:
            pass

        return FWAction()