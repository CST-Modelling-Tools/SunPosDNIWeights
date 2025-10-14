import os
import sys
import pandas as pd
import numpy as np

# -----------------------------------------------------------------------------
# Locate Excel file
# -----------------------------------------------------------------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
excel_path = os.path.join(
    project_root,
    "projects",
    "hyder_arizona_staggered_layout",
    "results",
    "parameter_sets.xlsx"
)

if not os.path.exists(excel_path):
    print(f"\n❌ Excel file not found at:\n   {excel_path}\n", file=sys.stderr)
    sys.exit(1)

print(f"\n✅ Loading data from: {excel_path}\n")

# -----------------------------------------------------------------------------
# Read Excel data
# -----------------------------------------------------------------------------
df = pd.read_excel(excel_path, sheet_name="parameter_sets - Copy")

# Keep only numeric columns
numeric_df = df.select_dtypes(include=[np.number])

# -----------------------------------------------------------------------------
# Compute Pearson and Spearman correlations
# -----------------------------------------------------------------------------
pearson_corr = numeric_df.corr(method="pearson")["fitnessValue"].sort_values(ascending=False)
spearman_corr = numeric_df.corr(method="spearman")["fitnessValue"].sort_values(ascending=False)

# Combine into one table
corr_df = pd.DataFrame({
    "Pearson": pearson_corr,
    "Spearman": spearman_corr
}).drop("fitnessValue")

# -----------------------------------------------------------------------------
# Display ranked sensitivities
# -----------------------------------------------------------------------------
print("📊 Parameter Sensitivity Summary (vs Fitness Value):\n")
print(corr_df.sort_values(by="Spearman", ascending=False).round(4))

# -----------------------------------------------------------------------------
# Optional: Save to CSV for record keeping
# -----------------------------------------------------------------------------
out_path = os.path.join(script_dir, "parameter_sensitivity_summary.csv")
corr_df.to_csv(out_path)
print(f"\n✅ Sensitivity summary saved to: {out_path}\n"