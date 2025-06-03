import numpy as np
from pathlib import Path
import math
import csv

def generate_biomimetic_spiral_layout(
    output_file: Path,
    num_heliostats: int,
    tower_height: float,
    a0: float,
    b: float,
    delta: float,
    exclusion_radius: float,
    receiver_height: float = 35.0,
):
    """
    Generates a biomimetic spiral heliostat layout in the north field
    and writes it to a CSV file.

    Parameters:
        output_file: Path to the output CSV file.
        num_heliostats: Number of heliostats to generate.
        tower_height: Height of the tower base (zc for heliostats).
        a0, b, delta: Spiral parameters as described in Noone et al. (2012).
        exclusion_radius: Minimum allowed distance between heliostat centers.
        receiver_height: Height of the receiver.
    """
    layout_data = []
    aperture_center = np.array([0.0, 0.0, receiver_height])
    placed_positions = []

    theta = 0.0
    i = 0
    max_attempts = 100000
    attempts = 0

    while len(layout_data) < num_heliostats and attempts < max_attempts:
        r = a0 + b * theta
        x = r * np.cos(theta + delta)
        y = r * np.sin(theta + delta)
        z = tower_height

        if y > 0:  # Only place in the north field
            new_pos = np.array([x, y])
            too_close = any(np.linalg.norm(new_pos - np.array([xp, yp])) < 2 * exclusion_radius
                            for xp, yp in placed_positions)
            if not too_close:
                slant_range = np.linalg.norm(aperture_center - np.array([x, y, z]))
                heliostat_id = f"H{i+1:03d}"
                layout_data.append((heliostat_id, x, y, z, slant_range))
                placed_positions.append((x, y))
                i += 1

        theta += np.deg2rad(1.0)  # advance in small angular steps
        attempts += 1

    if len(layout_data) < num_heliostats:
        raise RuntimeError(f"Failed to place {num_heliostats} heliostats in north field after {max_attempts} attempts.")

    # Compute receiver angle based on y-z projection
    directions = []
    for (_, x, y, z, _) in layout_data:
        vec = aperture_center - np.array([x, y, z])
        vec[0] = 0  # project onto y-z plane
        norm = np.linalg.norm(vec)
        if norm > 0:
            directions.append(vec / norm)

    avg_direction = np.mean(directions, axis=0)
    angle_rad = math.acos(np.clip(np.dot(avg_direction, [0, 1, 0]), -1.0, 1.0))
    if avg_direction[2] < 0:
        angle_rad = -angle_rad
    receiver_angle_deg = np.rad2deg(angle_rad)

    # Write CSV
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([f"# receiver_height: {receiver_height}"])
        writer.writerow([f"# receiver_angle_deg: {receiver_angle_deg:.6f}"])
        for row in layout_data:
            writer.writerow(row)