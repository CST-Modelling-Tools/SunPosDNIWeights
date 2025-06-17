# File: tests/test_compute_fitness.py

import tempfile
from pathlib import Path
from firetasks.compute_fitness import ComputeFitnessFiretask
from unittest.mock import patch, MagicMock

def test_compute_fitness_firetask():
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        scripts_dir = project_root / "scripts"
        results_dir = project_root / "results"
        scripts_dir.mkdir()
        results_dir.mkdir()

        # Dummy script with matching string
        dummy_script = scripts_dir / "simulate_layout.tnhpps"
        dummy_script.write_text("loadLayout('../layouts/layout_initial.csv')")

        task = ComputeFitnessFiretask({
            "project_root": str(project_root),
            "generation_id": "000",
            "a0": 10.0,
            "b": 2.0,
            "delta": 0.0
        })

        fw_spec = {
            "tonatiuh_exe": "/mock/path/to/tonatiuh",
            "tonatiuh_script": str(dummy_script.resolve()),
            "energy_exe": "/mock/path/to/energy",
            "skip_cleanup": True  # <-- Prevents script deletion
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock()
            result = task.run_task(fw_spec)

        assert result is not None

        layout_id = "000_10p00_2p00_0p00"
        expected_script = scripts_dir / f"simulate_{layout_id}.tnhpps"
        assert expected_script.exists(), f"Expected script {expected_script.resolve()} was not created."