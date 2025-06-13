from fireworks import FiretaskBase, explicit_serialize, FWAction
from pathlib import Path

@explicit_serialize
class CreateNextPopulationFolderFiretask(FiretaskBase):
    required_params = ["project_root"]

    def run_task(self, fw_spec):
        project_root = Path(self["project_root"]).resolve()
        layouts_dir = project_root / "layouts"
        layouts_dir.mkdir(exist_ok=True)

        # Find next population index
        existing_indices = []
        for item in layouts_dir.iterdir():
            if item.is_dir() and item.name.startswith("population_"):
                try:
                    idx = int(item.name.replace("population_", ""))
                    existing_indices.append(idx)
                except ValueError:
                    continue

        next_index = 0 if not existing_indices else max(existing_indices) + 1
        population_folder = layouts_dir / f"population_{next_index:03d}"
        population_folder.mkdir()

        # Return path in fw_spec for downstream tasks
        return FWAction(update_spec={"population_folder": str(population_folder)})