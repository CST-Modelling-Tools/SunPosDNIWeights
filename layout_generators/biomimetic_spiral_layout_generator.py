import os
from pathlib import Path
import numpy as np
import math
import csv

class BiomimeticSpiralLayoutGenerator:
    def __init__(self, a=5.5, b=1.3, e=0.045, tower_height=35.0):
        self.a = a
        self.b = b
        self.e = e  # unused in this version but kept for future variants
        self.tower_height = tower_height
        self.receiver_center = np.array([0.0, 0.0, tower_height])

    def generate_layout(self, num_heliostats, output_file: Path):
        DEGREE = np.pi / 180
        heliostats = []

        for i in range(num_heliostats):
            theta = i * (137.508 * DEGREE)
            r = self.a + self.b * i
            x = r * np.cos(theta)
            y = r * np.sin(theta)
            z = 1.0
            heliostats.append((x, y, z))

        sum_directions_yz = np.zeros(2)
        for x, y, z in heliostats:
            vec = self.receiver_center - np.array([x, y, z])
            proj_yz = np.array([vec[1], vec[2]])
            proj_yz_norm = proj_yz / np.linalg.norm(proj_yz)
            sum_directions_yz += proj_yz_norm

        avg_direction_yz = sum_directions_yz / np.linalg.norm(sum_directions_yz)
        receiver_angle_rad = math.atan2(avg_direction_yz[1], avg_direction_yz[0])
        receiver_angle_deg = np.degrees(receiver_angle_rad)

        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([f"# receiver_height: {self.tower_height:.1f}"])
            writer.writerow([f"# receiver_angle_deg: {receiver_angle_deg:.6f}"])
            writer.writerow(["heliostat_id", "xc", "yc", "zc", "fl"])

            for idx, (x, y, z) in enumerate(heliostats, start=1):
                row_id = f"H{idx:03}"
                fl = np.linalg.norm(self.receiver_center - np.array([x, y, z]))
                writer.writerow([row_id, f"{x:.6f}", f"{y:.6f}", f"{z:.6f}", f"{fl:.6f}"])