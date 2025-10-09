# File: utils/project_manager.py

import json
from pathlib import Path
import csv
from jsonschema import validate, ValidationError


# -------------------- Helper Functions --------------------

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


# -------------------- ProjectManager --------------------

class ProjectManager:
    """
    Manages the project configuration, paths, and parameter metadata.

    Compatible with structured project_config.json containing:
      - physical_parameters
      - layout_generation_parameters
      - optimization_parameters

    Supports mixed optimizable/fixed parameters for parametric layout generators
    such as 'radial_staggered'.
    """

    def __init__(self, config_path):
        self.config_path = Path(config_path).resolve()
        with open(self.config_path, "r") as f:
            self.config = json.load(f)

        # Validate configuration against schema
        schema_path = Path(__file__).parent.parent / "utils" / "schemas" / "project_config_schema.json"
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found at {schema_path}")

        with open(schema_path, "r") as schema_file:
            schema = json.load(schema_file)

        try:
            validate(instance=self.config, schema=schema)
        except ValidationError as e:
            raise ValueError(f"Configuration file validation failed: {e.message}")

        # Top-level sections
        self.project_name = extract_value(self.config["project_name"])
        self.location = {
            "latitude": extract_value(self.config["location"]["latitude"]),
            "longitude": extract_value(self.config["location"]["longitude"]),
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

        # Parameter subsections
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

    # -------------------- Parameter Parsing --------------------

    def _parse_parameters(self):
        """
        Populate optimizable keys, bounds, and fixed parameters.
        Validates presence of proper bounds for all optimizable entries.
        """
        for section_name, section in [
            ("physical_parameters", self.physical_parameters),
            ("layout_generation_parameters", self.layout_generation_parameters),
        ]:
            for key, entry in section.items():
                if is_optimizable(entry):
                    bounds = extract_bounds(entry)
                    if not (isinstance(bounds, list) and len(bounds) == 2):
                        raise ValueError(
                            f"Optimizable parameter '{key}' in section '{section_name}' must have a valid [min, max] bounds list."
                        )
                    self._optimizable_keys.append(key)
                    self._bounds.append(bounds)
                else:
                    self._fixed_values[key] = extract_value(entry)

    # -------------------- Accessors --------------------

    def get_optimizable_keys(self):
        return self._optimizable_keys

    def get_bounds_list(self):
        return self._bounds

    def get_bounds_dict(self):
        return dict(zip(self._optimizable_keys, self._bounds))

    def get_fixed_parameters(self):
        """Return fixed (non-optimizable) parameters."""
        return self._fixed_values.copy()

    def get_all_parameter_keys(self):
        """
        Return ordered list of all parameter names for CSV / optimizer I/O:
          - Optimizable keys first (in config order)
          - Fixed parameters (alphabetically for determinism)
        """
        return self._optimizable_keys + sorted(self._fixed_values.keys())

    def build_parameter_dict(self, optimizable_values: dict) -> dict:
        """
        Merge optimizer-suggested values with fixed configuration parameters.
        Returns a flat dict suitable for generator invocation.
        """
        merged = {**self.get_fixed_parameters()}
        merged.update(optimizable_values)
        return merged

    def get_flat_physical_parameters(self):
        """Return all non-optimizable physical parameters."""
        result = {}
        for k, v in self.physical_parameters.items():
            if not is_optimizable(v):
                result[k] = extract_value(v)
        return result

    def get_layout_generation_parameters(self):
        """Return full layout generation parameter definitions."""
        return self.layout_generation_parameters.copy()

    # -------------------- Generator & Optimizer Info --------------------

    def get_layout_generator_type(self):
        return self.generator_type

    def get_optimizer_type(self):
        return self.optimizer_type

    def get_optimization_parameters(self):
        return self.optimization_parameters

    # -------------------- Executable & Path Accessors --------------------

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

    # -------------------- Project Structure Utilities --------------------

    @property
    def root_dir(self):
        return self.config_path.parent

    @property
    def parameter_sets_file(self):
        return self.root_dir / self.get_results_folder() / "parameter_sets.csv"

    def read_parameters_for_generation(self, generation_id_str):
        """
        Load parameters (without fitness) for a given generation.

        - Preserves identifiers (generation_id, candidate_id, candidate_tag)
        - Converts numeric strings to float
        - Omits fitnessValue column
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
                                cleaned[k] = v
                    rows.append(cleaned)
        return rows

    # -------------------- Optional Info --------------------

    def get_receiver_type(self):
        return extract_value(self.config.get("receiver", {}).get("type", "flat"))

    def get_field_geometry_type(self):
        return extract_value(self.config.get("field_geometry", {}).get("type", "polar"))