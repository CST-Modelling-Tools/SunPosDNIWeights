# File: firetasks/generate_layout_from_parameters.py

from fireworks import FiretaskBase, explicit_serialize, FWAction
from pathlib import Path
from layout_generators.layout_generator_factory import get_layout_generator


@explicit_serialize
class GenerateLayoutFromParametersFiretask(FiretaskBase):
    """
    Firetask that generates a heliostat field layout from a set of parameters.
    All parameters (optimizable + fixed) must be passed in `parameters`.
    """

    required_params = [
        "generator_type",   # "biomimetic_spiral", "octagon_biomimetic_spiral", "radial_staggered"
        "parameters",       # dict of parameters (optimizable + fixed)
        "layout_file",      # full path for generated layout CSV (naming done in workflow)
    ]

    def run_task(self, fw_spec):
        generator_type = self["generator_type"]
        parameters = self._normalize_parameters(generator_type, self["parameters"])

        layout_file = Path(self["layout_file"]).resolve()

        # Core required parameters
        try:
            num_heliostats = int(parameters["num_heliostats"])
            bubble_radius = float(parameters["bubble_radius"])
            receiver_height = float(parameters["receiver_height"])
        except KeyError as e:
            raise ValueError(f"[ERROR] Missing required parameter: {e.args[0]} in {parameters}") from e
        except (TypeError, ValueError) as e:
            raise ValueError(f"[ERROR] Invalid type for core parameters in {parameters}") from e

        # Construct generator
        generator = self._construct_generator(
            generator_type=generator_type,
            num_heliostats=num_heliostats,
            bubble_radius=bubble_radius,
            receiver_height=receiver_height,
            parameters=parameters,
        )

        # Generate layout CSV
        try:
            generator.generate_layout(output_file=layout_file, parameters=parameters)
        except RuntimeError as e:
            print(f"[WARNING] Skipping layout due to generation error: {e}")
            return FWAction()

        print(f"[INFO] Layout file generated: {layout_file}")
        return FWAction()

    def _normalize_parameters(self, generator_type, parameters):
        """
        Ensure parameters are in dict form.
        Legacy support for list inputs (still allowed by optimizers).
        """
        if isinstance(parameters, dict):
            return parameters

        elif isinstance(parameters, list):
            if generator_type == "radial_staggered":
                if len(parameters) != 4:
                    raise ValueError("Expected 4 values for 'radial_staggered': [d0, alpha, a0, gamma]")
                return {"d0": parameters[0], "alpha": parameters[1], "a0": parameters[2], "gamma": parameters[3]}
            else:
                if len(parameters) != 3:
                    raise ValueError("Expected 3 values for spiral types: [a0, b, delta]")
                return {"a0": parameters[0], "b": parameters[1], "delta": parameters[2]}

        else:
            raise TypeError("Invalid format for 'parameters'; must be dict or list.")

    def _construct_generator(self, generator_type, num_heliostats, bubble_radius, receiver_height, parameters):
        """
        Select and initialize the appropriate layout generator.
        """
        GeneratorClass = get_layout_generator(generator_type)

        if generator_type == "octagon_biomimetic_spiral":
            return GeneratorClass(
                num_heliostats=num_heliostats,
                bubble_radius=bubble_radius,
                receiver_height=receiver_height,
                receiver_radial_distance=float(parameters["receiver_radial_distance"]),
                receiver_radius=float(parameters["receiver_radius"]),
                octagon_radius=float(parameters["octagon_radius"]),
                receiver_tilt_deg=float(parameters["receiver_tilt_deg"]),
            )

        elif generator_type == "radial_staggered":
            return GeneratorClass(
                num_heliostats=num_heliostats,
                bubble_radius=bubble_radius,
                receiver_height=receiver_height,
                min_tower_clearance=float(parameters["min_tower_clearance"]),
                north_only=bool(parameters["north_only"]),
            )

        else:  # biomimetic_spiral and others
            return GeneratorClass(
                num_heliostats=num_heliostats,
                bubble_radius=bubble_radius,
                receiver_height=receiver_height,
            )