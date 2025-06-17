# File: tests/test_generate_layout_from_parameters.py

import tempfile
from pathlib import Path
from firetasks.generate_layout_from_parameters import GenerateLayoutFromParametersFiretask

def test_generate_layout_from_parameters_firetask():
    with tempfile.TemporaryDirectory() as tmpdir:
        layout_path = Path(tmpdir) / "layout_test.csv"

        task = GenerateLayoutFromParametersFiretask({
            "generator_type": "biomimetic_spiral",
            "parameters": {"a0": 10.0, "b": 2.0, "delta": 0.0},
            "output_layout_file": str(layout_path),
            "num_heliostats": 10,
            "bubble_radius": 4.5,
            "receiver_height": 35.0
        })

        # Run the FireTask
        result = task.run_task({})

        # Verify file creation
        assert layout_path.exists(), f"Expected layout file {layout_path} was not created."

        # Verify that at least one data line was written
        lines = layout_path.read_text().splitlines()
        assert len(lines) > 3, "Layout file seems incomplete or malformed."