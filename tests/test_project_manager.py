import sys
from pathlib import Path
import math

# Add repo root to sys.path so imports from 'projects' work
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

# Import the ProjectManager
from projects.tarancon.project_manager import ProjectManager


def test_project_manager_basic_loading():
    config_path = repo_root / "projects" / "tarancon" / "project_config.json"
    manager = ProjectManager(config_path)

    assert manager.project_name == "tarancon_spain"
    assert math.isclose(manager.latitude, 39.872)
    assert math.isclose(manager.longitude, -3.01)

    assert manager.num_heliostats == 223
    assert math.isclose(manager.bubble_radius, 4.5)
    assert math.isclose(manager.receiver_height, 35.0)
    assert manager.population_size == 10
    assert manager.max_generations == 50

    assert math.isclose(manager.mutation_factor, 0.8)
    assert math.isclose(manager.crossover_rate, 0.9)

    assert manager.parameter_bounds["a0"] == [5.0, 20.0]
    assert manager.parameter_bounds["b"] == [0.5, 5.0]
    assert manager.parameter_bounds["delta"] == [0.0, 2 * math.pi]