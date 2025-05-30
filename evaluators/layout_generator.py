import csv
from pathlib import Path
from typing import Dict

def layout_generator(parameters: Dict[str, float], layout_path: Path) -> None:
    """
    Generates a heliostat layout CSV file based on input parameters.

    Args:
        parameters (Dict[str, float]): Dictionary of parameters (e.g., num_rows, num_cols, spacing_x, spacing_y).
        layout_path (Path): Path to the output CSV file.
    """
    num_rows = int(parameters.get("num_rows", 5))
    num_cols = int(parameters.get("num_cols", 5))
    spacing_x = parameters.get("spacing_x", 10.0)  # meters
    spacing_y = parameters.get("spacing_y", 10.0)  # meters

    layout_path.parent.mkdir(parents=True, exist_ok=True)

    with open(layout_path, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["id", "x", "y", "z"])  # CSV header

        heliostat_id = 1
        for row in range(num_rows):
            for col in range(num_cols):
                x = col * spacing_x
                y = row * spacing_y
                z = 0.0
                writer.writerow([heliostat_id, x, y, z])
                heliostat_id += 1