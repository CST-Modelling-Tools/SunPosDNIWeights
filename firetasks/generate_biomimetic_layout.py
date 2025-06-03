from fireworks import FiretaskBase, explicit_serialize, FWAction
from pathlib import Path
from layout_generators.biomimetic_spiral_layout_generator import generate_biomimetic_spiral_layout

@explicit_serialize
class GenerateBiomimeticSpiralLayoutFiretask(FiretaskBase):
    required_params = [
        "output_file", "num_heliostats", "tower_height",
        "a0", "b", "delta", "exclusion_radius"
    ]

    optional_params = ["receiver_height"]

    def run_task(self, fw_spec):
        output_file = Path(self["output_file"]).resolve()
        num_heliostats = int(self["num_heliostats"])
        tower_height = float(self["tower_height"])
        a0 = float(self["a0"])
        b = float(self["b"])
        delta = float(self["delta"])
        exclusion_radius = float(self["exclusion_radius"])
        receiver_height = float(self.get("receiver_height", 35.0))

        generate_biomimetic_spiral_layout(
            output_file=output_file,
            num_heliostats=num_heliostats,
            tower_height=tower_height,
            a0=a0,
            b=b,
            delta=delta,
            exclusion_radius=exclusion_radius,
            receiver_height=receiver_height
        )

        return FWAction()