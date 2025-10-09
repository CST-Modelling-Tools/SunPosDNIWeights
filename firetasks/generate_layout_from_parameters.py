# File: firetasks/generate_layout_from_parameters.py

from fireworks import FiretaskBase, explicit_serialize, FWAction
from pathlib import Path
from layout_generators.layout_generator_factory import get_layout_generator


@explicit_serialize
class GenerateLayoutFromParametersFiretask(FiretaskBase):
    """
    Firetask that generates a heliostat field layout from a set of parameters.

    Compatible with structured parameter dictionaries as defined in project_config.json.
    Supports generator types:
        - biomimetic_spiral
        - octagon_biomimetic_spiral
        - radial_staggered
    """

    required_params = [
        "generator_type",   # e.g., "radial_staggered"
        "parameters",       # dict of parameters (optimizable + fixed)
        "layout_file",      # full output CSV path
    ]

    def run_task(self, fw_spec):
        generator_type = self["generator_type"]
        parameters = self._normalize_parameters(self["parameters"])
        layout_file = Path(self["layout_file"]).resolve()

        # Core parameters (must exist)
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

        # Generate layout
        try:
            generator.generate_layout(output_file=layout_file, parameters=parameters)
        except RuntimeError as e:
            print(f"[WARNING] Skipping layout generation for {generator_type} due to error: {e}")
            return FWAction()

        print(f"[INFO] Layout file generated: {layout_file}")
        return FWAction()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _normalize_parameters(self, parameters):
        """
        Ensure parameters are a dict of concrete numeric values.
        Converts numeric strings to floats where applicable.
        """
        if not isinstance(parameters, dict):
            raise TypeError("Invalid format for 'parameters'; must be a dictionary.")

        normalized = {}
        for k, v in parameters.items():
            try:
                normalized[k] = float(v)
            except (ValueError, TypeError):
                normalized[k] = v  # Keep non-numeric entries as is (e.g., bools)
        return normalized

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
                min_tower_clearance=float(parameters.get("min_tower_clearance", 3.0)),
                north_only=bool(parameters.get("north_only", False)),  # API compatibility
                design_beta_deg=float(parameters.get("design_beta_deg", 25.0)),
                kr=float(parameters.get("kr", 1.0)),
            )

        else:  # biomimetic_spiral and other simpler generators
            return GeneratorClass(
                num_heliostats=num_heliostats,
                bubble_radius=bubble_radius,
                receiver_height=receiver_height,
            )