# File: layout_generators/layout_generator_octagon_biomimetic_spiral.py

import numpy as np
from pathlib import Path
import math
import csv
from layout_generators.parametric_layout_generator import ParametricLayoutGenerator

class OctagonBiomimeticSpiralGenerator(ParametricLayoutGenerator):
    def __init__(self, num_heliostats: int, bubble_radius: float, receiver_height: float, receiver_radial_distance: float):
        self.num_heliostats = num_heliostats
        self.bubble_radius = bubble_radius
        self.receiver_height = receiver_height
        self.receiver_radial_distance = receiver_radial_distance

    def generate_layout(self, output_file: Path, parameters: dict):
        a0 = parameters["a0"]
        b = parameters["b"]
        delta = parameters["delta"]

        layout_data = []
        heliostat_sectors = [[] for _ in range(8)]

        receiver_angles_deg = [i * 45.0 for i in range(8)]
        receiver_positions = [
            (
                self.receiver_radial_distance * math.cos(math.radians(angle)),
                self.receiver_radial_distance * math.sin(math.radians(angle)),
                self.receiver_height
            )
            for angle in receiver_angles_deg
        ]

        angle = 0.0
        placed = 0
        max_iterations = 20000
        iteration = 0

        while placed < self.num_heliostats and iteration < max_iterations:
            r = a0 + b * angle
            x = r * math.cos(angle + delta)
            y = r * math.sin(angle + delta)
            z = 0.0

            candidate = np.array([x, y, z])
            too_close = any(
                math.sqrt((x - xj)**2 + (y - yj)**2) < 2 * self.bubble_radius
                for _, xj, yj, zj, _, _, _, _ in layout_data
            )

            if too_close:
                angle += math.radians(1)
                iteration += 1
                continue

            heliostat_id = f"H{placed+1:03d}"

            azimuth = math.degrees(math.atan2(y, x)) % 360
            sector_index = int(azimuth // 45) % 8

            receiver_x, receiver_y, receiver_z = receiver_positions[sector_index]

            layout_data.append((heliostat_id, x, y, z, receiver_x, receiver_y, receiver_z, None))
            heliostat_sectors[sector_index].append((x, y, z))

            placed += 1
            angle += math.radians(1)
            iteration += 1

        if placed < self.num_heliostats:
            raise RuntimeError(f"Only placed {placed} heliostats out of {self.num_heliostats}.")

        receiver_tilt_angles = []

        for sector_index, heliostats in enumerate(heliostat_sectors):
            receiver_x, receiver_y, receiver_z = receiver_positions[sector_index]
            receiver_pos = np.array([receiver_x, receiver_y, receiver_z])
            sector_direction = np.array([math.cos(math.radians(receiver_angles_deg[sector_index])), math.sin(math.radians(receiver_angles_deg[sector_index])), 0])

            projections = []
            for hx, hy, hz in heliostats:
                vec = receiver_pos - np.array([hx, hy, hz])
                parallel_component = np.dot(vec, sector_direction) * sector_direction
                vertical_plane_vec = np.array([0.0, parallel_component[1], vec[2]])
                if np.linalg.norm(vertical_plane_vec) > 0:
                    projections.append(vertical_plane_vec / np.linalg.norm(vertical_plane_vec))

            if len(projections) == 0:
                tilt_angle_deg = 0.0
            else:
                avg_vec = np.mean(projections, axis=0)
                tilt_angle_rad = math.atan2(avg_vec[2], avg_vec[1])
                tilt_angle_deg = 180.0 - math.degrees(tilt_angle_rad)

            receiver_tilt_angles.append(tilt_angle_deg)

        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([f"# receiver_height: {self.receiver_height}"])
            writer.writerow([f"# receiver_radial_distance_to_z_axis: {self.receiver_radial_distance}"])
            writer.writerow(["# receiver_angles_deg: " + ", ".join(f"{angle:.6f}" for angle in receiver_tilt_angles)])

            for heliostat_id, x, y, z, xa, ya, za, _ in layout_data:
                slant_range = np.linalg.norm(np.array([xa, ya, za]) - np.array([x, y, z]))
                writer.writerow([heliostat_id, x, y, z, xa, ya, za, slant_range])