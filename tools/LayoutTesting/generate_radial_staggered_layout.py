# File: generate_radial_staggered_layout.py
# -----------------------------------------
# Edit the parameters in the block below, then press "Run" in VS Code.

from pathlib import Path
import numpy as np
import math
import csv
from textwrap import dedent

# =========================
# Parameters (edit these)
# =========================
# Output file names
OUTPUT_CSV = Path("radial_staggered_layout_6500_90_round.csv")   # layout CSV to generate
OUTPUT_TNH = OUTPUT_CSV.with_suffix(".tnhpps")                    # Tonatiuh++ script to generate
EFFICIENCY_OUTPUT_CSV = Path("annual_efficiency_results.csv")     # results CSV written by Tonatiuh++

# Directions-with-weights CSV location (from /tools/LayoutTesting to parallel /projects/...)
DIRECTIONS_WITH_WEIGHTS_CSV = Path("../../projects/hyder_arizona/data/directions_with_weights_hyder_arizona.csv")

# Heliostat field parameters
NUM_HELIOSTATS = 6500
BUBBLE_RADIUS = 2.4         # m (half min center-to-center distance)
RECEIVER_HEIGHT = 90.0      # m (z of aiming point / receiver center)
MIN_TOWER_CLEARANCE = 9.0   # extra beyond nominal 3.0 m (so min distance = 3.0 + this)

# Field type and global orientation
NORTH_ONLY = True           # True => north/polar field; False => surround field
DELTA_DEG = 0.0             # global rotation (degrees)

# Spacing laws:
#   radial spacing:     d(r) = d0 + alpha * r
#   azimuthal spacing:  a(r) = a0 + gamma * r
D0 = 5.5
ALPHA = 0.010
A0 = 5.0
GAMMA = 0.014

# Tonatiuh++ scene defaults (used inside the generated .tnhpps)
MIRROR_WIDTH  = 4.06       # m
MIRROR_HEIGHT = 4.06       # m
RECEIVER_RADIUS_APERTURE = 2.5     # m (north-field planar circular receiver radius in x–z plane)
TOWER_SIDE = 4.0                    # m (square tower cross-section side)
RAYS = 5_000_000                    # rays per sun direction
SUN_AZIMUTH_DEG = 180
SUN_ELEVATION_DEG = 67
IRRADIANCE = 1000                   # W/m^2 used in efficiency loop
GRID_MARGIN = TOWER_SIDE + 2.5      # m

# Cylindrical receiver parameters (used when NORTH_ONLY == False)
RECEIVER_CYL_RADIUS = 5.0    # m
RECEIVER_CYL_HEIGHT = 12.0   # m# File: layout_generators/layout_generator_octagon_biomimetic_spiral.py

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
# =========================
# End of parameters
# =========================


class RadialStaggeredGenerator:
    """
    Parametric radial-staggered field generator.

    CSV:
      # receiver_height: H
      # receiver_angle_deg: A   (kept for compatibility; not used by these receivers)
      heliostat_id, x, y, z, slant_range
    """

    def __init__(
        self,
        num_heliostats: int,
        bubble_radius: float,
        receiver_height: float,
        min_tower_clearance: float = 3.0,
        north_only: bool = True,
    ):
        self.num_heliostats = int(num_heliostats)
        self.bubble_radius = float(bubble_radius)
        self.receiver_height = float(receiver_height)
        self.min_tower_clearance = float(min_tower_clearance)
        self.north_only = bool(north_only)

    def _radial_spacing(self, r: float, d0: float, alpha: float) -> float:
        d_param = d0 + alpha * r
        return max(d_param, 2.0 * self.bubble_radius)

    def _azimuthal_delta(self, r: float, a0: float, gamma: float) -> float:
        a_r = a0 + gamma * r
        dtheta_from_arc = a_r / max(r, 1e-9)
        ratio = min(1.0, self.bubble_radius / max(r, 1e-9))
        dtheta_bubble = 2.0 * math.asin(ratio)
        return max(dtheta_from_arc, dtheta_bubble)

    def generate_layout(self, output_file: Path, d0: float, alpha: float, a0: float, gamma: float, delta_rad: float):
        aperture_center = np.array([0.0, 0.0, self.receiver_height])

        # First usable radius (tower clearance + bubble safety)
        min_distance_to_tower = 3.0 + self.min_tower_clearance
        r = max(min_distance_to_tower, 2.0 * self.bubble_radius)

        # Azimuth bounds
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

            layout_data.append((heliostat_id, x, y, z, receiver_x, # File: layout_generators/layout_generator_octagon_biomimetic_spiral.py

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
                writer.writerow([heliostat_id, x, y, z, xa, ya, za, slant_range])receiver_y, receiver_z, None))
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
        if placed < self.num_heliostats:
            raise RuntimeError(
                f"Only placed {placed} heliostats out of {self.num_heliostats} "
                f"(rows tried: {row_index}, last radius: {r:.2f} m)."
            )

        # Keep angle header for compatibility (not used by the north planar/cylindrical receivers)
        receiver_angle_deg = 0.0

        # Write CSV
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([f"# receiver_height: {self.receiver_height}"])
            writer.writerow([f"# receiver_angle_deg: {receiver_angle_deg:.6f}"])
            for row in layout_data:
                writer.writerow(row)

        return receiver_angle_deg


def write_tonatiuh_script(script_path: Path, csv_path: Path, results_csv_path: Path, north_field: bool):
    """
    Emit a .tnhpps that:
      - reads CSV headers (# receiver_height, # receiver_angle_deg)
      - for north field: FLAT CIRCULAR receiver in the x–z plane, centered at aiming point.
                         Tower top at RECEIVER_Z - RECEIVER_RADIUS_APERTURE - 1.0
      - for surround field: CYLINDRICAL receiver centered at aiming point.
                            Tower top at RECEIVER_Z - 1.0
    """
    layout_csv_posix = csv_path.as_posix()
    results_csv_posix = results_csv_path.as_posix()
    dirs_weights_posix = DIRECTIONS_WITH_WEIGHTS_CSV.as_posix()

    # Build the full Tonatiuh++ script content
    tnh = dedent(f"""
    const DEGREE = Math.PI / 180;
    const MIRROR_WIDTH = {MIRROR_WIDTH};
    const MIRROR_HEIGHT = {MIRROR_HEIGHT};

    let RECEIVER_Z = 35.0;     // Will be read from file
    let RECEIVER_ANGLE = 0.0;  // Kept for CSV compatibility
    let V_REC = `0 0 ${{RECEIVER_Z}}`;

    const TOWER_SIDE = {TOWER_SIDE};
    const rays = {RAYS};
    const GRID_MARGIN = TOWER_SIDE + 2.5; // meters

    // Receiver geometry constants
    const RECEIVER_RADIUS_APERTURE = {RECEIVER_RADIUS_APERTURE}; // for north planar receiver
    const RECEIVER_CYL_RADIUS = {RECEIVER_CYL_RADIUS};           // for surround cylinder
    const RECEIVER_CYL_HEIGHT = {RECEIVER_CYL_HEIGHT};

    let minX = Infinity;
    let maxX = -Infinity;
    let minY = Infinity;
    let maxY = -Infinity;

    let nMax = 0;

    function createNode(parent, name) {{
        const node = parent.createNode(name);
        if (!node) throw new Error(`Failed to create node: ${{name}}`);
        return node;
    }}

    function insertShape(node, surfaceType, profileType) {{
        const shape = node.createShape();
        const surface = shape.insertSurface(surfaceType);
        const profile = shape.insertProfile(profileType);
        return {{ shape, surface, profile }};
    }}

    function applyMaterial(shape, parameters) {{
        const materialPart = shape.getPart("material");
        if (!materialPart) return;

        if (parameters.ambientColor) materialPart.setParameter("ambientColor", parameters.ambientColor);
        if (parameters.diffuseColor) materialPart.setParameter("diffuseColor", parameters.diffuseColor);
        if (parameters.specularColor) materialPart.setParameter("specularColor", parameters.specularColor);
        if (parameters.shininess) materialPart.setParameter("shininess", parameters.shininess);
    }}

    function makeHeliostat(parent, name, position, aiming, focus) {{
        const PYLON_LENGTH = 2.1;
        const heliostatNode = createNode(parent, name);
        heliostatNode.setParameter("translation", `${{position[0]}} ${{position[1]}} 0`);

        const tracker = heliostatNode.createTracker();
        const armature = tracker.insertArmature("two-axes");
        armature.setParameter("primaryShift", `0 0 ${{position[2] + PYLON_LENGTH}}`);
        armature.setParameter("primaryAxis", "0 0 1");
        armature.setParameter("primaryAngles", "-360 360");
        armature.setParameter("secondaryShift", "0 0 0");
        armature.setParameter("secondaryAxis", "1 0 0");
        armature.setParameter("secondaryAngles", "-90 90");
        armature.setParameter("facetShift", "0 0 0");
        armature.setParameter("facetNormal", "0 0 1");

        tracker.getPart("target").setParameter("aimingPoint", aiming);

        const facetNode = createNode(createNode(createNode(heliostatNode, "primary"), "secondary"), "facet");
        facetNode.setParameter("translation", "0 0 0");

        const facet = insertShape(facetNode, "Parabolic", "Box");
        facet.surface.setParameter("fX", focus);
        facet.surface.setParameter("fY", focus);
        facet.profile.setParameter("uSize", MIRROR_WIDTH);
        facet.profile.setParameter("vSize", MIRROR_HEIGHT);

        const material = facet.shape.insertMaterial("Specular");
        material.setParameter("reflectivity", "1.0");
        material.setParameter("slope", "0.002");

        applyMaterial(facet.shape, {{
            ambientColor: "0.65 0.72 0.79",
            diffuseColor: "0.05 0.05 0.05",
            specularColor: "0.3 0.25 0.2",
            shininess: "0.5"
        }});

        const pylonNode = createNode(heliostatNode, "pylon");
        pylonNode.setParameter("scale", "0.2 0.2 1");

        const pylon = insertShape(pylonNode, "Cylinder", "Rectangular");
        pylon.profile.setParameter("uMin", 0.0);
        pylon.profile.setParameter("uMax", "360d");
        pylon.profile.setParameter("vMin", 0.0);
        pylon.profile.setParameter("vMax", position[2] + PYLON_LENGTH - 0.2);

        pylon.shape.insertMaterial("Transparent");
        applyMaterial(pylon.shape, {{
            ambientColor: "0.5 0.5 0.5",
            diffuseColor: "0.3 0.3 0.3",
            specularColor: "0.2 0.2 0.2",
            shininess: "0.1"
        }});
    }}

    function generateHeliostatFieldFromCSV(parent, csvFilePath) {{
        const file = new DataObject();
        if (!file.read(csvFilePath)) throw new Error(`Failed to load: ${{csvFilePath}}`);

        // Parse receiver height and angle from the first two comment lines
        const line0 = file.array(0)[0];
        const line1 = file.array(1)[0];

        if (line0.startsWith("# receiver_height:")) {{
            RECEIVER_Z = parseFloat(line0.split(":")[1].trim());
        }} else {{
            throw new Error("Missing '# receiver_height:' line in CSV");
        }}

        if (line1 && line1.startsWith("# receiver_angle_deg:")) {{
            RECEIVER_ANGLE = parseFloat(line1.split(":")[1].trim());
        }} // angle kept only for compatibility

        V_REC = `0 0 ${{RECEIVER_Z}}`;

        parent.setName("HeliostatField");
        const nodeHeliostats = createNode(parent, "Heliostats");
        nMax = 0;
        for (let i = 2; i < file.rows(); i++) {{
            const row = file.array(i);
            if (row.length < 5) continue;
            const label = row[0];
            const x = parseFloat(row[1]);
            const y = parseFloat(row[2]);
            const z = parseFloat(row[3]);
            const focus = parseFloat(row[4]);
            if ([x, y, z, focus].some(Number.isNaN)) continue;

            // Update global min/max
            if (x < minX) minX = x;
            if (x > maxX) maxX = x;
            if (y < minY) minY = y;
            if (y > maxY) maxY = y;

            makeHeliostat(nodeHeliostats, label, [x, y, z], V_REC, focus);
            nMax++;
        }}

        print(`Heliostat field successfully generated with ${{nMax}} heliostats.`);
    }}

    // === Receivers ===
    function makePlanarReceiverNorth(parent) {{
        // Planar circular receiver in the x–z plane, centered at (0,0,RECEIVER_Z); normal is +Y
        parent.setName("ReceiverGroup");
        parent.setParameter("translation", `0 0 ${{RECEIVER_Z}}`);

        const inputAperture = createNode(parent, "InputAperture");
        inputAperture.setParameter("rotation", "0 0 1 180");

        const apertureX = createNode(inputAperture, "InputApertureRotationX");
        apertureX.setParameter("rotation", "1 0 0 90"); // Rotate plane to x–z (normal +y)

        const {{ shape, profile }} = insertShape(apertureX, "Planar", "Circular");
        profile.setParameter("rMax", `${{RECEIVER_RADIUS_APERTURE}}`);
        applyMaterial(shape, {{ ambientColor: "0.9 0.4 0.5" }});
    }}

    function makeCylindricalReceiver(parent, center, radius, height) {{
        // Cylinder centered at 'center'; axis along +Z; center of gravity = aiming point
        parent.setName("ReceiverGroup");
        parent.setParameter("translation", `${{center[0]}} ${{center[1]}} ${{center[2]}}`);
        const cylNode = createNode(parent, "ReceiverCylinder");
        const {{ shape, profile }} = insertShape(cylNode, "Cylinder", "Rectangular");
        profile.setParameter("uMin", 0.0);
        profile.setParameter("uMax", "360d");
        profile.setParameter("vMin", -height/2.0);
        profile.setParameter("vMax",  height/2.0);
        cylNode.setParameter("scale", `${{radius}} ${{radius}} 1`);
        applyMaterial(shape, {{ ambientColor: "0.9 0.4 0.5" }});
    }}

    // === Tower ===
    function makeTowerNorth(parent) {{
        // Top 1 m below the disk’s lower edge: RECEIVER_Z - RECEIVER_RADIUS_APERTURE - 1.0
        const TOWER_HEIGHT = Math.max(RECEIVER_Z - RECEIVER_RADIUS_APERTURE - 1.0, 1.0);
        const yOffset = -(TOWER_SIDE / 2.0);
        parent.setName("Tower");
        parent.setParameter("translation", `0 ${{yOffset}} ${{TOWER_HEIGHT / 2.0}}`);
        parent.setParameter("scale", `${{TOWER_SIDE}} ${{TOWER_SIDE}} ${{TOWER_HEIGHT}}`);
        insertShape(parent, "Cube", "Box");
    }}

    function makeTowerSurround(parent) {{
        // Top 1 m below receiver center height
        const TOWER_HEIGHT = Math.max(RECEIVER_Z - 1.0, 1.0);
        const yOffset = -(TOWER_SIDE / 2.0);
        parent.setName("Tower");
        parent.setParameter("translation", `0 ${{yOffset}} ${{TOWER_HEIGHT / 2.0}}`);
        parent.setParameter("scale", `${{TOWER_SIDE}} ${{TOWER_SIDE}} ${{TOWER_HEIGHT}}`);
        insertShape(parent, "Cube", "Box");
    }}

    try {{
        tn.Clear();

        const field = new NodeObject();
        generateHeliostatFieldFromCSV(field, "{layout_csv_posix}");
        tn.InsertScene(field);

        const receiver = new NodeObject();
        {"makePlanarReceiverNorth(receiver);" if north_field else f"makeCylindricalReceiver(receiver, [0, 0, RECEIVER_Z], {RECEIVER_CYL_RADIUS}, {RECEIVER_CYL_HEIGHT});"}
        tn.InsertScene(receiver);

        const tower = new NodeObject();
        {"makeTowerNorth(tower);" if north_field else "makeTowerSurround(tower);"}
        tn.InsertScene(tower);

        const scene = tn.getScene();
        scene.getPart("world.camera").setParameter("position", "0 0 100");
        scene.getPart("world.camera").setParameter("rotation", "0 -90");
        scene.getPart("world.sun").setParameter("shape", "Buie");

        const sunPos = scene.getPart("world.sun").getPart("position");
        sunPos.setParameter("azimuth", {SUN_AZIMUTH_DEG});
        sunPos.setParameter("elevation", {SUN_ELEVATION_DEG});

        const gridMinX = Math.floor(minX - {GRID_MARGIN});
        const gridMaxX = Math.ceil(maxX + {GRID_MARGIN});
        const gridMinY = Math.floor(minY - {GRID_MARGIN});
        const gridMaxY = Math.ceil(maxY + {GRID_MARGIN});

        const grid = scene.getPart("world.terrain").getPart("grid");
        grid.setParameter("min", `${{gridMinX}} ${{gridMinY}} 0`);
        grid.setParameter("max", `${{gridMaxX}} ${{gridMaxY}} 0`);

        if (rays > 0) {{
            const inputFile = new DataObject();
            if (!inputFile.read("{dirs_weights_posix}")) {{
                throw new Error("Missing input file with directions & weights");
            }}

            const outputFile = new DataObject();
            const outputPath = "{results_csv_posix}";

            // Mirror area computation
            const mirrorAreaEach = MIRROR_WIDTH * MIRROR_HEIGHT;
            const mirrorAreaTotal = mirrorAreaEach * nMax;

            // Copy the latitude and DNI header line from the input file
            const latitudeRow = inputFile.array(0);
            const latitudeLine = latitudeRow.join(", ");
            if (latitudeLine.startsWith("# latitude_deg:")) {{
                outputFile.addRow(latitudeLine);
            }} else {{
                throw new Error("Missing or invalid latitude/DNI header in input file.");
            }}

            // Write heliostat field parameters
            outputFile.addRow(`# heliostats: ${{nMax}}, mirror_area_each: ${{mirrorAreaEach.toFixed(6)}}, mirror_area_total: ${{mirrorAreaTotal.toFixed(6)}}`);

            // Add data header line
            outputFile.addRow("# azimuth_deg, elevation_deg, weight, efficiency");

            // Prepare ray tracing
            const irradiance = {IRRADIANCE};
            const maxInputPower = mirrorAreaTotal * irradiance;

            // Interception target
            const interceptPath = {"\"//Node/ReceiverGroup/InputAperture/InputApertureRotationX/Shape\"" if north_field else "\"//Node/ReceiverGroup/ReceiverCylinder/Shape\""};

            // Process sun directions and weights
            for (let i = 0; i < inputFile.rows(); i++) {{
                const row = inputFile.array(i);
                if (row.length < 3) continue;

                const azimuth = parseFloat(row[0]);
                const elevation = parseFloat(row[1]);
                const weight = parseFloat(row[2]);
                if ([azimuth, elevation, weight].some(Number.isNaN)) continue;

                sunPos.setParameter("azimuth", azimuth);
                sunPos.setParameter("elevation", elevation);
                sunPos.setParameter("irradiance", irradiance);

                const interceptedPower = tn.FindInterception(interceptPath, rays);
                const eta = interceptedPower / maxInputPower;

                outputFile.addRow(`${{azimuth}}, ${{elevation}}, ${{weight}}, ${{eta}}`);
            }}

            outputFile.write(outputPath);
        }}
    }} catch (error) {{
        print(`Simulation error: ${{error.message}}`);
    }}
    """).lstrip("\n")

    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text(tnh, encoding="utf-8")


def main():
    delta_rad = math.radians(DELTA_DEG)
    gen = RadialStaggeredGenerator(
        num_heliostats=NUM_HELIOSTATS,
        bubble_radius=BUBBLE_RADIUS,
        receiver_height=RECEIVER_HEIGHT,
        min_tower_clearance=MIN_TOWER_CLEARANCE,
        north_only=NORTH_ONLY,
    )
    receiver_angle_deg = gen.generate_layout(
        output_file=OUTPUT_CSV,
        d0=D0,
        alpha=ALPHA,
        a0=A0,
        gamma=GAMMA,
        delta_rad=delta_rad,
    )
    write_tonatiuh_script(
        script_path=OUTPUT_TNH,
        csv_path=OUTPUT_CSV,
        results_csv_path=EFFICIENCY_OUTPUT_CSV,
        north_field=NORTH_ONLY,
    )
    print(f"Wrote layout CSV: {OUTPUT_CSV.resolve()}")
    print(f"Wrote Tonatiuh++ script: {OUTPUT_TNH.resolve()}")
    print(f"Results CSV will be written by Tonatiuh++ to: {EFFICIENCY_OUTPUT_CSV.resolve()}")
    print(f"(CSV headers) receiver_height={RECEIVER_HEIGHT:.3f} m; receiver_angle_deg (compat) = {receiver_angle_deg:.3f}°")


if __name__ == "__main__":
    main()