import os
from pathlib import Path
from fireworks import LaunchPad
from workflows.workflow_generate_sampling import get_generate_sampling_workflow

# Get repo root
repo_root = Path(__file__).resolve().parents[3]
print(f"Repo root: {repo_root}")

# Load config path
config_path = repo_root / "projects" / "tarancon" / "project_config.json"

# Check config exists
if not config_path.exists():
    raise FileNotFoundError(f"Config file not found: {config_path}")

# Load launchpad
launchpad = LaunchPad.auto_load()

# Create and add workflow
wf = get_generate_sampling_workflow(config_path)
launchpad.add_wf(wf)
print(f"✅ Sampling workflow for project 'tarancon' added to LaunchPad.")