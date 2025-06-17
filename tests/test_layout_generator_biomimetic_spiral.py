import tempfile
import csv
from pathlib import Path
from layout_generators.layout_generator_biomimetic_spiral import BiomimeticSpiralGenerator

def test_biomimetic_spiral_generator_output():
    num_heliostats = 10
    bubble_radius = 4.5
    receiver_height = 35.0
    parameters = {
        "a0": 10.0,
        "b": 2.0,
        "delta": 0.0
    }

    generator = BiomimeticSpiralGenerator(
        num_heliostats=num_heliostats,
        bubble_radius=bubble_radius,
        receiver_height=receiver_height
    )

    with tempfile.TemporaryDirectory() as tmpdirname:
        output_path = Path(tmpdirname) / "layout.csv"
        generator.generate_layout(output_path, parameters)

        # Read generated file
        with open(output_path, newline='') as f:
            reader = list(csv.reader(f))
            assert len(reader) == num_heliostats + 2, "Expected header + heliostat rows"
            assert reader[0][0].startswith("# receiver_height:"), "Missing receiver height header"
            assert reader[1][0].startswith("# receiver_angle_deg:"), "Missing receiver angle header"