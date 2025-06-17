# File: tests/test_optimizer_runner.py

import tempfile
import json
from pathlib import Path
from workflows import workflow_optimize_generation  # for patching
from firetasks import create_population_folder
from unittest.mock import patch, MagicMock
import sys

# Insert repository root into sys.path so we can import optimizer_runner
sys.path.insert(0, str(Path.cwd()))
from optimizer_runner import run_optimization_cycle


def test_optimizer_runner_single_generation():
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "tarancon_test"
        data_dir = project_dir / "data"
        results_dir = project_dir / "results"
        layouts_dir = project_dir / "layouts"
        scripts_dir = project_dir / "scripts"
        for d in [data_dir, results_dir, layouts_dir, scripts_dir]:
            d.mkdir(parents=True)

        # Write Tonatiuh script file
        (scripts_dir / "simulate_layout.tnhpps").write_text(
            "loadLayout('../layouts/layout_initial.csv')"
        )

        # Create dummy DNI and directions files
        (data_dir / "dni_tarancon_spain.csv").write_text("")
        (data_dir / "directions_with_weights_tarancon_spain.csv").write_text("")

        # Write project_config.json
        config = {
            "project_name": "tarancon_test",
            "location": {"latitude": 39.87, "longitude": -3.01},
            "data": {
                "dni_file": "data/dni_tarancon_spain.csv",
                "directions_with_weights_file": "data/directions_with_weights_tarancon_spain.csv"
            },
            "executables": {
                "sampling_exe": "/mock/path/sampling.exe",
                "tonatiuh_exe": "/mock/path/tonatiuh.exe",
                "energy_exe": "/mock/path/energy.exe"
            },
            "scripts": {"tonatiuh_script": "scripts/simulate_layout.tnhpps"},
            "folders": {"results": "results", "layouts": "layouts"},
            "optimization_config": {
                "type": "differential_evolution",
                "num_heliostats": 10,
                "bubble_radius": 4.5,
                "receiver_height": 35.0,
                "parameter_bounds": {
                    "a0": [5.0, 6.0],
                    "b": [0.5, 0.6],
                    "delta": [0.0, 0.1]
                },
                "population_size": 1,
                "max_generations": 1,
                "differential_evolution": {
                    "mutation_factor": 0.8,
                    "crossover_rate": 0.9
                }
            }
        }
        config_path = project_dir / "project_config.json"
        with open(config_path, "w") as f:
            json.dump(config, f)

        # Write dummy project_manager.py
        (project_dir / "project_manager.py").write_text("""
from pathlib import Path
import json

class ProjectManager:
    def __init__(self, config_path):
        with open(config_path, "r") as f:
            self.config = json.load(f)
        self.root_dir = Path(config_path).parent
        self.project_name = self.config["project_name"]
        self.parameter_sets_file = self.root_dir / "data" / "parameter_sets.csv"
        self.optimizer_type = self.config["optimization_config"]["type"]
        self.population_size = self.config["optimization_config"]["population_size"]
        self.max_generations = self.config["optimization_config"]["max_generations"]
        self.parameter_bounds = self.config["optimization_config"]["parameter_bounds"]
        self.mutation_factor = self.config["optimization_config"]["differential_evolution"]["mutation_factor"]
        self.crossover_rate = self.config["optimization_config"]["differential_evolution"]["crossover_rate"]
        self.num_heliostats = self.config["optimization_config"]["num_heliostats"]
        self.bubble_radius = self.config["optimization_config"]["bubble_radius"]
        self.receiver_height = self.config["optimization_config"]["receiver_height"]
""")

        # Patch FireWorks LaunchPad and workflow launch
        with patch("optimizer_runner.LaunchPad") as MockLaunchPad, \
            patch("optimizer_runner.get_optimize_generation_workflow") as mock_get_wf, \
            patch("optimizer_runner.CreateNextPopulationFolderFiretask") as mock_create_task, \
            patch("optimizer_runner.load_optimizer") as mock_load_optimizer:

            mock_lp = MagicMock()
            MockLaunchPad.auto_load.return_value = mock_lp
            mock_get_wf.return_value = MagicMock()

            mock_task = MagicMock()
            mock_create_task.return_value = mock_task
            mock_task.run_task.return_value = None

            # Mock optimizer
            mock_optimizer = MagicMock()
            mock_optimizer.is_done.side_effect = [False, True]  # Will run once
            mock_optimizer.suggest.return_value = [{"a0": 5.5, "b": 0.55, "delta": 0.05}]
            mock_load_optimizer.return_value = mock_optimizer

            run_optimization_cycle(str(config_path))

            assert mock_lp.add_wf.call_count == 1