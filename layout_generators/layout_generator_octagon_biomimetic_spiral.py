# File: layout_generators/layout_generator_octagon_biomimetic_spiral.py

import numpy as np
from pathlib import Path
import math
import csv
from layout_generators.parametric_layout_generator import ParametricLayoutGenerator

class OctagonBiomimeticSpiralGenerator(ParametricLayoutGenerator):
    def __init__(self, num_heliostats: int, bubble_radius: float, receiver_height: float, receiver_radial_distance: float, min_tower_clearance: float = 3.0):
        self.num_heliostats = num_heliostats
        self.bubble_radius = bubble_radius
        self.receiver_height = receiver_height
        self.receiver_radial_distance = receiver_radial_distance
        self.min_tower_clearance = min_tower_clearance  # Minimum distance from heliostat to tower wall

    def generate_layout(self, output_file: Path, parameters: dict):
        a0 = parameters["a0"]
        b = parameters["b"]
        delta = parameters["delta"]

        layout_data = []
        heliostat_sectors = [[] for _ in range(8)]

        # Define sector borders correctly
        sector_borders = [(-22.5 + 360) % 360, 22.5, 67.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5, (360 + 22.5)]

        receiver_angles_deg = [0, 45, 90, 135, 180, 225, 270, 315]
        receiver_positions = [
            (
                self.receiver_radial_distance * math.cos(math.radians(angle)),
                self.receiver_radial_distance * math.sin(math.radians(angle)),
                self.receiver_height
            )
            for angle in receiver_angles_deg
        ]

        min_distance_to_tower = 3.0 + self.min_tower_clearance

        angle = 0.0
        placed = 0
        max_iterations = 50000
        iteration = 0

        while placed < self.num_heliostats and iteration < max_iterations:
            r = a0 + b * angle
            x = r * math.cos(angle + delta)
            y = r * math.sin(angle + delta)
            z = 0.0

            distance_to_tower = math.sqrt(x ** 2 + y ** 2)
            if distance_to_tower < min_distance_to_tower:
                angle += math.radians(1)
                iteration += 1
                continue

            candidate = np.array([x, y, z])
            too_close = any(
                math.sqrt((x - xj) ** 2 + (y - yj) ** 2) < 2 * self.bubble_radius
                for _, xj, yj, zj, _, _, _, _ in layout_data
            )

            if too_close:
                angle += math.radians(1)
                iteration += 1
                continue

            heliostat_id = f"H{placed + 1:03d}"

            azimuth = math.degrees(math.atan2(y, x)) % 360

            sector_index = None
            for idx in range(8):
                lower = sector_borders[idx] % 360
                upper = sector_borders[idx + 1] % 360

                if lower < upper:
                    if lower <= azimuth < upper:
                        sector_index = idx
                        break
                else:
                    if azimuth >= lower or azimuth < upper:
                        sector_index = idx
                        break

            if sector_index is None:
                angle += math.radians(1)
                iteration += 1
                continue

            receiver_x, receiver_y, receiver_z = receiver_positions[sector_index]

            layout_data.append((heliostat_id, x, y, z, receiver_x, receiver_y, receiver_z, None))
            heliostat_sectors[sector_index].append((x, y, z))

            placed += 1
            angle += math.radians(1)
            iteration += 1

        if placed < self.num_heliostats:
            raise RuntimeError(f"Only placed {placed} heliostats out of {self.num_heliostats}.")

        # Set all receiver tilt angles to -45 degrees (downwards, facing towards the heliostat field)
        receiver_tilt_angles = [-45.0 for _ in range(8)]

        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([f"# receiver_height: {self.receiver_height}"])
            writer.writerow([f"# receiver_radial_distance_to_z_axis: {self.receiver_radial_distance}"])
            writer.writerow(["# receiver_angles_deg: " + ", ".join(f"{angle:.6f}" for angle in receiver_tilt_angles)])

            for heliostat_id, x, y, z, xa, ya, za, _ in layout_data:
                slant_range = np.linalg.norm(np.array([xa, ya, za]) - np.array([x, y, z]))
                writer.writerow([heliostat_id, x, y, z, xa, ya, za, slant_range])