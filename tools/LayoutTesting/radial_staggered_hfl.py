# hfl_count_based_overrides.py
# Count-based radial-staggered HFL with user-overrides for r_min and split_threshold.
# • β and (HM, WM) are user-provided (not optimized here).
# • Required knobs: receiver_height, N_total.
# • Convenience knobs: packing (0..1), inner_bias (0..1).
# • New critical knobs (optional overrides): r_min, split_threshold.
# • If an override is None, it's auto-mapped from packing.
# • Robust generator: parity-node rows, correct split rule, nudge-before-drop.
# • Last row: contiguous symmetric block about N–S with same Δφ.

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from dataclasses import dataclass, asdict
from typing import Tuple, List, Dict, Optional, Iterable

# ---------------- Noone correlations ----------------
def deltaR(rc: float, receiver_height: float, HM: float, theta: float) -> float:
    cot_theta = 1.0 / np.tan(theta)
    return HM * 0.5 * (1.14424 * cot_theta - 1.0935 + 3.0684 * theta - 1.1256 * theta**2)

def deltaAzimuth(r: float, receiver_height: float, HM: float, WM: float, theta: float, dR: float) -> float:
    part1 = 1.7491 + 0.6396 * theta + 0.02873 / (theta - 0.04902)
    numerator = WM * (2 * r / (2 * r - HM * dR))
    denominator = 1 - (HM * dR) / (2 * r * receiver_height)
    denominator = max(denominator, 0.01)
    delta_azimuth_m = part1 * numerator / denominator
    return np.degrees(delta_azimuth_m / r)  # degrees

# ---------------- Parameter structs ----------------
@dataclass
class LayoutParams:
    r_min: float
    receiver_height: float
    HM: float
    WM: float
    beta: float = np.pi
    radial_multiplier: float = 1.0
    azimuth_multiplier: float = 1.0

@dataclass
class SafetyParams:
    chord_diameter_factor: float = 1.08
    rowrow_diameter_factor: float = 1.08

@dataclass
class StaggerParams:
    split_threshold: float = 2.0     # split when dphi_noone <= s_current / split_threshold
    dense_first_row: bool = True

@dataclass
class InnerCompressionParams:
    enabled: bool = True
    strength: float = 0.50
    r_start: Optional[float] = None
    r_end: Optional[float] = None
    gamma: float = 1.0
    def factor(self, r: float) -> float:
        if not self.enabled or self.strength <= 0: return 1.0
        rs = self.r_start if self.r_start is not None else 0.0
        re = self.r_end   if self.r_end   is not None else rs
        if re <= rs: re = rs + 1e-6
        t = np.clip((r - rs)/(re - rs), 0.0, 1.0)
        s = t*t*(3 - 2*t)  # smoothstep
        if self.gamma != 1.0: s = s**self.gamma
        return (1.0 - self.strength) + self.strength*s

@dataclass
class NudgeParams:
    enable: bool = True
    step_diagonals: float = 0.2
    max_diagonals: float = 0.8

# ---------------- Spatial hash ----------------
class SpatialHash:
    def __init__(self, cell: float):
        self.cell = float(cell); self.inv = 1.0/self.cell
        self.grid: Dict[Tuple[int,int], List[Tuple[float,float]]] = {}
    def _key(self, x: float, y: float) -> Tuple[int,int]:
        return int(np.floor(x*self.inv)), int(np.floor(y*self.inv))
    def add(self, p: Tuple[float,float]) -> None:
        self.grid.setdefault(self._key(*p), []).append(p)
    def neighbors(self, p: Tuple[float,float]) -> Iterable[Tuple[float,float]]:
        i, j = self._key(*p)
        for di in (-1,0,1):
            for dj in (-1,0,1):
                yield from self.grid.get((i+di, j+dj), [])

# ---------------- Helpers ----------------
def min_angle_for_chord(r: float, d_min: float) -> float:
    if r <= 0: return np.pi
    x = np.clip(d_min/(2.0*r), -1.0, 1.0)
    return 2.0*np.arcsin(x)

# ---------------- Core generator ----------------
class RadialStaggeredHFL:
    """
    Count-based radial-staggered layout:
      • Parity-node rows (no axis holes):
          parity=0 → H nodes incl. endpoints (0..β), spacing s=β/(H−1)
          parity=1 → H−1 nodes, half-step (s/2 .. β−s/2)
        Row capacity (both parities): P = 2H − 2 (mirror about N–S).
      • Split when dφ_noone <= s_current / split_threshold → H_new = 2*(H_old−1)+1.
      • Place full rows until N_total is approached; last row is a CONTIGUOUS,
        symmetric block centered on N–S, with uniform Δφ of that row.
      • Nudge-before-drop; global Euclidean + ΔR floors.
    """
    def __init__(self, tower_position: Tuple[float,float]=(0.0,0.0)):
        self.tower_position = np.array(tower_position, float)
        self.heliostat_positions = np.empty((0,2))
        self.row_info: List[Dict] = []
        self.diagonal = None
        self.bubble_radius = None
        self.d_min = None
        self.d_rowrow = None
        self._last_params = {}

    # equalized angles for a row
    @staticmethod
    def _angles_for_row(H: int, beta: float, parity: int) -> np.ndarray:
        s = beta / (H - 1)
        return (s * np.arange(H)) if parity == 0 else ((s/2.0) + s * np.arange(H - 1))

    # full row points with ±x mirroring
    @staticmethod
    def _points_from_angles(r: float, angs: np.ndarray) -> List[Tuple[float,float]]:
        pts: List[Tuple[float,float]] = []
        for ang in angs:
            x = r*np.sin(ang); y = r*np.cos(ang)
            if abs(x) <= 1e-12:
                pts.append((0.0, float(y)))
            else:
                pts.append(( float(x), float(y)))
                pts.append((-float(x), float(y)))
        return pts

    # contiguous symmetric subset for partial last row
    @staticmethod
    def _select_partial_contiguous(full_angles: np.ndarray, r: float, parity: int, M: int) -> List[Tuple[float,float]]:
        pts: List[Tuple[float,float]] = []
        if M <= 0: return pts

        if parity == 0:
            # parity=0 has axis at index 0 (North). Contiguous symmetric around axis.
            if M % 2 == 1:
                # odd M: axis + (M-1)/2 pairs at i=1..L
                L = (M - 1) // 2
                # axis
                y0 = r*np.cos(full_angles[0]); pts.append((0.0, float(y0)))
                for i in range(1, L+1):
                    ang = full_angles[i]
                    x = r*np.sin(ang); y = r*np.cos(ang)
                    pts.append(( float(x), float(y)))
                    pts.append((-float(x), float(y)))
            else:
                # even M: M/2 pairs at i=1..L with L=M//2
                L = M // 2
                for i in range(1, L+1):
                    if i >= len(full_angles): break
                    ang = full_angles[i]
                    x = r*np.sin(ang); y = r*np.cos(ang)
                    pts.append(( float(x), float(y)))
                    pts.append((-float(x), float(y)))
        else:
            # parity=1: no axis; must be even M. Take first k pairs (closest to axis).
            if M % 2 == 1: M -= 1
            k = M // 2
            for i in range(k):
                if i >= len(full_angles): break
                ang = full_angles[i]
                x = r*np.sin(ang); y = r*np.cos(ang)
                pts.append(( float(x), float(y)))
                pts.append((-float(x), float(y)))

        return pts

    @staticmethod
    def _row_is_safe(points: List[Tuple[float,float]], index: SpatialHash, d_min: float) -> bool:
        d2 = d_min*d_min
        for p in points:
            for q in index.neighbors(p):
                dx = p[0]-q[0]; dy = p[1]-q[1]
                if dx*dx + dy*dy < d2:
                    return False
        return True

    # ---------------- Count-based generation ----------------
    def generate_layout_by_count(
        self,
        N_total: int,
        layout: LayoutParams,
        safety: SafetyParams = SafetyParams(),
        stagger: StaggerParams = StaggerParams(),
        inner: InnerCompressionParams = InnerCompressionParams(),
        nudge: NudgeParams = NudgeParams(),
        verbose: bool = False,
    ) -> np.ndarray:

        self._last_params = {
            "layout": asdict(layout),
            "safety": asdict(safety),
            "stagger": asdict(stagger),
            "inner": asdict(inner),
            "nudge": asdict(nudge),
            "N_total": N_total,
        }

        HM, WM = layout.HM, layout.WM
        self.diagonal = float(np.sqrt(HM**2 + WM**2))
        self.bubble_radius = 0.5*self.diagonal
        self.d_min = safety.chord_diameter_factor * self.diagonal
        self.d_rowrow = safety.rowrow_diameter_factor * self.diagonal

        index = SpatialHash(cell=self.d_min)
        self.row_info.clear()
        pts: List[Tuple[float,float]] = []

        r = float(layout.r_min)
        row_idx = 0
        beta = layout.beta
        H_current: Optional[int] = None
        parity = 0  # 0=endpoints row; 1=half-step row
        placed_total = 0

        def capacity(H: int) -> int:
            return 2*H - 2

        while placed_total < N_total and row_idx < 5000:
            theta = np.arctan(layout.receiver_height / r)

            # ΔR & compression
            dR_noone = deltaR(r, layout.receiver_height, HM, theta) * layout.radial_multiplier
            dR = max(dR_noone * inner.factor(r), self.d_rowrow)

            # Δφ suggestion & floors
            dphi_noone = np.radians(deltaAzimuth(r, layout.receiver_height, HM, WM, theta, dR)) \
                         / max(layout.azimuth_multiplier, 1e-9)
            floor_same = min_angle_for_chord(r, self.d_min)
            H_floor = max(2, int(np.floor(beta / max(floor_same, 1e-12))) + 1)

            if row_idx == 0:
                H_current = H_floor if stagger.dense_first_row else max(2, int(np.floor(beta / dphi_noone)) + 1)
                H_current = max(2, min(H_current, H_floor))
                parity = 0
            else:
                s_cur = beta / (H_current - 1)
                if dphi_noone <= s_cur / max(stagger.split_threshold, 1e-9):
                    H_current = min(2*(H_current - 1) + 1, H_floor)  # halve spacing
                else:
                    H_current = min(H_current, H_floor)

            P_full = capacity(H_current)
            remaining = N_total - placed_total
            full_row = remaining >= P_full

            placed = 0
            used_radius = r
            used_H = H_current
            used_parity = parity
            used_spacing = beta / (H_current - 1)

            # try radii (nudges outward) with either full or partial row
            radii_to_try = [r]
            if nudge.enable:
                step = nudge.step_diagonals * self.diagonal
                maxd = nudge.max_diagonals * self.diagonal
                for k in range(1, int(np.floor(maxd / max(step,1e-12))) + 1):
                    radii_to_try.append(r + k*step)

            ok = False
            for r_try in radii_to_try:
                angs = self._angles_for_row(H_current, beta, parity)
                if full_row:
                    cand = self._points_from_angles(r_try, angs)
                else:
                    par = parity
                    # If odd remainder and parity=1 (no axis available), switch last row to parity=0.
                    if par == 1 and (remaining % 2 == 1):
                        par = 0
                        angs = self._angles_for_row(H_current, beta, par)
                    cand = self._select_partial_contiguous(angs, r_try, par, remaining)

                if self._row_is_safe(cand, index, self.d_min):
                    for p in cand: index.add(p); pts.append(p)
                    placed = len(cand)
                    used_radius = r_try
                    used_parity = parity if full_row else par
                    ok = True
                    break

            # If we failed, relax H (larger Δφ) and retry
            if not ok:
                for H_try in range(H_current-1, 1, -1):
                    s_try = beta / (H_try - 1)
                    angs_try = self._angles_for_row(H_try, beta, parity)
                    P_try = capacity(H_try)
                    full_ok = remaining >= P_try
                    for r_try in radii_to_try:
                        if full_ok:
                            cand = self._points_from_angles(r_try, angs_try)
                        else:
                            par = parity
                            if par == 1 and (remaining % 2 == 1):
                                par = 0
                                angs_try = self._angles_for_row(H_try, beta, par)
                            cand = self._select_partial_contiguous(angs_try, r_try, par, remaining)
                        if self._row_is_safe(cand, index, self.d_min):
                            for p in cand: index.add(p); pts.append(p)
                            placed = len(cand)
                            used_radius = r_try
                            used_H = H_try
                            used_spacing = s_try
                            used_parity = par if not full_ok else parity
                            ok = True
                            break
                    if ok: break

            # Record & advance
            self.row_info.append(dict(
                row=row_idx, r=used_radius, H=used_H, parity=used_parity,
                spacing_deg=np.degrees(used_spacing), placed=placed,
                full_row=full_row and placed==P_full
            ))
            if verbose:
                kind = "full" if (full_row and placed==P_full) else "partial"
                print(f"Row {row_idx:02d}: r={used_radius:7.2f} m, H={used_H:4d}, "
                      f"s={np.degrees(used_spacing):6.2f}°, parity={'endpts' if used_parity==0 else 'half'}, "
                      f"placed={placed} ({kind}), remaining={N_total-placed_total-placed}")

            placed_total += placed
            parity ^= 1
            r += max(dR, 1e-6)
            row_idx += 1

        self.heliostat_positions = np.array(pts, float) + self.tower_position
        return self.heliostat_positions

    # ---------------- Plot with row circles + movable params box ----------------
    def plot_layout_with_rows(
        self,
        heliostat_size: float = 16,
        tower_size: float = 90,
        show_grid: bool = True,
        show_quadrants: bool = True,
        show_row_circles: bool = False,
        show_protection_bubbles: bool = True,
        figsize: Tuple[float, float] = (14, 12),
        title: str = "Radial Staggered HFL (count-based)",
        show_params: bool = True,
        params_loc: str = "ne",          # 'nw'|'ne'|'sw'|'se'
        params_alpha: float = 0.92,
        params_fontsize: float = 9.0,
        params_compact: bool = False,
    ):
        if self.heliostat_positions.size == 0:
            raise ValueError("Run generate_layout_by_count() first.")
        fig, ax = plt.subplots(figsize=figsize)

        if show_protection_bubbles:
            for p in self.heliostat_positions:
                ax.add_patch(Circle(p, self.bubble_radius, fill=False,
                                    linestyle='-', color='red', alpha=0.35, linewidth=0.8))
        if show_row_circles:
            radii = np.unique(np.round(np.linalg.norm(self.heliostat_positions - self.tower_position, axis=1), 6))
            for r in radii:
                ax.add_patch(Circle(self.tower_position, r, fill=False,
                                    linestyle='--', color='purple', alpha=0.25, linewidth=0.9))

        pos = self.heliostat_positions
        west = pos[:,0] >  1e-9; east = pos[:,0] < -1e-9; axis = ~(west | east)
        ax.scatter(pos[west,0], pos[west,1], c='skyblue',   s=heliostat_size, edgecolors='navy',    linewidth=0.35, label='West')
        ax.scatter(pos[east,0], pos[east,1], c='lightcoral', s=heliostat_size, edgecolors='darkred', linewidth=0.35, label='East')
        if np.any(axis):
            ax.scatter(pos[axis,0], pos[axis,1], c='yellow', s=heliostat_size, edgecolors='orange', linewidth=0.6, label='N-S Axis')

        ax.scatter(self.tower_position[0], self.tower_position[1],
                   c='red', s=tower_size, marker='s', edgecolors='darkred', linewidth=2, label='Tower')
        if show_quadrants:
            ax.axvline(self.tower_position[0], color='green',  linestyle='--', alpha=0.5, linewidth=1.5, label='N-S Axis')
            ax.axhline(self.tower_position[1], color='orange', linestyle='--', alpha=0.5, linewidth=1.5, label='E-W Axis')

        ax.set_xlabel('East ← X Position (m) → West', fontsize=12, fontweight='bold')
        ax.set_ylabel('South ← Y Position (m) → North', fontsize=12, fontweight='bold')
        beta_used = self._last_params.get("layout", {}).get("beta", np.pi)
        ax.set_title(f"{title} (β = {np.degrees(beta_used):.0f}°)", fontsize=14, fontweight='bold', pad=16)
        ax.legend(loc='upper right', fontsize=9, framealpha=0.9)
        ax.set_aspect('equal'); ax.grid(show_grid, alpha=0.3, linestyle='-', linewidth=0.5)

        # Stats box
        d = np.linalg.norm(pos - self.tower_position, axis=1)
        stats_text = "\n".join([
            f"Total Heliostats: {len(pos)}",
            f"Number of Rows: {len(self.row_info)}",
            f"Avg Distance: {np.mean(d):.1f} m",
            f"Min Distance: {np.min(d):.1f} m",
            f"Max Distance: {np.max(d):.1f} m",
            f"Bubble Radius: {self.bubble_radius:.2f} m",
        ])
        ax.text(0.015, 0.985, stats_text, transform=ax.transAxes,
                fontsize=9.5, va='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.90))

        # Params box (movable/compact)
        if show_params and self._last_params:
            lp = self._last_params["layout"]; sp = self._last_params["safety"]
            sg = self._last_params["stagger"]; ip = self._last_params["inner"]; npz = self._last_params["nudge"]
            Nt = self._last_params.get("N_total")
            def f(v): return "None" if v is None else (f"{v:.2f}" if isinstance(v, float) else str(v))

            if params_compact:
                lines = [
                    "Params:",
                    f" N={Nt}; r_min={f(lp['r_min'])} m; Hrec={f(lp['receiver_height'])} m; β={np.degrees(lp['beta']):.0f}°; "
                    f"HM×WM={f(lp['HM'])}×{f(lp['WM'])} m; ΔR×={f(lp['radial_multiplier'])}; Δφ×={f(lp['azimuth_multiplier'])}; "
                    f"chord×={f(sp['chord_diameter_factor'])}; rowrow×={f(sp['rowrow_diameter_factor'])}; "
                    f"split_thr={f(sg['split_threshold'])}; dense_first={sg['dense_first_row']}; "
                    f"inner_on={ip['enabled']}; k={f(ip['strength'])}; r*=[{f(ip['r_start'])},{f(ip['r_end'])}] m; γ={f(ip['gamma'])}; "
                    f"nudge_on={npz['enable']}; step={f(npz['step_diagonals'])}×diag; max={f(npz['max_diagonals'])}×diag"
                ]
            else:
                lines = [
                    "Params:",
                    f" N_total={Nt}",
                    f" r_min={f(lp['r_min'])} m, H_rec={f(lp['receiver_height'])} m, β={np.degrees(lp['beta']):.0f}°",
                    f" HM×WM={f(lp['HM'])}×{f(lp['WM'])} m",
                    f" ΔR×={f(lp['radial_multiplier'])}, Δφ×={f(lp['azimuth_multiplier'])}",
                    f" chord×diag={f(sp['chord_diameter_factor'])}, rowrow×diag={f(sp['rowrow_diameter_factor'])}",
                    f" split_thr={f(sg['split_threshold'])}, dense_first={sg['dense_first_row']}",
                    f" inner_on={ip['enabled']}, strength={f(ip['strength'])}, r*=[{f(ip['r_start'])},{f(ip['r_end'])}] m, γ={f(ip['gamma'])}",
                    f" nudge_on={npz['enable']}, step={f(npz['step_diagonals'])}×diag, max={f(npz['max_diagonals'])}×diag",
                ]

            corners = {
                "nw": (0.015, 0.985, "left",  "top"),
                "ne": (0.985, 0.985, "right", "top"),
                "sw": (0.015, 0.015, "left",  "bottom"),
                "se": (0.985, 0.015, "right", "bottom"),
            }
            x, y, ha, va = corners.get(params_loc.lower(), corners["ne"])
            ax.text(x, y, "\n".join(lines), transform=ax.transAxes,
                    fontsize=params_fontsize, ha=ha, va=va,
                    bbox=dict(boxstyle='round', facecolor='lavender', alpha=params_alpha))

        plt.tight_layout()
        return fig, ax

# ---------------- Mapping (adds r_min & split_threshold overrides) ----------------
def lerp(a, b, t):  # linear interpolation
    return a + (b - a) * float(np.clip(t, 0.0, 1.0))

def map_knobs_to_params(
    HM: float, WM: float, beta_deg: float,
    receiver_height: float,
    N_total: int,
    packing: float,        # 0..1
    inner_bias: float,     # 0..1
    r_min: Optional[float] = None,           # ← OVERRIDE if not None
    split_threshold: Optional[float] = None  # ← OVERRIDE if not None
):
    diag = float(np.sqrt(HM**2 + WM**2))

    # r_min: from override or from packing+tower
    if r_min is None:
        a_h = lerp(0.15, 0.08, packing)
        a_d = lerp(8.0, 4.0, packing)
        r_min_val = a_h * receiver_height + a_d * diag
    else:
        r_min_val = float(r_min)

    # safety floors & Noone multipliers from packing
    chord_factor = lerp(1.10, 1.04, packing)
    rowrow_factor = lerp(1.10, 1.04, packing)
    radial_mult  = lerp(1.05, 0.95, packing)
    azim_mult    = lerp(1.05, 1.40, packing)

    # split threshold: override or from packing (higher packing → earlier split)
    split_thr_val = float(split_threshold) if split_threshold is not None else lerp(2.6, 1.7, packing)

    # inner compression from inner_bias
    inner_strength = lerp(0.20, 0.60, inner_bias)
    inner_rstart   = r_min_val
    inner_rend     = r_min_val + lerp(20.0, 80.0, inner_bias)
    inner_gamma    = 1.0

    layout  = LayoutParams(
        r_min=r_min_val, receiver_height=receiver_height, HM=HM, WM=WM,
        beta=np.radians(beta_deg), radial_multiplier=radial_mult, azimuth_multiplier=azim_mult
    )
    safety  = SafetyParams(chord_diameter_factor=chord_factor, rowrow_diameter_factor=rowrow_factor)
    stagger = StaggerParams(split_threshold=split_thr_val, dense_first_row=True)
    inner   = InnerCompressionParams(enabled=True, strength=inner_strength, r_start=inner_rstart,
                                     r_end=inner_rend, gamma=inner_gamma)
    nudge   = NudgeParams(enable=True, step_diagonals=0.2, max_diagonals=0.8)
    return layout, safety, stagger, inner, nudge

# ---------------- Convenience API ----------------
def generate_layout_simple_count(
    HM: float, WM: float, beta_deg: float,
    receiver_height: float,
    N_total: int,
    packing: float,
    inner_bias: float,
    r_min: Optional[float] = None,
    split_threshold: Optional[float] = None,
    tower_position: Tuple[float,float]=(0.0,0.0),
    verbose: bool = False,
):
    field = RadialStaggeredHFL(tower_position=tower_position)
    layout, safety, stagger, inner, nudge = map_knobs_to_params(
        HM, WM, beta_deg, receiver_height, N_total, packing, inner_bias,
        r_min=r_min, split_threshold=split_threshold
    )
    positions = field.generate_layout_by_count(
        N_total, layout, safety, stagger, inner, nudge, verbose=verbose
    )
    return field, positions

# ---------------- Example ----------------
if __name__ == "__main__":
    # User-given (not counted as knobs)
    HM = WM = 4.06
    beta_deg = 90.0

    # Minimal knobs + new critical overrides
    receiver_height = 90.0
    N_total = 600
    packing = 1
    inner_bias = 1
    r_min_override = 15.0           # e.g., 22.0 to force 22 m; or None to auto
    split_thr_override = 2.2        # e.g., force earlier split

    field, pos = generate_layout_simple_count(
        HM, WM, beta_deg,
        receiver_height=receiver_height,
        N_total=N_total,
        packing=packing,
        inner_bias=inner_bias,
        r_min=r_min_override,
        split_threshold=split_thr_override,
        tower_position=(0.0, 0.0),
        verbose=False
    )
    print(f"Generated {len(pos)} heliostat positions.")

    fig, _ = field.plot_layout_with_rows(
        heliostat_size=16,
        show_row_circles=False,
        show_protection_bubbles=True,
        title="Radial Staggered HFL (count-based, r_min & split_thr overrides)",
        show_params=True,
        params_loc="sw", params_alpha=0.92, params_fontsize=9.0, params_compact=False
    )
    plt.savefig("heliostat_field_count_based_overrides.png", dpi=300, bbox_inches="tight")
    plt.show()