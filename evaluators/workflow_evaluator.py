from typing import Dict
from layout_generators.rectangular_layout_generator import generate_layout_file
from workflows.workflow_tarancon_full import get_tarancon_workflow
from fireworks import LaunchPad
from project_manager import ProjectManager
from pathlib import Path

def evaluate_layout(parameters: Dict[str, float], layout_file: Path, pm: ProjectManager) -> float:
    # Generate the layout file
    generate_layout_file(parameters, layout_file)

    # Get the FireWorks workflow
    wf = get_tarancon_workflow(pm, layout_file)

    # Connect to LaunchPad and add the workflow
    lpad = LaunchPad(
        host="localhost",
        port=27017,
        name="fireworks",
        username=None,
        password=None
    )
    lpad.add_wf(wf)

    # For now return dummy result
    return 0.0