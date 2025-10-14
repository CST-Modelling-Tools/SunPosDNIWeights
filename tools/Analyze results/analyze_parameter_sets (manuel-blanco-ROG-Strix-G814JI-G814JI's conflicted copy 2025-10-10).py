import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 (needed for 3D projection)

# -----------------------------------------------------------------------------
# Locate the Excel file robustly
# -----------------------------------------------------------------------------
# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Go two levels up: "Analyze results" → "tools" → project root
project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))

# Build the full path to the Excel file
excel_path = os.path.join(
    project_root,
    "projects",
    "hyder_arizona_staggered_layout",
    "results",
    "parameter_sets.xlsx"
)

# Check that the file exists
if not os.path.exists(excel_path):
    print(f"\n❌ ERROR: Excel file not found at:\n   {excel_path}\n", file=sys.stderr)
    sys.exit(1)

print(f"\n✅ Loading data from: {excel_path}\n")

# -----------------------------------------------------------------------------
# Read data from Excel
# -----------------------------------------------------------------------------
try:
    df = pd.read_excel(excel_path, sheet_name="parameter_sets - Copy")
except Exception as e:
    print(f"❌ Error reading Excel file: {e}", file=sys.stderr)
    sys.exit(1)

print(df[["packing", "inner_bias", "fitnessValue"]].corr())

# -----------------------------------------------------------------------------
# Create 3D scatter plot
# -----------------------------------------------------------------------------
fig = plt.figure(figsize=(9, 7))
ax = fig.add_subplot(111, projection='3d')

# Scatter plot
p = ax.scatter(
    df["packing"],
    df["inner_bias"],
    df["fitnessValue"],
    c=df["fitnessValue"],
    cmap="inferno",
    s=30,
    alpha=0.9,
    edgecolor="k"
)

# Axis labels and title
ax.set_xlabel("Packing", fontsize=11, labelpad=8)
ax.set_ylabel("Inner Bias", fontsize=11, labelpad=8)
ax.set_zlabel("Fitness (η_opt)", fontsize=11, labelpad=8)
ax.set_title("3D Scatter Plot: Fitness vs Packing and Inner Bias", fontsize=13, pad=12)

# Add colorbar for fitness values
cbar = plt.colorbar(p, ax=ax, shrink=0.6, pad=0.1)
cbar.set_label("Fitness Value (η_opt)", fontsize=10)

# Make it interactive and nicer to view
ax.view_init(elev=25, azim=45)
plt.tight_layout()
plt.show()