# File: tests/test_project_manager.py

import pytest
from pathlib import Path
from utils.project_manager import ProjectManager


@pytest.fixture(scope="module")
def project_manager():
    config_path = Path("tests/data/project_config.json").resolve()
    return ProjectManager(config_path)


def test_project_manager_initialization(project_manager):
    assert project_manager.project_name == "hyder_arizona_staggered_layout"
    assert project_manager.location["latitude"] == 33.024436
    assert project_manager.location["longitude"] == -113.381777


def test_get_optimizable_keys(project_manager):
    keys = project_manager.get_optimizable_keys()
    expected_keys = ["receiver_height", "flat_receiver_radius", "d0", "alpha", "a0", "gamma"]
    assert set(keys) == set(expected_keys)


def test_get_bounds_dict(project_manager):
    bounds = project_manager.get_bounds_dict()
    assert bounds["receiver_height"] == [70.0, 90.0]
    assert bounds["gamma"] == [0.0, 0.02]


def test_get_fixed_parameters(project_manager):
    fixed = project_manager.get_fixed_parameters()
    assert fixed["num_heliostats"] == 6500
    assert fixed["north_only"] is True


def test_build_parameter_dict(project_manager):
    x = [75.0, 1.2, 6.0, 0.1, 0.5, 0.01]
    full_params = project_manager.build_parameter_dict(x)
    assert full_params["receiver_height"] == 75.0
    assert full_params["flat_receiver_radius"] == 1.2
    assert full_params["num_heliostats"] == 6500  # fixed param


def test_get_optimization_parameters(project_manager):
    params = project_manager.get_optimization_parameters()
    assert params["population_size"] == 10
    assert params["crossover_rate"] == 0.6


def test_executable_paths(project_manager):
    assert "Tonatiuh" in project_manager.get_tonatiuh_exe()
    assert project_manager.get_energy_exe().endswith("AnnualEnergy")
    assert project_manager.get_sampling_exe().endswith("GenerateSamplingDirectionsAndWeights")


def test_paths_and_folders(project_manager):
    assert project_manager.get_dni_file().endswith(".csv")
    assert project_manager.get_directions_file().endswith(".csv")
    assert project_manager.get_results_folder() == "results"
    assert project_manager.get_workflows_dir() == "../../workflows"


def test_read_parameters_for_generation(project_manager):
    gen_000 = project_manager.read_parameters_for_generation("000")
    assert isinstance(gen_000, list)
    assert len(gen_000) == 1
    assert gen_000[0]["receiver_height"] == 80.0
    assert gen_000[0]["gamma"] == 0.01


def test_receiver_and_field_types(project_manager):
    assert project_manager.get_receiver_type() == "flat"
    assert project_manager.get_field_geometry_type() == "polar"