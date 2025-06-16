from pathlib import Path
import json
import sys
from dataclasses import dataclass, field
from typing import Dict

@dataclass
class ProjectManager:
    config_path: Path = field(default=Path(__file__).parent / "project_config.json")
    config: Dict = field(init=False)
    root_dir: Path = field(init=False)

    def __post_init__(self):
        self.config_path = self.config_path.resolve()
        self.root_dir = self.config_path.parent

        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found at {self.config_path}")

        with open(self.config_path, 'r') as f:
            self.config = json.load(f)

        self._add_workflows_to_sys_path_if_needed()

    def _add_workflows_to_sys_path_if_needed(self):
        paths_config = self.config.get("paths", {})
        workflows_path = paths_config.get("workflows_dir")
        if workflows_path:
            full_path = (self.root_dir / workflows_path).resolve()
            if full_path.is_dir() and str(full_path) not in sys.path:
                sys.path.insert(0, str(full_path))

    @property
    def project_name(self):
        return self.config["project_name"]

    @property
    def latitude(self):
        return self.config["location"]["latitude"]

    @property
    def longitude(self):
        return self.config["location"]["longitude"]

    @property
    def dni_file(self):
        return (self.root_dir / self.config["data"]["dni_file"]).resolve()

    @property
    def directions_file(self):
        return (self.root_dir / self.config["data"]["directions_with_weights_file"]).resolve()

    @property
    def sampling_exe(self):
        return (self.root_dir / self.config["executables"]["sampling_exe"]).resolve()

    @property
    def tonatiuh_exe(self):
        return Path(self.config["executables"]["tonatiuh_exe"]).resolve()

    @property
    def energy_exe(self):
        return (self.root_dir / self.config["executables"]["energy_exe"]).resolve()

    @property
    def tonatiuh_script(self):
        return (self.root_dir / self.config["scripts"]["tonatiuh_script"]).resolve()

    @property
    def results_dir(self):
        return (self.root_dir / self.config["folders"]["results"]).resolve()

    @property
    def result_file_prefix(self):
        return self.config.get("result_file_prefix", self.project_name)

    @property
    def parameter_bounds(self):
        return self.config["optimization_config"]["parameter_bounds"]

    @property
    def population_size(self):
        return self.config["optimization_config"]["population_size"]

    @property
    def receiver_height(self):
        return self.config["optimization_config"]["receiver_height"]

    @property
    def bubble_radius(self):
        return self.config["optimization_config"]["bubble_radius"]

    @property
    def num_heliostats(self):
        return self.config["optimization_config"]["num_heliostats"]

    @property
    def max_generations(self):
        return self.config["optimization_config"]["max_generations"]

    @property
    def mutation_factor(self):
        return self.config["optimization_config"]["differential_evolution"]["mutation_factor"]

    @property
    def crossover_rate(self):
        return self.config["optimization_config"]["differential_evolution"]["crossover_rate"]

    @property
    def layouts_dir(self):
        return (self.root_dir / "layouts").resolve()

    @property
    def parameter_sets_file(self):
        return (self.root_dir / "data" / "parameter_sets.csv").resolve()