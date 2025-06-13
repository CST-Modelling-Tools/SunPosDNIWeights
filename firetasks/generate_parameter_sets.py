from fireworks import FiretaskBase, explicit_serialize, FWAction
from pathlib import Path
import random
import json
import csv

@explicit_serialize
class GenerateParameterSetsFiretask(FiretaskBase):
    required_params = ["project_root"]

    def run_task(self, fw_spec):
        project_root = Path(self["project_root"]).resolve()
        config_path = project_root / "project_config.json"
        data_dir = project_root / "data"
        data_dir.mkdir(exist_ok=True)

        param_file = data_dir / "parameter_sets.csv"

        # Get population folder and generation ID
        population_folder = Path(fw_spec["population_folder"])
        generation_id = population_folder.name  # e.g., population_000

        # Read config
        with open(config_path, 'r') as f:
            config = json.load(f)

        pop_size = config["optimization_config"]["population_size"]
        bounds = config["optimization_config"]["parameter_bounds"]

        # Sample parameters
        samples = []
        for _ in range(pop_size):
            a0 = random.uniform(*bounds["a0"])
            b = random.uniform(*bounds["b"])
            delta = random.uniform(*bounds["delta"])
            samples.append((generation_id, a0, b, delta, None))  # fitnessValue is None initially

        # Append to CSV
        with open(param_file, 'a', newline='') as f:
            writer = csv.writer(f)
            for row in samples:
                writer.writerow(row)

        return FWAction(update_spec={"generation_id": generation_id, "parameter_samples": samples})