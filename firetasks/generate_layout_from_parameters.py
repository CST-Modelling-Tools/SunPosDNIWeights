# File: firetasks/generate_layout_from_parameters.py

from fireworks import FiretaskBase, explicit_serialize, FWAction
from pathlib import Path
from layout_generators.layout_generator_factory import get_layout_generator

@explicit_serialize
class GenerateLayoutFromParametersFiretask(FiretaskBase):
    required_params = [
        "generator_type",       # e.g., "biomimetic_spiral" or "octagon_biomimetic_spiral"
        "parameters",           # list or dict
        "output_layout_file",   # path to generated CSV file
        "num_heliostats",       # e.g., 290
        "bubble_radius"         # e.g., 2.4
    ]

    optional_params = [
        "receiver_height",          # default = 35.0
        "receiver_radial_distance"  # optional, needed for octagon generator
    ]

    def run_task(self, fw_spec):
        generator_type = self["generator_type"]
        parameters = self["parameters"]

        # Normalize parameters if passed as list
        if isinstance(parameters, list):
            if len(parameters) != 3:
                raise ValueError("Expected 3 values in parameters list: [a0, b, delta]")
            parameters = {"a0": parameters[0], "b": parameters[1], "delta": parameters[2]}

        output_file = Path(self["output_layout_file"]).resolve()
        num_heliostats = int(self["num_heliostats"])
        bubble_radius = float(self["bubble_radius"])
        receiver_height = float(self.get("receiver_height", 35.0))
        receiver_radial_distance = self.get("receiver_radial_distance", None)

        # Get generator class from factory
        GeneratorClass = get_layout_generator(generator_type)

        # Select generator type and initialize with correct parameters
        if generator_type == "octagon_biomimetic_spiral":
            if receiver_radial_distance is None:
                raise ValueError("receiver_radial_distance must be provided for octagon layout.")
            generator = GeneratorClass(
                num_heliostats=num_heliostats,
                bubble_radius=bubble_radius,
                receiver_height=receiver_height,
                receiver_radial_distance=receiver_radial_distance
            )
        else:
            generator = GeneratorClass(
                num_heliostats=num_heliostats,
                bubble_radius=bubble_radius,
                receiver_height=receiver_height
            )

        # Generate layout file
        try:
            generator.generate_layout(output_file=output_file, parameters=parameters)
        except RuntimeError as e:
            print(f"[WARNING] Skipping layout due to generation error: {e}")
            return FWAction()

        return FWAction()