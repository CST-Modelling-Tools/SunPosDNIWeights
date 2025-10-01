# File: utils/project_manager.py

import json
from pathlib import Path
import csv
from jsonschema import validate, ValidationError


def extract_value(entry):
    if isinstance(entry, dict):
        return entry.get("value")
    return entry


def extract_bounds(entry):
    if isinstance(entry, dict):
        return entry.get("bounds")
    return None


def is_optimizable(entry):
    return isinstance(entry, dict) and entry.get("optimizable", False)


def extract_type(entry):
    if isinstance(entry, dict):
        return entry.get("type")
    return type(entry).__name__


class ProjectManager:
    def __init__(self, config_path):
        self.config_path = Path(config_path).resolve()
        with open(self.config_path, 'r') as f:
            self.config = json.load(f)

        schema_path = Path(__file__).parent.parent / "utils" / "schemas" / "project_config_schema.json"
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found at {schema_path}")

        with open(schema_path, 'r') as schema_file:
            schema = json.load(schema_file)

        try:
            validate(instance=self.config, schema=schema)
        except ValidationError as e:
            raise ValueError(f"Configuration file validation failed: {e.message}")

        # Top-level config keys
        self.project_name = extract_value(self.config["project_name"])
        self.location = {
            "latitude": extract_value(self.config["location"]["latitude"]),
            "longitude": extract_value(self.config["location"]["longitude"])
        }
        self.data_paths = {k: extract_value(v) for k, v in self.config["data"].items()}
        self.executables = {k: extract_value(v) for k, v in self.config["executables"].items()}
        self.scripts = {k: extract_value(v) for k, v in self.config["scripts"].items()}
        self.folders = {k: extract_value(v) for k, v in self.config["folders"].items()}
        self.paths = {k: extract_value(v) for k, v in self.config["paths"].items()}

        # Optimization configuration
        self.optimization_config = self.config["optimization_config"]
        self.generator_type = extract_value(self.optimization_config["layout_generator_type"])
        self.optimizer_type = extract_value(self.optimization_config["type"])

        # Parameter sections
        self.physical_parameters = self.optimization_config.get("physical_parameters", {})
        self.layout_generation_parameters = self.optimization_config.get("layout_generation_parameters", {})
        self.optimization_parameters = {
            k: extract_value(v) for k, v in self.optimization_config.get("optimization_parameters", {}).items()
        }

        # Internal storage
        self._optimizable_keys = []
        self._bounds = []
        self._fixed_values = {}

        self._parse_parameters()

    def _parse_parameters(self):
        for section in [self.physical_parameters, self.layout_generation_parameters]:
            for key, entry in section.items():
                if is_optimizable(entry):
                    bounds = extract_bounds(entry)
                    if bounds is not None and len(bounds) == 2:
                        self._optimizable_keys.append(key)
                        self._bounds.append(bounds)
                else:
                    self._fixed_values[key] = extract_value(entry)

    # --- Parameter Accessors ---

    def get_optimizable_keys(self):
        return self._optimizable_keys

    def get_bounds_list(self):
        return self._bounds

    def get_bounds_dict(self):
        return dict(zip(self._optimizable_keys, self._bounds))

    def get_fixed_parameters(self):
        return self._fixed_values.copy()

    def get_all_parameter_keys(self):
        """
        Return a consistent ordered list of parameter keys for CSV I/O.

        - Optimizable keys first (in the order defined in config).
        - Then fixed parameters (sorted for determinism).
        """
        return self._optimizable_keys + sorted(self._fixed_values.keys())

    def build_parameter_dict(self, optimizable_values: dict) -> dict:
        """
        Merge optimizer-suggested values with fixed parameters from config.
        Ensures final dict has concrete values, not placeholders.
        """
        merged = {}

        # Start with fixed parameters (always actual values)
        for key, val in self.get_fixed_parameters().items():
            merged[key] = val if not isinstance(val, dict) else val.get("value")

        # Add optimizable ones
        for key, val in optimizable_values.items():
            merged[key] = val

        return merged

    def get_flat_physical_parameters(self):
        result = {}
        for k, v in self.physical_parameters.items():
            if is_optimizable(v):
                continue
            result[k] = extract_value(v)
        return result

    # --- Generator and Optimizer Info ---

    def get_layout_generator_type(self):
        return self.generator_type

    def get_optimizer_type(self):
        return self.optimizer_type

    def get_optimization_parameters(self):
        return self.optimization_parameters

    # --- Executable & Path Accessors ---

    def get_script_path(self):
        return self.scripts["tonatiuh_script"]

    def get_tonatiuh_exe(self):
        return self.executables["tonatiuh_exe"]

    def get_energy_exe(self):
        return self.executables["energy_exe"]

    def get_sampling_exe(self):
        return self.executables["sampling_exe"]

    def get_dni_file(self):
        return self.data_paths["dni_file"]

    def get_directions_file(self):
        return self.data_paths["directions_with_weights_file"]

    def get_results_folder(self):
        return self.folders["results"]

    def get_workflows_dir(self):
        return self.paths["workflows_dir"]

    # --- Project Structure Utilities ---

    @property
    def root_dir(self):
        return self.config_path.parent

    @property
    def parameter_sets_file(self):
        return self.root_dir / self.get_results_folder() / "parameter_sets.csv"

    def read_parameters_for_generation(self, generation_id_str):
        """
        Load parameters (without fitness) for a given generation.

        - Preserves identifiers (generation_id, candidate_id, candidate_tag) as strings.
        - Converts numeric parameter values to float where possible.
        - Drops the fitnessValue column.
        """
        rows = []
        with open(self.parameter_sets_file, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["generation_id"] == generation_id_str:
                    cleaned = {}
                    for k, v in row.items():
                        if k in ("generation_id", "candidate_id", "candidate_tag"):
                            cleaned[k] = v
                        elif k == "fitnessValue":
                            continue
                        else:
                            try:
                                cleaned[k] = float(v)
                            except (ValueError, TypeError):
                                cleaned[k] = v  # keep raw if not convertible
                    rows.append(cleaned)
        return rows

    # --- Optional: Receiver & Geometry Types ---

    def get_receiver_type(self):
        return extract_value(self.config.get("receiver", {}).get("type", "flat"))

    def get_field_geometry_type(self):
        return extract_value(self.config.get("field_geometry", {}).get("type", "polar"))