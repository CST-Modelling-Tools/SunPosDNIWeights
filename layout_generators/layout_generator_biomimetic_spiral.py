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
        a0 = parameters["a0"]
        b = parameters["b"]
        delta = parameters["delta"]

        aperture_center = np.array([0.0, 0.0, self.receiver_height])
        layout_data = []

        angle = 0.0
        placed = 0
        max_iterations = 10000
        iteration = 0

        while placed < self.num_heliostats and iteration < max_iterations:
            r = a0 + b * angle
            x = r * math.cos(angle + delta)
            y = r * math.sin(angle + delta)
            z = 0.0

            if y < 0:
                angle += math.radians(1)
                iteration += 1
                continue

            candidate = np.array([x, y, z])
            too_close = any(
                math.sqrt((x - xj)**2 + (y - yj)**2) < 2 * self.bubble_radius
                for _, xj, yj, zj, _ in layout_data
            )

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

        if placed < self.num_heliostats:
            raise RuntimeError(f"Only placed {placed} heliostats out of {self.num_heliostats}.")

        directions = []
        for _, x, y, z, _ in layout_data:
            vec = aperture_center - np.array([x, y, z])
            vec[0] = 0
            if np.linalg.norm(vec) > 0:
                directions.append(vec / np.linalg.norm(vec))

        avg_direction = np.mean(directions, axis=0)
        receiver_angle_rad = math.acos(np.dot(avg_direction, [0, 1, 0]))
        if avg_direction[2] < 0:
            receiver_angle_rad = -receiver_angle_rad
        receiver_angle_deg = 180.0 - np.rad2deg(receiver_angle_rad)

        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([f"# receiver_height: {self.receiver_height}"])
            writer.writerow([f"# receiver_angle_deg: {receiver_angle_deg:.6f}"])
            for row in layout_data:
                writer.writerow(row)