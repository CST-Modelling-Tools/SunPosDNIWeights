# File: layout_generators/layout_generator_radial_staggered.py

import math
import csv
import numpy as np
from pathlib import Path
from layout_generators.parametric_layout_generator import ParametricLayoutGenerator

class RadialStaggeredGenerator(ParametricLayoutGenerator):
    def __init__(self, num_heliostats: int, bubble_radius: float, receiver_height: float,
                 min_tower_clearance: float = 3.0, north_only: bool = True):
        self.num_heliostats = num_heliostats
        self.bubble_radius = bubble_radius
        self.receiver_height = receiver_height
        self.min_tower_clearance = min_tower_clearance
        self.north_only = north_only

    def _radial_spacing(self, r: float, d0: float, alpha: float) -> float:
        d = d0 + alpha * r
        return max(d, 2.0 * self.bubble_radius)

    def _azimuthal_delta(self, r: float, a0: float, gamma: float) -> float:
        a = a0 + gamma * r
        dtheta_from_arc = a / max(r, 1e-9)
        ratio = min(1.0, self.bubble_radius / max(r, 1e-9))
        dtheta_bubble = 2.0 * math.asin(ratio)
        return max(dtheta_from_arc, dtheta_bubble)

    def generate_layout(self, output_file: Path, parameters: dict):
        d0 = float(parameters["d0"])
        alpha = float(parameters["alpha"])
        a0 = float(parameters["a0"])
        gamma = float(parameters["gamma"])
        delta = float(parameters.get("delta", 0.0))

        # ✅ receiver_radius now comes from parameters instead of project_config
        receiver_radius = float(parameters["flat_receiver_radius"])

        delta_rad = math.radians(delta)
        aperture_center = np.array([0.0, 0.0, self.receiver_height])

        min_distance_to_tower = 3.0 + self.min_tower_clearance
        r = max(min_distance_to_tower, 2.0 * self.bubble_radius)

        if self.north_only:
            theta_lower, theta_upper = 0.0, math.pi
        else:
            theta_lower, theta_upper = 0.0, 2.0 * math.pi
        theta_span = theta_upper - theta_lower

        layout_data = []
        placed = 0
        row_index = 0
        max_rows = 10000
        max_radius = 1e6

        while placed < self.num_heliostats and row_index < max_rows and r < max_radius:
            dtheta = self._azimuthal_delta(r, a0, gamma)
            if not math.isfinite(dtheta) or dtheta <= 0:
                dtheta = theta_span

            n_theta = max(1, int(math.floor(theta_span / dtheta)))
            slip = 0.5 * dtheta if (row_index % 2 == 1) else 0.0
            theta0 = theta_lower + slip

            for j in range(n_theta):
                if placed >= self.num_heliostats:
                    break

                theta = theta0 + j * dtheta
                if theta >= theta_upper:
                    break

                theta_rot = theta + delta_rad
                x = r * math.cos(theta_rot)
                y = r * math.sin(theta_rot)
                z = 0.0

                if self.north_only and y < 0.0:
                    continue
                if math.hypot(x, y) < min_distance_to_tower:
                    continue

                too_close = any(
                    math.hypot(x - xj, y - yj) < 2.0 * self.bubble_radius
                    for _, xj, yj, _, _ in layout_data
                )
                if too_close:
                    continue

                heliostat_id = f"H{placed + 1:03d}"
                slant_range = float(np.linalg.norm(aperture_center - np.array([x, y, z])))
                layout_data.append((heliostat_id, x, y, z, slant_range))
                placed += 1

            r += self._radial_spacing(r, d0, alpha)
            row_index += 1

        if placed < self.num_heliostats:
            raise RuntimeError(
                f"Only placed {placed} heliostats out of {self.num_heliostats} "
                f"(rows tried: {row_index}, last radius: {r:.2f} m)."
            )

        receiver_angle_deg = 0.0

        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([f"# receiver_height: {self.receiver_height}"])
            writer.writerow([f"# receiver_angle_deg: {receiver_angle_deg:.6f}"])
            writer.writerow([f"# receiver_type: flat_circular"])
            writer.writerow([f"# receiver_radius: {receiver_radius:.6f}"])
            for row in layout_data:
                writer.writerow(row)