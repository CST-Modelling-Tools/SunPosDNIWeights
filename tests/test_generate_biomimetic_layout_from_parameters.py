# File: tests/test_generate_biomimetic_layout_from_parameters.py

import tempfile
from pathlib import Path
import csv
from firetasks.generate_biomimetic_layout_from_parameters import GenerateBiomimeticLayoutFiretask

def test_generate_biomimetic_layout_firetask_creates_file():
    # Prepare temporary directory for layout output
    with tempfile.TemporaryDirectory() as tmpdirname:
        output_path = Path(tmpdirname) / "layout_test.csv"

        # Define task parameters
        task = GenerateBiomimeticLayoutFiretask(
            {
                "parameters": [10.0, 2.0, 0.0],       # a0, b, delta
                "output_layout_file": str(output_path),
                "num_heliostats": 10,
                "bubble_radius": 4.5,
                "receiver_height": 35.0
            }
        )

        # Run the FireTask
        fw_action = task.run_task({})  # fw_spec is unused

        # Check if file was created
        assert output_path.exists(), "Layout CSV file was not created"

        # Optionally check contents (first lines should be comments, then heliostat rows)
        with open(output_path, newline="") as csvfile:
            reader = csv.reader(csvfile)
            rows = list(reader)
            assert len(rows) >= 3, "Layout file should contain header and heliostat data"
            assert rows[0][0].startswith("# receiver_height"), "Missing header line for receiver height"
            assert rows[1][0].startswith("# receiver_angle_deg"), "Missing header line for receiver angle"