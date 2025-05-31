import sys
from pathlib import Path

# Step 1: Locate the root of the repository
current_file = Path(__file__).resolve()
repo_root = current_file.parents[3]  # Goes from scripts/ → tarancon/ → projects/ → SunPosDNIWeights

# Step 2: Add root of the repo to Python path
sys.path.insert(0, str(repo_root))

# Step 3: Check that project_manager.py is found
project_manager_path = repo_root / "project_manager.py"
print("Repo root:", repo_root)
print("Checking project_manager.py exists:", project_manager_path.exists())

if not project_manager_path.exists():
    raise FileNotFoundError(f"Expected project_manager.py at {project_manager_path}, but it was not found.")

# Step 4: Import and launch the workflow
from project_manager import ProjectManager
from workflows.workflow_tarancon_full import get_tarancon_workflow
from fireworks import LaunchPad

if __name__ == "__main__":
    # Initialize project
    pm = ProjectManager(root_dir=repo_root / "projects" / "tarancon")
    layout_file = pm.initial_layout_file

    # Load FireWorks launchpad (from ~/.fireworks/my_launchpad.yaml by default)
    launchpad = LaunchPad.auto_load()

    # Generate and add workflow
    wf = get_tarancon_workflow(pm, layout_file)
    launchpad.add_wf(wf)

    print(f"✅ Workflow for project '{pm.project_name}' added to LaunchPad.")