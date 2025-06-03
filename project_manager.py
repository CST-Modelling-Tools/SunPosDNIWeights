from pathlib import Path
import json
import sys
from dataclasses import dataclass, field
from typing import Dict

@dataclass
class ProjectManager:
    root_dir: Path
    config_path: Path = field(init=False)
    config: Dict = field(init=False)

    def __post_init__(self):
        self.root_dir = Path(self.root_dir).resolve()
        self.config_path = (self.root_dir / "project_config.json").resolve()

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