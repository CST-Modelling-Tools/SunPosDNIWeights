from typing import Dict
from pathlib import Path
import csv
import json

def generate_layout_file(params: Dict[str, float], output_path: Path, project_name: str = "tarancon", location: str = "default-location"):
    num_rows = int(round(params["num_rows"]))
    num_cols = int(round(params["num_cols"]))
    spacing_x = float(params["spacing_x"])
    spacing_y = float(params["spacing_y"])
    receiver_height = float(params["receiver_height"])

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        for r in range(num_rows):
            for c in range(num_cols):
                label = f"H{r:02}{c:03}"
                xc = c * spacing_x
                yc = r * spacing_y
                zc = 0.0
                xa = 0.0
                ya = 0.0
                za = receiver_height
                writer.writerow([label, xc, yc, zc, xa, ya, za])

    config = {
        "project_name": project_name,
        "receiver_height": receiver_height,
        "receiver_angle_deg": 0.0,
        "location": location
    }

    config_path = output_path.parent / "config.json"
    with config_path.open("w") as f:
        json.dump(config, f, indent=2)