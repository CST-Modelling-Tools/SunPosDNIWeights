# File: firetasks/generate_biomimetic_layout_from_parameters.py

from fireworks import FiretaskBase, explicit_serialize, FWAction
from pathlib import Path
from layout_generators.layout_generator_biomimetic_spiral import BiomimeticSpiralGenerator

@explicit_serialize
class GenerateBiomimeticLayoutFiretask(FiretaskBase):
    required_params = [
        "parameters",          # [a0, b, delta]
        "output_layout_file",  # Path to output CSV
        "num_heliostats",      # e.g. 223
        "bubble_radius"        # e.g. 4.5
    ]

    optional_params = [
        "receiver_height"      # default to 35.0 if not provided
    ]

    def run_task(self, fw_spec):
        # Unpack inputs
        a0, b, delta = self["parameters"]
        output_file = Path(self["output_layout_file"]).resolve()
        num_heliostats = int(self["num_heliostats"])
        bubble_radius = float(self["bubble_radius"])
        receiver_height = float(self.get("receiver_height", 35.0))

        # Initialize generator and create layout
        generator = BiomimeticSpiralGenerator(
            num_heliostats=num_heliostats,
            bubble_radius=bubble_radius,
            receiver_height=receiver_height
        )
        generator.generate_layout(output_file, {"a0": a0, "b": b, "delta": delta})

        return FWAction()