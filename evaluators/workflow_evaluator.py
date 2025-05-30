from typing import Dict
from pathlib import Path
import subprocess
import json
import uuid
import shutil
import time

class WorkflowEvaluator:
    def __init__(self, project_template_dir: Path, base_run_dir: Path, layout_generator, firework_script_path: Path):
        """
        Initialize the evaluator with necessary configuration.

        Args:
            project_template_dir (Path): Path to the static project template directory.
            base_run_dir (Path): Directory under which unique run folders will be created.
            layout_generator (Callable): Function that writes a layout CSV given parameters and a path.
            firework_script_path (Path): Path to the Python script that adds the workflow to LaunchPad.
        """
        self.project_template_dir = project_template_dir
        self.base_run_dir = base_run_dir
        self.layout_generator = layout_generator
        self.firework_script_path = firework_script_path

    def evaluate(self, parameters: Dict[str, float]) -> float:
        """
        Evaluate the heliostat layout defined by the given parameters using the full workflow.

        Args:
            parameters (dict): Dictionary of layout-generating parameters.

        Returns:
            float: Annual energy (or other objective) computed by the workflow.
        """
        # Step 1: Create unique run directory
        run_id = uuid.uuid4().hex[:8]
        run_dir = self.base_run_dir / f"run_{run_id}"
        shutil.copytree(self.project_template_dir, run_dir)

        # Step 2: Generate layout
        layout_path = run_dir / "projects" / "tarancon" / "layouts" / "generated_layout.csv"
        self.layout_generator(parameters, layout_path)

        # Step 3: Modify config.json to use new layout
        config_path = run_dir / "projects" / "tarancon" / "config.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        config["initial_layout"] = "generated_layout.csv"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)

        # Step 4: Launch workflow
        subprocess.run(["python", str(self.firework_script_path)], cwd=run_dir, check=True)

        # Step 5: Wait for completion (basic polling)
        result_path = run_dir / "projects" / "tarancon" / "results" / "annual_energy.csv"
        while not result_path.exists():
            time.sleep(2)

        # Step 6: Read result
        with open(result_path, 'r') as f:
            energy_value = float(f.read().strip().split(",")[1])  # assuming "energy,value" format

        return energy_value