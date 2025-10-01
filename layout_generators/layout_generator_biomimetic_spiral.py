# File: layout_generators/layout_generator_biomimetic_spiral.py

import numpy as np
from pathlib import Path
import math
import csv
from layout_generators.parametric_layout_generator import ParametricLayoutGenerator


class BiomimeticSpiralGenerator(ParametricLayoutGenerator):
    def __init__(self, num_heliostats: int, bubble_radius: float, receiver_height: float):
        self.num_heliostats = num_heliostats
        self.bubble_radius = bubble_radius
        self.receiver_height = receiver_height

    def generate_layout(self, output_file: Path, parameters: dict):
        # ✅ Core spiral parameters
        a0 = float(parameters["a0"])
        b = float(parameters["b"])
        delta = float(parameters.get("delta", 0.0))

        # ✅ Receiver geometry from parameters (instead of hidden config)
        receiver_radius = float(parameters.get("flat_receiver_radius", 1.0))
        receiver_tilt_deg = float(parameters.get("flat_receiver_tilt", 0.0))

        aperture_center = np.array([0.0, 0.0, self.receiver_height])
        layout_data = []

        angle = 0.0
        placed = 0
        max_iterations = 20000  # give more tries in case of collisions
        iteration = 0

        while placed < self.num_heliostats and iteration < max_iterations:
            r = a0 + b * angle
            x = r * math.cos(angle + delta)
            y = r * math.sin(angle + delta)
            z = 0.0

            # ❌ Old hard-coded north-only filter — now optional
            if parameters.get("north_only", True) and y < 0:
                angle += math.radians(1)
                iteration += 1
                continue

            # Enforce heliostat spacing
            too_close = any(
                math.hypot(x - xj, y - yj) < 2 * self.bubble_radius
                for _, xj, yj, _, _ in layout_data
            )
            if too_close:
                angle += math.radians(1)
                iteration += 1
                continue

            # Place heliostat
            slant_range = np.linalg.norm(aperture_center - np.array([x, y, z]))
            heliostat_id = f"H{placed+1:03d}"
            layout_data.append((heliostat_id, x, y, z, slant_range))
            placed += 1

            angle += math.radians(1)
            iteration += 1

        if placed < self.num_heliostats:
            raise RuntimeError(
                f"Only placed {placed} heliostats out of {self.num_heliostats} "
                f"(iterations: {iteration})."
            )

        # ✅ Compute average pointing direction → receiver tilt
        directions = []
        for _, x, y, z, _ in layout_data:
            vec = aperture_center - np.array([x, y, z])
            vec[0] = 0  # project onto Y–Z plane
            if np.linalg.norm(vec) > 0:
                directions.append(vec / np.linalg.norm(vec))

        avg_direction = np.mean(directions, axis=0)
        receiver_angle_rad = math.acos(np.clip(np.dot(avg_direction, [0, 1, 0]), -1.0, 1.0))
        if avg_direction[2] < 0:
            receiver_angle_rad = -receiver_angle_rad
        receiver_angle_deg = float(180.0 - np.rad2deg(receiver_angle_rad))

        # ✅ Save layout
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([f"# receiver_height: {self.receiver_height}"])
            writer.writerow([f"# receiver_radius: {receiver_radius:.6f}"])
            writer.writerow([f"# receiver_tilt_deg: {receiver_tilt_deg:.6f}"])
            writer.writerow([f"# receiver_angle_deg: {receiver_angle_deg:.6f}"])
            writer.writerow([f"# receiver_type: flat_circular"])
            for row in layout_data:
                writer.writerow(row)