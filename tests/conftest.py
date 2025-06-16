import sys
from pathlib import Path

# Add repository root to sys.path for all tests
REPO_ROOT = Path(__file__).resolve().parents[0]
sys.path.insert(0, str(REPO_ROOT))