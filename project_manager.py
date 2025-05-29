from pathlib import Path
import json
from dataclasses import dataclass, field
from typing import Dict

@dataclass
class ProjectManager:
    root_dir: Path
    config_path: Path = field(init=False)
    config: Dict = field(init=False)

    def __post_init__(self):
        self.root_dir = self.root_dir.resolve()
        self.config_path = (self.root_dir / "config.json").resolve()
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found at {self.config_path}")
        with open(self.config_path, 'r') as f:
            self.config = json.load(f)

        # Validate required fields
        required_keys = [
            "project_name",
            "location",
            "dni",
            "scripts",
            "folders",
            "initial_layout",
            "sampling_file",
            "result_file_prefix",
            "executables"
        ]
        for key in required_keys:
            if key not in self.config:
                raise ValueError(f"Missing required key in config: '{key}'")

    @property
    def project_name(self):
        return self.config["project_name"]

    @property
    def latitude(self):
        return self.config["location"]["latitude_deg"]

    @property
    def longitude(self):
        return self.config["location"]["longitude_deg"]

    @property
    def dni_file(self):
        return (self.root_dir / self.config["dni"]["file"]).resolve()

    @property
    def tonatiuh_script(self):
        return (self.root_dir / self.config["scripts"]["tonatiuh_script"]).resolve()

    @property
    def layouts_dir(self):
        return (self.root_dir / self.config["folders"]["layouts"]).resolve()

    @property
    def results_dir(self):
        return (self.root_dir / self.config["folders"]["results"]).resolve()

    @property
    def data_dir(self):
        return (self.root_dir / self.config["folders"]["data"]).resolve()

    @property
    def initial_layout_file(self):
        return (self.layouts_dir / self.config["initial_layout"]).resolve()

    @property
    def sampling_file(self):
        return (self.results_dir / self.config["sampling_file"]).resolve()

    @property
    def result_file_prefix(self):
        return self.config["result_file_prefix"]

    @property
    def sampling_exe(self):
        return (self.root_dir / self.config["executables"]["sampling_exe"]).resolve()

    @property
    def tonatiuh_exe(self):
        return Path(self.config["executables"]["tonatiuh_exe"]).resolve()

    @property
    def energy_exe(self):
        return (self.root_dir / self.config["executables"]["energy_exe"]).resolve()

    def make_dirs(self):
        self.layouts_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)