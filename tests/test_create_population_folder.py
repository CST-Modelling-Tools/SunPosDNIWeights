import shutil
import tempfile
from pathlib import Path
from firetasks.create_population_folder import CreateNextPopulationFolderFiretask

def test_create_next_population_folder():
    # Create temporary directory for the mock project
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        layouts_dir = project_root / "layouts"
        layouts_dir.mkdir()

        # Simulate existing folders
        (layouts_dir / "population_000").mkdir()
        (layouts_dir / "population_001").mkdir()

        # Run the task
        task = CreateNextPopulationFolderFiretask({"project_root": str(project_root)})
        result = task.run_task({})

        # Expected new folder
        expected_folder = layouts_dir / "population_002"
        assert expected_folder.exists(), "New population folder was not created"

        # Check FWAction spec update
        assert "population_folder" in result.update_spec
        assert Path(result.update_spec["population_folder"]).resolve().samefile(expected_folder)