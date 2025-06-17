# File: firetasks/generate_layout_from_parameters.py

from fireworks import FiretaskBase, explicit_serialize, FWAction
from pathlib import Path
from layout_generators.layout_generator_factory import get_layout_generator

@explicit_serialize
class GenerateLayoutFromParametersFiretask(FiretaskBase):
    required_params = [
        "generator_type",       # e.g., "biomimetic_spiral"
        "parameters",           # dictionary, e.g., {"a0": 10.0, "b": 2.0, "delta": 0.0}
        "output_layout_file",   # path to generated CSV file
        "num_heliostats",       # e.g., 223
        "bubble_radius"         # e.g., 4.5
    ]

    optional_params = [
        "receiver_height"       # default = 35.0
    ]

    def run_task(self, fw_spec):
        generator_type = self["generator_type"]
        parameters = self["parameters"]
        output_file = Path(self["output_layout_file"]).resolve()
        num_heliostats = int(self["num_heliostats"])
        bubble_radius = float(self["bubble_radius"])
        receiver_height = float(self.get("receiver_height", 35.0))

        # Get generator class and instantiate
        GeneratorClass = get_layout_generator(generator_type)
        generator = GeneratorClass(
            num_heliostats=num_heliostats,
            bubble_radius=bubble_radius,
            receiver_height=receiver_height
        )

        # Generate layout file
        generator.generate_layout(output_file=output_file, parameters=parameters)

        return FWAction()