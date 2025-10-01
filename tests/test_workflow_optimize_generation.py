# File: tests/test_workflow_optimize_generation.py

import pytest
from pathlib import Path
from fireworks import Workflow
from utils.project_manager import ProjectManager
from workflows.workflow_optimize_generation import get_optimize_generation_workflow
from utils.layout_utils import generate_layout_id


@pytest.fixture
def project_manager():
    config_path = Path("tests/data/project_config.json")
    return ProjectManager(config_path)


def test_get_optimize_generation_workflow(project_manager):
    project_root = project_manager.root_dir

    # Minimal valid parameter set (now includes num_heliostats + bubble_radius inside parameters)
    param_set = {
        "generation_id": "000",
        "parameters": {
            "receiver_height": 80.0,
            "flat_receiver_radius": 1.5,
            "flat_receiver_tilt": 0.0,
            "min_tower_clearance": 10.0,
            "north_only": True,
            "d0": 6.0,
            "alpha": 0.1,
            "a0": 0.5,
            "gamma": 0.01,
            "num_heliostats": 6500,
            "bubble_radius": 2.4,
        },
    }

    workflow = get_optimize_generation_workflow(
        project_root=project_root,
        parameter_population=[param_set],
        project_manager=project_manager,
    )

    # Assertions
    assert isinstance(workflow, Workflow)
    assert len(workflow.fws) == 1

    fw = workflow.fws[0]
    assert fw.name.startswith("Evaluate layout")
    assert len(fw.tasks) == 2

    gen_task = fw.tasks[0]
    fitness_task = fw.tasks[1]

    # Firetasks should be our custom ones
    assert "GenerateLayoutFromParametersFiretask" in str(gen_task.__class__)
    assert "ComputeFitnessFiretask" in str(fitness_task.__class__)


def test_generate_layout_id_consistency():
    params = {
        "a0": 0.25,
        "gamma": 0.01,
        "north_only": True,
        "count": 5,
    }
    layout_id = generate_layout_id("003", params)

    expected = "003_a0_0p25_count_5_gamma_0p01_north_only_true"
    assert layout_id == expected