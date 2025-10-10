# File: layout_generators/layout_generator_radial_staggered.py

import math
import csv
import numpy as np
from pathlib import Path
from layout_generators.parametric_layout_generator import ParametricLayoutGenerator


# =========================
# Helpers / small utilities
# =========================

def _lerp(a: float, b: float, t: float) -> float:
    t = max(0.0, min(1.0, float(t)))
    return a + (b - a) * t

def _min_angle_for_chord(r: float, d_min: float) -> float:
    """Minimum central angle (rad) so that chord >= d_min on radius r."""
    if r <= 0.0:
        return math.pi
    x = max(-1.0, min(1.0, d_min / (2.0 * r)))
    return 2.0 * math.asin(x)


# ================================================
# Noone-style correlations (spacing suggestions)
# ================================================

def _deltaR_noone(rc: float, receiver_height: float, HM: float, theta: float) -> float:
    """
    Row-to-row spacing correlation (Noone et al.).
    HM ≈ heliostat height (m). theta is solar elevation proxy: atan(H_rec / r).
    """
    cot_theta = 1.0 / max(1e-12, math.tan(theta))
    return HM * 0.5 * (1.14424 * cot_theta - 1.0935 + 3.0684 * theta - 1.1256 * theta**2)

def _deltaAzimuth_noone(r: float, receiver_height: float, HM: float, WM: float, theta: float, dR: float) -> float:
    """
    Same-row spacing correlation → returns Δφ in **degrees** (Noone et al.).
    We convert to radians where needed by callers.
    """
    # Guard tiny denominators
    part1 = 1.7491 + 0.6396 * theta + 0.02873 / max(1e-6, (theta - 0.04902))
    numerator = WM * (2.0 * r / max(1e-6, 2.0 * r - HM * dR))
    denominator = 1.0 - (HM * dR) / max(1e-6, 2.0 * r * receiver_height)
    denominator = max(denominator, 0.01)
    delta_azimuth_m = part1 * numerator / denominator   # [meters along arc]
    return math.degrees(delta_azimuth_m / max(1e-9, r)) # [degrees]


# =====================================
# Tiny spatial hash for spacing checks
# =====================================

class _SpatialHash:
    def __init__(self, cell: float):
        self.cell = float(cell)
        self.inv = 1.0 / self.cell
        self.grid = {}

    def _key(self, x: float, y: float):
        return int(math.floor(x * self.inv)), int(math.floor(y * self.inv))

    def add(self, p):
        k = self._key(p[0], p[1])
        self.grid.setdefault(k, []).append(p)

    def neighbors(self, p):
        i, j = self._key(p[0], p[1])
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                yield from self.grid.get((i + di, j + dj), [])


# ============================
# Count-based field generator
# ============================

class RadialStaggeredGenerator(ParametricLayoutGenerator):
    """
    Count-based radial-staggered field generator (symmetric about N–S; supports any β).

    Constructor inputs (kept for API compatibility):
      - num_heliostats     : total number to place (exact)
      - bubble_radius      : NOT USED for spacing (only mirror size is used here)
      - receiver_height    : tower/receiver height (m)
      - min_tower_clearance: inner exclusion beyond receiver radius (m)
      - north_only         : deprecated; β controls the sector (kept for API)
      - design_beta_deg, kr: unused in this implementation (no blocking guard)

    Parameters (dict) passed to generate_layout(..., parameters):
      REQUIRED:
        - flat_receiver_radius       : receiver aperture radius (m)

      ANGULAR EXTENT:
        - beta_deg                   : total sector angle in **degrees**, 0<β≤180 (default 180)
        - delta                      : global rotation in degrees (default 0; rotates the whole field)

      DENSITY / SHAPING (optimizable):
        - packing                    : 0..1 density slider (default 0.65)
        - inner_bias                 : 0..1 extra density near tower (default 0.50)

      OVERRIDES / ADVANCED (optional):
        - r_min                      : inner radius (m). If <=0 or missing → auto from packing & height
        - split_threshold            : split trigger (if missing → derived from packing)
        - radial_multiplier          : Noone ΔR scale (default from packing)
        - azimuth_multiplier         : Noone Δφ tightening (default from packing)
        - chord_diameter_factor      : safety factor × diag for same-row floor (default from packing)
        - rowrow_diameter_factor     : safety factor × diag for row-to-row floor (default from packing)
        - HM, WM                     : mirror height/width (m). Defaults 4.06 each.

    Output CSV (unchanged):
      # receiver_height: ...
      # receiver_angle_deg: 0
      # receiver_type: flat_circular
      # receiver_radius: ...
      heliostat_id, x, y, z, slant_to_receiver_center
    """

    def __init__(
        self,
        num_heliostats: int,
        bubble_radius: float,
        receiver_height: float,
        min_tower_clearance: float = 3.0,
        north_only: bool = False,          # deprecated: β controls the sector
        design_beta_deg: float = 25.0,     # unused here
        kr: float = 1.0                    # unused here
    ):
        self.num_heliostats = int(num_heliostats)
        self.rb = float(bubble_radius)               # kept for API; not used for spacing
        self.receiver_height = float(receiver_height)
        self.min_tower_clearance = float(min_tower_clearance)
        self.north_only = bool(north_only)           # not used to clip sector
        self.design_beta_deg = float(design_beta_deg)
        self.kr = float(kr)

    # --- equalized angles for a row ---
    @staticmethod
    def _angles_for_row(H: int, beta: float, parity: int) -> np.ndarray:
        """
        Equalized angles on [0, beta], measured from NORTH (0 at North).
          parity=0: include endpoints → 0, s, ..., beta
          parity=1: half-step → s/2, 3s/2, ..., beta-s/2
        """
        s = beta / (H - 1)
        if parity == 0:
            return s * np.arange(H)
        else:
            return (s / 2.0) + s * np.arange(H - 1)

    # --- full row points with ±x mirroring (symmetry about N–S axis) ---
    @staticmethod
    def _points_from_angles_unrotated(r: float, angs: np.ndarray) -> list[tuple[float, float]]:
        pts = []
        for ang in angs:
            x = r * math.sin(ang)
            y = r * math.cos(ang)
            if abs(x) <= 1e-12:
                pts.append((0.0, float(y)))
            else:
                pts.append(( float(x), float(y)))
                pts.append((-float(x), float(y)))
        return pts

    # --- contiguous symmetric subset for partial last row ---
    @staticmethod
    def _select_partial_contiguous(angs_full: np.ndarray, r: float, parity: int, M: int) -> list[tuple[float, float]]:
        """
        Last-row partial fill: choose a CONTIGUOUS, symmetric block around the N–S axis
        using the same Δφ as that row (no holes, still equalized).
        """
        pts = []
        if M <= 0:
            return pts

        if parity == 0:
            # parity=0 has axis at index 0 (North). Contiguous symmetric around axis.
            if M % 2 == 1:
                # odd M: axis + (M-1)//2 pairs at i=1..L
                y0 = r * math.cos(angs_full[0])
                pts.append((0.0, float(y0)))
                L = (M - 1) // 2
                for i in range(1, L + 1):
                    ang = float(angs_full[i])
                    x = r * math.sin(ang); y = r * math.cos(ang)
                    pts.append(( float(x), float(y)))
                    pts.append((-float(x), float(y)))
            else:
                # even M: M/2 pairs at i=1..L
                L = M // 2
                for i in range(1, L + 1):
                    if i >= len(angs_full): break
                    ang = float(angs_full[i])
                    x = r * math.sin(ang); y = r * math.cos(ang)
                    pts.append(( float(x), float(y)))
                    pts.append((-float(x), float(y)))
        else:
            # parity=1: no axis; must be even M. Take first k pairs (closest to axis).
            if M % 2 == 1:
                M -= 1
            k = M // 2
            for i in range(k):
                if i >= len(angs_full): break
                ang = float(angs_full[i])
                x = r * math.sin(ang); y = r * math.cos(ang)
                pts.append(( float(x), float(y)))
                pts.append((-float(x), float(y)))

        return pts

    # --- Euclidean spacing check against already placed heliostats ---
    @staticmethod
    def _row_is_safe(points_xy: list[tuple[float, float]], grid: _SpatialHash, d_min: float) -> bool:
        d2 = d_min * d_min
        for p in points_xy:
            for q in grid.neighbors(p):
                dx = p[0] - q[0]; dy = p[1] - q[1]
                if dx * dx + dy * dy < d2:
                    return False
        return True

    # ===================
    # Main entry point
    # ===================

    def generate_layout(self, output_file: Path, parameters: dict):
        """
        Generate layout and write CSV (receiver metadata + rows of heliostats).
        """
        # --- required receiver aperture ---
        receiver_radius = float(parameters["flat_receiver_radius"])

        # --- sector angle β and global rotation δ ---
        beta_deg = float(parameters.get("beta_deg", 180.0))
        if not (0.0 < beta_deg <= 180.0):
            raise ValueError("beta_deg must be in (0, 180].")
        beta = math.radians(beta_deg)
        delta_deg = float(parameters.get("delta", 0.0))
        delta = math.radians(delta_deg)
        cosd, sind = math.cos(delta), math.sin(delta)

        # --- mirror geometry (defaults to your 4.06 m square facet) ---
        HM = float(parameters.get("HM", parameters.get("mirror_height", 4.06)))
        WM = float(parameters.get("WM", parameters.get("mirror_width", 4.06)))
        diag = float(math.sqrt(HM * HM + WM * WM))

        # --- packing-driven defaults (can be overridden) ---
        packing = float(parameters.get("packing", 0.65))        # 0..1
        inner_bias = float(parameters.get("inner_bias", 0.50))  # 0..1

        # Safety floors (same-row chord & row-to-row) scaled by mirror diagonal
        chord_factor = float(parameters.get("chord_diameter_factor", _lerp(1.10, 1.04, packing)))
        rowrow_factor = float(parameters.get("rowrow_diameter_factor", _lerp(1.10, 1.04, packing)))
        d_min   = chord_factor * diag
        d_rowrow = rowrow_factor * diag

        # Noone multipliers and split threshold
        radial_multiplier  = float(parameters.get("radial_multiplier",  _lerp(1.05, 0.95, packing)))
        azimuth_multiplier = float(parameters.get("azimuth_multiplier", _lerp(1.05, 1.40, packing)))
        split_threshold = parameters.get("split_threshold", None)
        if split_threshold is None:
            split_threshold = _lerp(2.6, 1.7, packing)
        split_threshold = float(split_threshold)

        # r_min (auto if <= 0)
        r_min_user = float(parameters.get("r_min", 0.0))
        if r_min_user > 0.0:
            r_min = r_min_user
        else:
            a_h = _lerp(0.15, 0.08, packing)
            a_d = _lerp(8.0, 4.0,  packing)
            r_min = a_h * self.receiver_height + a_d * diag

        # Inner exclusion: receiver + clearance + one mirror half-diagonal (conservative)
        r_inner = receiver_radius + self.min_tower_clearance + 0.5 * diag

        # Start radius
        r = max(r_inner, r_min, 0.5 * diag)

        # Inner compression band (from inner_bias)
        k_inner = _lerp(0.20, 0.60, inner_bias)  # strength
        r_start = r
        r_end   = r + _lerp(20.0, 80.0, inner_bias)

        def inner_factor(rr: float) -> float:
            if r_end <= r_start:
                return 1.0
            t = max(0.0, min(1.0, (rr - r_start) / (r_end - r_start)))
            s = t * t * (3.0 - 2.0 * t)  # smoothstep
            return (1.0 - k_inner) + k_inner * s

        # State
        grid = _SpatialHash(cell=d_min)
        layout_rows = []
        placed_total = 0
        row_idx = 0
        max_rows = 5000

        # Parity-node staggering
        parity = 0
        H_current = None

        def capacity(H: int) -> int:
            """Full mirrored row capacity on [0, beta]."""
            return 2 * H - 2

        # Outward nudges to salvage dense rows
        nudge_step = float(parameters.get("nudge_step_diagonals", 0.2)) * diag
        nudge_max  = float(parameters.get("nudge_max_diagonals", 0.8))  * diag

        while placed_total < self.num_heliostats and row_idx < max_rows:
            theta_elev = math.atan2(self.receiver_height, r)

            # ΔR suggestion with shaping & safety floors
            dR_suggest = _deltaR_noone(r, self.receiver_height, HM, theta_elev) * radial_multiplier
            dR_suggest *= inner_factor(r)
            dR = max(dR_suggest, d_rowrow)

            # Δφ suggestion and equalization floor
            dphi_noone_deg = _deltaAzimuth_noone(r, self.receiver_height, HM, WM, theta_elev, dR)
            dphi_target = math.radians(dphi_noone_deg) / max(azimuth_multiplier, 1e-9)

            floor_same = _min_angle_for_chord(r, d_min)
            H_floor = max(2, int(math.floor(beta / max(floor_same, 1e-12))) + 1)

            if row_idx == 0:
                H_current = H_floor  # densest equalization permitted for first row
                parity = 0
            else:
                s_cur = beta / (H_current - 1)
                if dphi_target <= s_cur / max(split_threshold, 1e-9):
                    H_current = min(2 * (H_current - 1) + 1, H_floor)  # halve spacing
                else:
                    H_current = min(H_current, H_floor)

            P_full = capacity(H_current)
            remaining = self.num_heliostats - placed_total
            want_full_row = remaining >= P_full

            radii_to_try = [r]
            if nudge_step > 0 and nudge_max > 0:
                for k in range(1, int(math.floor(nudge_max / max(nudge_step, 1e-9))) + 1):
                    radii_to_try.append(r + k * nudge_step)

            placed_this_row = 0
            used_radius = r
            used_parity = parity
            used_H = H_current

            success = False
            for r_try in radii_to_try:
                angs = self._angles_for_row(H_current, beta, parity)

                if want_full_row:
                    cand_unrot = self._points_from_angles_unrotated(r_try, angs)
                    par_eff = parity
                else:
                    par_eff = parity
                    # if odd remainder and no axis (parity=1), switch last row to parity=0 for symmetry
                    if (par_eff == 1) and (remaining % 2 == 1):
                        par_eff = 0
                        angs = self._angles_for_row(H_current, beta, par_eff)
                    cand_unrot = self._select_partial_contiguous(angs, r_try, par_eff, remaining)

                # rotate whole field by delta
                cand_rot = [(x * cosd - y * sind, x * sind + y * cosd) for (x, y) in cand_unrot]

                if cand_rot and self._row_is_safe(cand_rot, grid, d_min):
                    for (xr, yr) in cand_rot:
                        slant = float(np.linalg.norm(np.array([xr, yr, 0.0], dtype=float) -
                                                     np.array([0.0, 0.0, self.receiver_height], dtype=float)))
                        heliostat_id = f"H{placed_total + 1:03d}"
                        layout_rows.append((heliostat_id, xr, yr, 0.0, slant))
                        grid.add((xr, yr))
                        placed_total += 1
                        placed_this_row += 1
                        if placed_total >= self.num_heliostats:
                            break
                    used_radius = r_try
                    used_parity = par_eff
                    success = True
                if success or placed_total >= self.num_heliostats:
                    break

            # If we failed, relax H (larger Δφ) and retry
            if not success:
                for H_try in range(H_current - 1, 1, -1):
                    angs = self._angles_for_row(H_try, beta, parity)
                    P_try = capacity(H_try)
                    full_ok = remaining >= P_try

                    for r_try in radii_to_try:
                        if full_ok:
                            cand_unrot = self._points_from_angles_unrotated(r_try, angs)
                            par_eff = parity
                        else:
                            par_eff = parity
                            if (par_eff == 1) and (remaining % 2 == 1):
                                par_eff = 0
                                angs = self._angles_for_row(H_try, beta, par_eff)
                            cand_unrot = self._select_partial_contiguous(angs, r_try, par_eff, remaining)

                        cand_rot = [(x * cosd - y * sind, x * sind + y * cosd) for (x, y) in cand_unrot]

                        if cand_rot and self._row_is_safe(cand_rot, grid, d_min):
                            for (xr, yr) in cand_rot:
                                slant = float(np.linalg.norm(np.array([xr, yr, 0.0], dtype=float) -
                                                             np.array([0.0, 0.0, self.receiver_height], dtype=float)))
                                heliostat_id = f"H{placed_total + 1:03d}"
                                layout_rows.append((heliostat_id, xr, yr, 0.0, slant))
                                grid.add((xr, yr))
                                placed_total += 1
                                placed_this_row += 1
                                if placed_total >= self.num_heliostats:
                                    break
                            used_radius = r_try
                            used_parity = par_eff
                            used_H = H_try
                            success = True
                        if success or placed_total >= self.num_heliostats:
                            break
                    if success or placed_total >= self.num_heliostats:
                        break

            # next row
            parity ^= 1
            r += max(dR, 1e-6)
            row_idx += 1

        if placed_total < self.num_heliostats:
            raise RuntimeError(
                f"Only placed {placed_total} heliostats out of {self.num_heliostats} "
                f"(rows tried: {row_idx}, last radius: {r:.2f} m)."
            )

        # --- write CSV (metadata + layout rows) ---
        receiver_angle_deg = 0.0
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow([f"# receiver_height: {self.receiver_height}"])
            w.writerow([f"# receiver_angle_deg: {receiver_angle_deg:.6f}"])
            w.writerow([f"# receiver_type: flat_circular"])
            w.writerow([f"# receiver_radius: {receiver_radius:.6f}"])
            for row in layout_rows:
                w.writerow(row)