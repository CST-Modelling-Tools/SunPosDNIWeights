import tempfile
from pathlib import Path
import csv

from layout_generators.layout_generator_factory import get_layout_generator

def test_biomimetic_factory_integration():
    # Configuration for the test
    generator_type = "biomimetic_spiral"
    num_heliostats = 10
    receiver_height = 35.0
    bubble_radius = 4.5

    parameters = {
        "a0": 10.0,
        "b": 2.0,
        "delta": 0.0
    }

    with tempfile.TemporaryDirectory() as tmpdirname:
        output_path = Path(tmpdirname) / "layout_test.csv"

        # Instantiate generator class from factory
        generator_class = get_layout_generator(generator_type)
        generator = generator_class(
            num_heliostats=num_heliostats,
            bubble_radius=bubble_radius,
            receiver_height=receiver_height
        )

        # Generate layout
        generator.generate_layout(output_file=output_path, parameters=parameters)

        # Check output file exists and is not empty
        assert output_path.exists(), "Layout CSV file was not created."

        with open(output_path, newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)

        # At least 2 comment rows and 1 heliostat row expected
        assert len(rows) > 2, "Layout file does not contain enough data rows."
        assert rows[0][0].startswith("# receiver_height")
        assert rows[1][0].startswith("# receiver_angle_deg")
        assert rows[2][0].startswith("H"), "First heliostat row does not have expected format."