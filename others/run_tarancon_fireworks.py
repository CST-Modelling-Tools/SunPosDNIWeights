import os
import subprocess
import sys
from pathlib import Path

# Get the repo root (assumes script is in projects/tarancon/scripts/)
script_path = Path(__file__).resolve()
repo_root = script_path.parents[3]  # Go up 3 levels to reach repo root

# Set PYTHONPATH to include the repo root
env = os.environ.copy()
env["PYTHONPATH"] = str(repo_root)

print(f"🔧 Setting PYTHONPATH to: {repo_root}")
print("🚀 Launching FireWorks rapidfire...")

# Call rlaunch rapidfire using the same Python environment
subprocess.run(["rlaunch", "rapidfire"], env=env)