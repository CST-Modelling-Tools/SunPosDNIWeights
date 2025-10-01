# File: firetasks/create_population_folder.py

from fireworks import FiretaskBase, explicit_serialize, FWAction
from pathlib import Path
import re

@explicit_serialize
class CreateNextPopulationFolderFiretask(FiretaskBase):
    """
    Firetask that creates the next population folder inside the results directory.

    Required params:
        - project_root (str): path to the project root.
    """

    required_params = ["project_root"]

    def run_task(self, fw_spec):
        project_root = Path(self["project_root"]).resolve()

        # Use "results" folder under project root (could later be replaced with project_manager if passed)
        results_dir = project_root / "results"
        results_dir.mkdir(exist_ok=True)

        # Find existing population indices with regex
        existing_indices = []
        for item in results_dir.iterdir():
            if item.is_dir():
                match = re.match(r"population_(\d{3})$", item.name)
                if match:
                    existing_indices.append(int(match.group(1)))

        next_index = 0 if not existing_indices else max(existing_indices) + 1
        population_folder = results_dir / f"population_{next_index:03d}"

        try:
            population_folder.mkdir(exist_ok=True)  # prevent race condition
        except OSError as e:
            raise RuntimeError(f"Could not create population folder {population_folder}: {e}")

        # Return both path and index for downstream tasks
        return FWAction(update_spec={
            "population_folder": str(population_folder),
            "population_index": next_index
        })