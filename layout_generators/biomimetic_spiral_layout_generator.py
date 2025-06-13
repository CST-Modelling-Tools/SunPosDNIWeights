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
    receiver_height: float = 35.0,
    bubble_radius: float = 4.5  # minimum allowed distance from center to center is 2 * bubble_radius
):
    """
    Generates a biomimetic spiral heliostat layout for a north field and writes it to a CSV file.

    Parameters:
        output_file: Path to the output CSV file.
        num_heliostats: Number of heliostats to generate.
        tower_height: Height of the tower base (not used here, but may be useful in future).
        a0, b, delta: Spiral parameters as described in Noone et al. (2012).
        receiver_height: Fixed receiver height (z position of receiver center).
        bubble_radius: Minimum allowed radius for heliostat placement (enforced exclusion radius).
    """
    aperture_center = np.array([0.0, 0.0, receiver_height])
    layout_data = []

    angle = 0.0
    placed = 0
    max_iterations = 10000
    iteration = 0

    while placed < num_heliostats and iteration < max_iterations:
        r = a0 + b * angle
        x = r * math.cos(angle + delta)
        y = r * math.sin(angle + delta)
        z = 0.0  # Heliostats are located at ground level

        if y < 0:
            angle += math.radians(1)
            iteration += 1
            continue

        candidate = np.array([x, y, z])

        # Check minimum spacing
        too_close = False
        for (_, xj, yj, zj, _) in layout_data:
            dist = math.sqrt((x - xj)**2 + (y - yj)**2)
            if dist < 2 * bubble_radius:
                too_close = True
                break

        if too_close:
            angle += math.radians(1)
            iteration += 1
            continue

        slant_range = np.linalg.norm(aperture_center - candidate)
        heliostat_id = f"H{placed+1:03d}"
        layout_data.append((heliostat_id, x, y, z, slant_range))
        placed += 1
        angle += math.radians(1)
        iteration += 1

    if placed < num_heliostats:
        raise RuntimeError(f"Only placed {placed} heliostats out of {num_heliostats}. Try adjusting parameters.")

    # Compute receiver angle (average direction in y-z plane)
    directions = []
    for (_, x, y, z, _) in layout_data:
        vec = aperture_center - np.array([x, y, z])
        vec[0] = 0  # projection onto y-z plane
        if np.linalg.norm(vec) > 0:
            vec = vec / np.linalg.norm(vec)
            directions.append(vec)
    avg_direction = np.mean(directions, axis=0)
    receiver_angle_rad = math.acos(np.dot(avg_direction, np.array([0, 1, 0])))
    if avg_direction[2] < 0:
        receiver_angle_rad = -receiver_angle_rad
    receiver_angle_deg = 180.0 - np.rad2deg(receiver_angle_rad)

    # Write to CSV
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([f"# receiver_height: {receiver_height}"])
        writer.writerow([f"# receiver_angle_deg: {receiver_angle_deg:.6f}"])
        for row in layout_data:
            writer.writerow(row)