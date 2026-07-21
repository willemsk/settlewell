# Ground Settlement During Dewatering — Python Package + Notebook

A Python package (`bronbemaling`) with a Jupyter notebook (`example_analysis.ipynb`) demonstrating its usage. Calculates ground settlement at neighboring buildings caused by dewatering of a residential-scale construction pit.

**Target context**: Flanders, Belgium — residential basement excavation.  
**Language**: English with Dutch terms in parentheses (e.g., "Settlement (zetting)").  
**Package management**: `uv`  

---

## Project Structure

```
d:\repos\bronbemaling\
├── pyproject.toml
├── README.md
├── src/
│   └── bronbemaling/
│       ├── __init__.py          # Package exports
│       ├── models.py            # All dataclasses (input models)
│       ├── hydraulics.py        # Drawdown calculations (Thiem, Theis)
│       ├── settlement.py        # Terzaghi consolidation + settlement
│       ├── damage.py            # Burland/Wroth + SBR classification
│       ├── numerical.py         # 2D finite-difference groundwater solver
│       └── plotting.py          # All 7 visualization functions
└── notebooks/
    └── example_analysis.ipynb   # Full worked example with Flemish defaults
```

---

## Proposed Changes

### [NEW] `pyproject.toml`

```toml
[project]
name = "bronbemaling"
version = "0.1.0"
description = "Ground settlement calculation for dewatering of construction pits"
requires-python = ">=3.11"
dependencies = [
    "numpy>=1.24",
    "scipy>=1.10",
    "matplotlib>=3.7",
    "plotly>=5.15",
]

[project.optional-dependencies]
notebook = ["jupyter>=1.0", "ipykernel>=6.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

---

### [NEW] `src/bronbemaling/models.py`

All input data structures as frozen dataclasses. Every field has a type annotation, unit in the docstring, and a sensible default where appropriate.

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

class AquiferType(Enum):
    """Type of aquifer for hydraulic calculations."""
    CONFINED = "confined"       # Afgesloten watervoerend pakket
    UNCONFINED = "unconfined"   # Freatisch watervoerend pakket

class BuildingType(Enum):
    """Building construction type for damage classification."""
    MASONRY = "masonry"              # Metselwerk
    CONCRETE_FRAME = "concrete_frame" # Betonskelet

@dataclass
class SoilLayer:
    """A single soil layer with geotechnical properties.
    
    All properties in SI units. Each layer is horizontal and uniform.
    """
    name: str                    # e.g., "Klei" or "Zand"
    thickness: float             # [m] Layer thickness
    gamma: float                 # [kN/m³] Dry unit weight
    gamma_sat: float             # [kN/m³] Saturated unit weight
    k_h: float                   # [m/s] Horizontal hydraulic conductivity
    e0: float                    # [-] Initial void ratio
    Cc: float                    # [-] Compression index (virgin compression)
    Cr: float                    # [-] Recompression index (swelling/recompression)
    Eoed: float                  # [kPa] Oedometric (constrained) modulus
    Cv: float                    # [m²/s] Coefficient of consolidation
    OCR: float = 1.0            # [-] Overconsolidation ratio

@dataclass
class SoilProfile:
    """Multi-layer soil profile with groundwater level.
    
    Layers are ordered top-to-bottom. The first layer starts at ground surface (z=0).
    """
    layers: list[SoilLayer]
    gwl_mtaw: float              # [mTAW] Groundwater level in Belgian datum (Tweede Algemene Waterpassing)
    surface_level_mtaw: float    # [mTAW] Ground surface level in Belgian datum

    @property
    def gwl_depth(self) -> float:
        """[m] Depth of groundwater below surface (positive downward)."""
        return self.surface_level_mtaw - self.gwl_mtaw

    @property
    def total_depth(self) -> float:
        """[m] Total depth of all layers combined."""
        return sum(layer.thickness for layer in self.layers)

@dataclass
class Well:
    """A single dewatering well."""
    x: float                     # [m] X-coordinate in local system
    y: float                     # [m] Y-coordinate in local system
    Q: float                     # [m³/s] Pumping rate (positive = extraction)
    r_w: float = 0.075           # [m] Well radius (default 150mm diameter)
    screen_top_mtaw: float = 0.0 # [mTAW] Top of well screen
    screen_bottom_mtaw: float = 0.0  # [mTAW] Bottom of well screen

@dataclass
class ConstructionPit:
    """Rectangular construction pit geometry."""
    length: float                # [m] Pit length (x-direction)
    width: float                 # [m] Pit width (y-direction)
    depth: float                 # [m] Pit depth below surface
    center_x: float = 0.0       # [m] X-coordinate of pit center
    center_y: float = 0.0       # [m] Y-coordinate of pit center
    bottom_mtaw: float = 0.0    # [mTAW] Pit bottom level

@dataclass
class DewateringConfig:
    """Dewatering well configuration and hydraulic parameters."""
    wells: list[Well]
    target_drawdown_mtaw: float  # [mTAW] Target water level inside the pit
    original_gwl_mtaw: float     # [mTAW] Original (undisturbed) groundwater level
    pumping_duration_days: float # [days] Duration of pumping
    aquifer_type: AquiferType = AquiferType.UNCONFINED
    R: Optional[float] = None   # [m] Radius of influence (computed via Sichardt if None)
    T: Optional[float] = None   # [m²/s] Transmissivity (computed from layers if None)
    S: Optional[float] = None   # [-] Storativity (computed from layers if None)

    @property
    def target_drawdown(self) -> float:
        """[m] Total drawdown from original GWL to target level."""
        return self.original_gwl_mtaw - self.target_drawdown_mtaw

@dataclass
class Building:
    """Neighboring building to assess for settlement damage."""
    x: float                     # [m] X-coordinate of building center
    y: float                     # [m] Y-coordinate of building center
    length: float                # [m] Building length
    width: float                 # [m] Building width
    orientation_deg: float = 0.0 # [°] Rotation angle from x-axis
    foundation_depth: float = 0.6  # [m] Foundation depth below surface
    building_type: BuildingType = BuildingType.MASONRY

    def corner_coordinates(self) -> list[tuple[float, float]]:
        """Return (x, y) coordinates of the 4 building corners, accounting for orientation.
        
        Implementation:
        1. Define corners relative to center: (±length/2, ±width/2)
        2. Apply 2D rotation matrix using orientation_deg
        3. Translate to (self.x, self.y)
        
        Returns list of 4 tuples: [bottom-left, bottom-right, top-right, top-left]
        """
        ...

    def evaluation_points(self) -> list[tuple[float, float]]:
        """Return 5 evaluation points: 4 corners + center.
        
        Returns list of 5 tuples: [center, corner1, corner2, corner3, corner4]
        """
        ...
```

> [!IMPORTANT]
> **mTAW (Tweede Algemene Waterpassing)**: All absolute water levels and elevations use the Belgian national reference datum mTAW. Relative measurements (layer thicknesses, drawdown magnitudes) remain in meters. The `SoilProfile` provides a `gwl_depth` property that converts from mTAW to depth below surface for internal calculations.

---

### [NEW] `src/bronbemaling/hydraulics.py`

Drawdown computation via analytical solutions with well superposition.

```python
"""Hydraulic drawdown calculations for dewatering.

Supports both confined and unconfined aquifers, steady-state (Thiem/Dupuit)
and transient (Theis) solutions, with superposition for multiple wells.
"""
import numpy as np
from scipy.special import exp1
from .models import DewateringConfig, SoilProfile, AquiferType

GAMMA_W = 9.81  # [kN/m³] Unit weight of water


def compute_transmissivity(profile: SoilProfile, config: DewateringConfig) -> float:
    """Compute aquifer transmissivity T [m²/s] from soil layers.
    
    For UNCONFINED: T = sum(k_h_i * thickness_i) for all saturated layers above the aquifer base.
    For CONFINED: T = sum(k_h_i * thickness_i) for layers within the confined aquifer only
                  (layers below the confining clay layer).
    
    The confining layer is identified as the layer with the lowest k_h value.
    """
    ...


def compute_storativity(profile: SoilProfile, config: DewateringConfig) -> float:
    """Compute storativity S [-] from soil layers.
    
    For UNCONFINED: S = specific yield ≈ effective porosity ≈ e0 / (1 + e0) for the
                    aquifer layer (typically 0.1 – 0.3 for sand).
    For CONFINED: S = sum(m_v_i * gamma_w * thickness_i) where m_v = 1/Eoed
                  (typically 1e-4 to 1e-3).
    """
    ...


def compute_radius_of_influence(config: DewateringConfig, T: float) -> float:
    """Compute radius of influence R [m] using Sichardt's empirical formula.
    
    R = 3000 * s * sqrt(k)
    
    where:
        s = target_drawdown [m]
        k = representative hydraulic conductivity [m/s] (derived from T / aquifer_thickness)
    
    Typical values: 50–500m for sand, 10–50m for silty sand.
    Returns config.R if explicitly set, otherwise computes it.
    """
    ...


def thiem_drawdown_single_well(
    r: float | np.ndarray,
    Q: float,
    T: float,
    R: float,
    H0: float,
    aquifer_type: AquiferType,
) -> float | np.ndarray:
    """Steady-state drawdown at distance r from a single well.
    
    CONFINED (Thiem, 1906):
        s(r) = Q / (2π T) * ln(R / r)
    
    UNCONFINED (Dupuit, 1863):
        h²(r) = H0² - (Q / (π K)) * ln(R / r)
        s(r) = H0 - h(r)
        where H0 = initial saturated thickness, K = hydraulic conductivity
    
    Parameters:
        r: distance(s) from well [m]. Clipped to r_w minimum.
        Q: pumping rate [m³/s]
        T: transmissivity [m²/s]
        R: radius of influence [m]
        H0: initial saturated aquifer thickness [m]
        aquifer_type: CONFINED or UNCONFINED
    
    Returns:
        drawdown s [m] at distance r (always >= 0, clipped)
    """
    ...


def theis_drawdown_single_well(
    r: float | np.ndarray,
    t: float,
    Q: float,
    T: float,
    S: float,
) -> float | np.ndarray:
    """Transient drawdown at distance r and time t from a single well (Theis, 1935).
    
    s(r, t) = Q / (4π T) * W(u)
    
    where:
        u = r² S / (4 T t)
        W(u) = -Ei(-u) = exp1(u) from scipy (the Theis well function)
    
    For u < 1e-5 (large t or small r), use the Cooper-Jacob approximation:
        s ≈ Q / (4π T) * [ln(2.25 T t / (r² S))]
    
    Parameters:
        r: distance from well [m]
        t: time since pumping started [s]
        Q: pumping rate [m³/s]
        T: transmissivity [m²/s]
        S: storativity [-]
    
    Returns:
        drawdown s [m]
    """
    ...


def compute_drawdown_at_points(
    points: list[tuple[float, float]],
    config: DewateringConfig,
    profile: SoilProfile,
    time_s: float | None = None,
) -> np.ndarray:
    """Compute total drawdown at multiple (x,y) points using superposition.
    
    Algorithm:
    1. Compute T (transmissivity) from profile, or use config.T if set
    2. Compute R (radius of influence) from config, or via Sichardt
    3. For each point (x, y):
       a. For each well in config.wells:
          - Compute distance r = sqrt((x - well.x)² + (y - well.y)²)
          - Clip r to max(r, well.r_w) to avoid singularity
          - If time_s is None: use thiem_drawdown_single_well()
          - If time_s is given: use theis_drawdown_single_well()
       b. Sum drawdowns from all wells (superposition principle)
       c. Clip total drawdown to [0, config.target_drawdown] (physical limit)
    4. Return array of drawdowns, shape (len(points),)
    
    Parameters:
        points: list of (x, y) coordinates [m]
        config: dewatering configuration
        profile: soil profile (for computing T, S if not in config)
        time_s: time since pumping start [s]. None = steady-state (Thiem).
    
    Returns:
        np.ndarray of drawdown values [m] at each point
    """
    ...


def compute_drawdown_grid(
    x_range: tuple[float, float],
    y_range: tuple[float, float],
    nx: int,
    ny: int,
    config: DewateringConfig,
    profile: SoilProfile,
    time_s: float | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute drawdown on a regular 2D grid for contour plotting.
    
    Creates meshgrid from x_range and y_range, calls compute_drawdown_at_points
    for each grid node.
    
    Returns:
        (X, Y, S) where X, Y are meshgrid arrays and S is drawdown array,
        all shape (ny, nx).
    """
    ...
```

---

### [NEW] `src/bronbemaling/settlement.py`

Core settlement engine — layer-by-layer Terzaghi consolidation.

```python
"""Settlement calculation using Terzaghi 1D consolidation theory.

Computes effective stress changes from drawdown, then settlement per layer
using Cc/Cr (log-law) or Eoed (linear) approach.
"""
import numpy as np
from .models import SoilProfile, SoilLayer

GAMMA_W = 9.81  # [kN/m³]


def compute_initial_stress_profile(
    profile: SoilProfile,
    z_points: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute initial vertical effective stress profile with depth.
    
    Algorithm (layer by layer, top to bottom):
    1. Start at z=0 (ground surface), σ_v = 0, u = 0
    2. For each layer, at depth increments:
       a. Above GWL: σ_v += γ_dry * Δz,  u = 0
       b. Below GWL: σ_v += γ_sat * Δz,  u += γ_w * Δz
       c. σ'_v = σ_v - u
    3. Compute at layer midpoints if z_points is None,
       otherwise interpolate to requested z_points
    
    Parameters:
        profile: soil profile
        z_points: optional specific depths to evaluate [m], measured from surface
    
    Returns:
        (z, sigma_v_eff, sigma_v_total):
            z: depth array [m]
            sigma_v_eff: effective vertical stress [kPa]
            sigma_v_total: total vertical stress [kPa]
    """
    ...


def compute_stress_increase_from_drawdown(
    profile: SoilProfile,
    drawdown: float,
    z_points: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute increase in effective stress due to drawdown at each depth.
    
    The drawdown lowers the water table, converting submerged soil to dry soil,
    which increases effective stress.
    
    Algorithm:
    1. Original GWL depth = profile.gwl_depth
    2. New GWL depth = profile.gwl_depth + drawdown
    3. For each depth z:
       a. If z < original_gwl_depth: Δσ' = 0 (above original water table, no change)
       b. If original_gwl_depth <= z < new_gwl_depth: Δσ' = (γ_sat - γ_dry) * (z - original_gwl_depth) 
          Wait, this is not quite right. Actually:
          Δσ' = γ_w * drawdown for z >= new_gwl_depth (full drawdown effect)
          For original_gwl_depth <= z < new_gwl_depth: Δσ' = γ_w * (z - original_gwl_depth)
          (partial drawdown, linear increase)
       c. If z >= new_gwl_depth: Δσ' = γ_w * drawdown (full drawdown effect)
    
    More precisely, the change in pore water pressure is:
       Δu = -γ_w * min(drawdown, max(0, z - original_gwl_depth))
       (but capped: the pore pressure can't go below zero)
    So: Δσ' = -Δu = γ_w * min(drawdown, max(0, z - original_gwl_depth))
    
    Parameters:
        profile: soil profile
        drawdown: drawdown at this location [m]
        z_points: depths to evaluate at [m]
    
    Returns:
        (z, delta_sigma_eff): arrays of depth and effective stress increase [kPa]
    """
    ...


def compute_layer_settlement_cc_cr(
    layer: SoilLayer,
    sigma_v0_eff: float,
    delta_sigma_v: float,
) -> float:
    """Compute settlement of a single layer using Cc/Cr approach.
    
    Preconsolidation pressure: σ'_p = OCR * σ'_v0
    
    Case 1 — Fully overconsolidated (σ'_v0 + Δσ'_v ≤ σ'_p):
        Δs = (Cr / (1 + e0)) * H * log10((σ'_v0 + Δσ'_v) / σ'_v0)
    
    Case 2 — Fully normally consolidated (σ'_v0 ≥ σ'_p, i.e., OCR ≈ 1):
        Δs = (Cc / (1 + e0)) * H * log10((σ'_v0 + Δσ'_v) / σ'_v0)
    
    Case 3 — Transitional (σ'_v0 < σ'_p < σ'_v0 + Δσ'_v):
        Δs = (Cr / (1 + e0)) * H * log10(σ'_p / σ'_v0)
           + (Cc / (1 + e0)) * H * log10((σ'_v0 + Δσ'_v) / σ'_p)
    
    Parameters:
        layer: soil layer properties
        sigma_v0_eff: initial effective vertical stress at layer midpoint [kPa]
        delta_sigma_v: increase in effective vertical stress [kPa]
    
    Returns:
        settlement of this layer [m]
    """
    ...


def compute_layer_settlement_eoed(
    layer: SoilLayer,
    delta_sigma_v: float,
) -> float:
    """Compute settlement of a single layer using constrained modulus.
    
    Δs = (Δσ'_v / Eoed) * H
    
    Parameters:
        layer: soil layer properties (uses layer.Eoed and layer.thickness)
        delta_sigma_v: increase in effective vertical stress [kPa]
    
    Returns:
        settlement of this layer [m]
    """
    ...


def compute_total_settlement(
    profile: SoilProfile,
    drawdown: float,
    method: str = "cc_cr",
) -> tuple[float, list[float]]:
    """Compute total settlement by summing contributions from all layers.
    
    Algorithm:
    1. Compute initial effective stress at each layer midpoint:
       z_mid_i = sum(thickness of layers above) + thickness_i / 2
       σ'_v0_i = compute_initial_stress_profile() evaluated at z_mid_i
    2. Compute effective stress increase at each layer midpoint:
       Δσ'_v_i = compute_stress_increase_from_drawdown() evaluated at z_mid_i
    3. For each layer, if Δσ'_v_i > 0:
       - If method == "cc_cr": Δs_i = compute_layer_settlement_cc_cr(layer_i, σ'_v0_i, Δσ'_v_i)
       - If method == "eoed": Δs_i = compute_layer_settlement_eoed(layer_i, Δσ'_v_i)
    4. Total: s_total = sum(Δs_i for all layers)
    
    Parameters:
        profile: soil profile
        drawdown: drawdown at this location [m]
        method: "cc_cr" or "eoed"
    
    Returns:
        (total_settlement [m], list of per-layer settlements [m])
    """
    ...


def compute_degree_of_consolidation(Tv: float) -> float:
    """Compute degree of consolidation U(Tv) using Terzaghi's closed-form approximations.
    
    For Tv ≤ 0.2827 (U < 60%):
        U = sqrt(4 * Tv / π)
    
    For Tv > 0.2827 (U ≥ 60%):
        U = 1 - (8 / π²) * exp(-π² * Tv / 4)
    
    Parameters:
        Tv: time factor [-] = Cv * t / Hdr²
    
    Returns:
        U: degree of consolidation, 0 to 1
    """
    ...


def compute_settlement_vs_time(
    profile: SoilProfile,
    drawdown: float,
    times_days: np.ndarray,
    method: str = "cc_cr",
) -> np.ndarray:
    """Compute settlement as a function of time (consolidation).
    
    Algorithm:
    1. Compute ultimate settlement s_ult = compute_total_settlement()
    2. Find the compressible (clay) layers — those with Cv > 0 and Cc > 0
    3. For each clay layer:
       a. Determine drainage path Hdr:
          - If bounded by sand layers on both sides: Hdr = thickness / 2 (double drainage)
          - If bounded by sand on one side only: Hdr = thickness (single drainage)
       b. For each time t in times_days:
          - Tv = Cv * t_seconds / Hdr²
          - U(t) = compute_degree_of_consolidation(Tv)
       c. Layer settlement at time t: s_i(t) = U(t) * s_i_ult
    4. For non-clay layers (sand, fill): assume immediate settlement (U = 1 for all t)
    5. Total: s(t) = sum of s_i(t) for all layers
    
    Parameters:
        profile: soil profile
        drawdown: drawdown at location [m]
        times_days: array of times [days]
        method: "cc_cr" or "eoed"
    
    Returns:
        np.ndarray of settlement values [m] at each time step
    """
    ...
```

---

### [NEW] `src/bronbemaling/damage.py`

Building damage classification per Burland & Wroth (1974) and SBR.

```python
"""Building damage assessment using Burland & Wroth and SBR classification.

Computes differential settlement, angular distortion, and classifies damage
risk for neighboring buildings.
"""
from dataclasses import dataclass
from .models import Building, SoilProfile, DewateringConfig, BuildingType


@dataclass
class DamageAssessment:
    """Results of the building damage assessment."""
    settlement_at_points: dict[str, float]  
    # Keys: "center", "corner_1"..."corner_4", values: settlement [m]
    
    max_settlement: float        # [m]
    min_settlement: float        # [m]
    differential_settlement: float  # [m] max - min
    angular_distortion: float    # [-] β = Δs / L (dimensionless)
    deflection_ratio: float      # [-] Δ/L
    
    damage_category: int         # 0–5 (SBR/Burland)
    damage_description: str      # e.g., "Slight (Licht)"
    expected_crack_width: str    # e.g., "1 – 5 mm"
    risk_color: str              # Color code for visualization: "green", "yellow", "orange", "red", "darkred", "black"


# SBR damage classification thresholds
# Based on Burland & Wroth (1974), adapted for Dutch/Flemish practice
SBR_THRESHOLDS = [
    # (max_angular_distortion, category, description_en, description_nl, crack_width, color)
    (1/500, 0, "Negligible",   "Verwaarloosbaar", "< 0.1 mm",   "green"),
    (1/333, 1, "Very slight",  "Zeer licht",      "0.1 – 1 mm", "yellow"),
    (1/250, 2, "Slight",       "Licht",           "1 – 5 mm",   "orange"),
    (1/150, 3, "Moderate",     "Matig",           "5 – 15 mm",  "red"),
    (1/75,  4, "Severe",       "Ernstig",         "15 – 25 mm", "darkred"),
    (float('inf'), 5, "Very severe", "Zeer ernstig", "> 25 mm", "black"),
]


def classify_damage(angular_distortion: float, building_type: BuildingType) -> tuple[int, str, str, str]:
    """Classify damage category from angular distortion.
    
    Algorithm:
    1. Iterate through SBR_THRESHOLDS
    2. Return the first category where angular_distortion < threshold
    3. For CONCRETE_FRAME buildings, shift thresholds by +1 category 
       (concrete frames tolerate more distortion than masonry)
    
    Returns:
        (category, description, crack_width, color)
    """
    ...


def assess_building_damage(
    building: Building,
    profile: SoilProfile,
    config: DewateringConfig,
    drawdown_func,  # callable(points) -> np.ndarray of drawdowns
    settlement_method: str = "cc_cr",
) -> DamageAssessment:
    """Full damage assessment for a building.
    
    Algorithm:
    1. Get evaluation points from building.evaluation_points() → 5 points
    2. Compute drawdown at each point using drawdown_func(points)
    3. Compute settlement at each point using compute_total_settlement(profile, drawdown_i)
    4. Find max and min settlement among the 5 points
    5. Compute differential settlement Δs = max - min
    6. Compute angular distortion β:
       - Find the two points with max settlement difference
       - β = |s1 - s2| / distance(point1, point2)
    7. Compute deflection ratio Δ/L:
       - Δ = max settlement - average of edge settlements
       - L = building diagonal length
    8. Classify damage using classify_damage(β, building.building_type)
    9. Return DamageAssessment
    """
    ...
```

---

### [NEW] `src/bronbemaling/numerical.py`

2D finite-difference groundwater flow solver — pure NumPy/SciPy.

```python
"""2D finite-difference groundwater flow solver.

Solves the steady-state Laplace equation ∇²h = 0 (or with source terms for wells)
on a regular grid, then feeds the resulting drawdown field into the settlement engine.
"""
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve
from .models import DewateringConfig, SoilProfile, ConstructionPit


@dataclass
class FDGrid:
    """Finite-difference grid definition."""
    x: np.ndarray          # 1D array of x-coordinates [m]
    y: np.ndarray          # 1D array of y-coordinates [m]
    dx: float              # Grid spacing in x [m]
    dy: float              # Grid spacing in y [m]
    nx: int                # Number of nodes in x
    ny: int                # Number of nodes in y
    head: np.ndarray       # 2D array of hydraulic head [m], shape (ny, nx)


def create_grid(
    x_range: tuple[float, float],
    y_range: tuple[float, float],
    dx: float = 1.0,
) -> FDGrid:
    """Create a regular finite-difference grid.
    
    Parameters:
        x_range, y_range: (min, max) extents [m]
        dx: grid spacing [m] (same for x and y)
    
    Returns:
        FDGrid with head initialized to 0
    """
    ...


def solve_steady_state(
    grid: FDGrid,
    config: DewateringConfig,
    profile: SoilProfile,
    pit: ConstructionPit,
) -> FDGrid:
    """Solve steady-state groundwater flow equation on the grid.
    
    Governing equation (2D, confined, homogeneous):
        T * (∂²h/∂x² + ∂²h/∂y²) = -Q_well * δ(x_w, y_w)
    
    Discretized (5-point stencil):
        T * (h[i-1,j] + h[i+1,j] + h[i,j-1] + h[i,j+1] - 4*h[i,j]) / dx² = -Q_w / (dx*dy)
    
    Algorithm:
    1. Build the coefficient matrix A as a sparse (CSR) matrix:
       - Interior nodes: 5-point Laplacian stencil, coefficient = T/dx²
       - Boundary nodes: Dirichlet BC, h = H0 (undisturbed head)
       - Well nodes: add source term Q_w / (dx*dy) to RHS vector b
    2. Assemble RHS vector b (zero everywhere except at well nodes and boundaries)
    3. Solve A * h_flat = b using scipy.sparse.linalg.spsolve
    4. Reshape h_flat to 2D grid
    5. Compute drawdown: s = H0 - h
    
    The matrix A has size (nx*ny) × (nx*ny). Node (i,j) maps to index i*nx + j.
    
    Parameters:
        grid: FD grid (modified in place, head field updated)
        config: dewatering config (wells, etc.)
        profile: soil profile (for T computation)
        pit: construction pit geometry (for identifying pit area nodes)
    
    Returns:
        Updated FDGrid with solved head field
    """
    ...


def extract_drawdown_at_points(
    grid: FDGrid,
    points: list[tuple[float, float]],
    H0: float,
) -> np.ndarray:
    """Extract drawdown values at arbitrary points from the grid using bilinear interpolation.
    
    Algorithm:
    1. For each point (x, y):
       a. Find the enclosing grid cell: i, j such that grid.x[j] <= x < grid.x[j+1]
       b. Bilinear interpolation of grid.head at (x, y)
       c. drawdown = H0 - interpolated_head
    2. Use scipy.interpolate.RegularGridInterpolator for efficiency
    
    Returns:
        np.ndarray of drawdown values [m]
    """
    ...
```

---

### [NEW] `src/bronbemaling/plotting.py`

All 7 visualizations. Each is a standalone function returning a `matplotlib.figure.Figure` or `plotly.graph_objects.Figure`.

```python
"""Visualization functions for dewatering settlement analysis.

All functions return Figure objects (matplotlib or plotly) — they do NOT call plt.show().
The notebook calls fig.show() or display(fig) explicitly.
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
import plotly.graph_objects as go
from .models import SoilProfile, ConstructionPit, DewateringConfig, Building
from .damage import DamageAssessment


def plot_cross_section(
    profile: SoilProfile,
    pit: ConstructionPit,
    config: DewateringConfig,
    building: Building,
    drawdown_at_building: float,
) -> plt.Figure:
    """Cross-section showing soil layers, water tables, pit, and building foundation.
    
    Layout (x-axis = horizontal distance, y-axis = depth/elevation):
    1. Draw each soil layer as a colored horizontal band (use distinct colors per soil type):
       - Fill: light brown (#D2B48C)
       - Sand (Zand): yellow (#F4D03F)
       - Clay (Klei): green-gray (#8FBC8F)
       - Peat (Veen): dark brown (#654321)
    2. Draw original GWL as a blue dashed line across the full width
    3. Draw lowered GWL as a blue solid line, following the drawdown cone shape
       (use drawdown computed at multiple x-positions along the section)
    4. Draw the construction pit as a white rectangle with black outline
    5. Draw the building as a gray rectangle at its distance from the pit
    6. Draw the building foundation as a thick black line at foundation_depth
    7. Add mTAW elevation labels on the right y-axis
    8. Hatch the drawdown zone (between original and lowered GWL) with blue diagonal lines
    
    Figure size: (14, 8) inches. Include legend and title.
    """
    ...


def plot_plan_view(
    pit: ConstructionPit,
    config: DewateringConfig,
    building: Building,
    X_grid: np.ndarray,
    Y_grid: np.ndarray,
    drawdown_grid: np.ndarray,
    assessment: DamageAssessment,
) -> plt.Figure:
    """Plan view with pit, wells, drawdown contours, and building.
    
    Layout:
    1. Filled contour plot of drawdown_grid using a blue colormap (light=small, dark=large)
    2. Contour lines with labels (drawdown in meters)
    3. Pit outline as a thick black rectangle
    4. Well positions as red circles with 'W' labels
    5. Building footprint as a colored rectangle:
       - Color = damage assessment risk_color
       - Annotate corners with settlement values in mm
    6. North arrow and scale bar
    7. Colorbar with label "Verlaging (Drawdown) [m]"
    
    Figure size: (12, 10) inches.
    """
    ...


def plot_settlement_trough(
    profile: SoilProfile,
    config: DewateringConfig,
    pit: ConstructionPit,
    building: Building,
    x_transect: np.ndarray,
    settlements: np.ndarray,
) -> plt.Figure:
    """Settlement profile along a transect from pit center through the building.
    
    Layout:
    1. x-axis: horizontal distance [m] from pit center
    2. y-axis: settlement [mm] (positive downward, so invert y-axis)
    3. Plot settlement curve as a solid line with markers
    4. Shade the building footprint zone with a light gray vertical band
    5. Mark the pit extent with a dark gray vertical band
    6. Add horizontal dashed lines for SBR damage thresholds (color-coded)
    7. Annotate max settlement at building location
    
    Figure size: (14, 6) inches.
    """
    ...


def plot_time_settlement(
    times_days: np.ndarray,
    settlements_at_corners: dict[str, np.ndarray],
    pumping_duration_days: float,
) -> plt.Figure:
    """Time-settlement curve showing consolidation over time.
    
    Layout:
    1. x-axis: time [days], log scale optional
    2. y-axis: settlement [mm] (positive downward, inverted)
    3. Plot s(t) curves for each building evaluation point (different line styles)
    4. Vertical dashed line at pumping_duration_days with label
    5. Add secondary y-axis showing degree of consolidation U [%]
    6. Legend identifying each evaluation point
    
    Figure size: (12, 6) inches.
    """
    ...


def plot_effective_stress_profile(
    profile: SoilProfile,
    z: np.ndarray,
    sigma_eff_initial: np.ndarray,
    sigma_eff_final: np.ndarray,
) -> plt.Figure:
    """Effective stress profile with depth, before and after drawdown.
    
    Layout:
    1. x-axis: effective stress σ'_v [kPa]
    2. y-axis: depth [m] (positive downward, inverted)
    3. Plot initial σ'_v as blue line, final σ'_v as red line
    4. Shade the area between them (the stress increase) in light red
    5. Draw horizontal lines at layer boundaries with layer names
    6. Draw GWL marker (original and lowered)
    7. Legend: "Initial (Initieel)" and "After drawdown (Na verlaging)"
    
    Figure size: (8, 10) inches.
    """
    ...


def plot_3d_drawdown(
    X_grid: np.ndarray,
    Y_grid: np.ndarray,
    drawdown_grid: np.ndarray,
    pit: ConstructionPit,
    building: Building,
) -> go.Figure:
    """Interactive 3D surface plot of the drawdown field using plotly.
    
    Layout:
    1. Surface plot of drawdown (z-axis inverted so drawdown goes down)
    2. Colorscale: blues (light = small drawdown, dark = large)
    3. Add pit outline as a 3D line trace at the drawdown surface
    4. Add building footprint as a 3D line trace
    5. Axis labels: "X [m]", "Y [m]", "Verlaging (Drawdown) [m]"
    6. Camera angle: isometric view, adjustable by user
    7. Hover tooltip showing (x, y, drawdown) values
    
    Returns plotly Figure object.
    """
    ...


def plot_damage_summary(
    assessment: DamageAssessment,
) -> plt.Figure:
    """Damage classification summary as a styled table figure.
    
    Layout:
    1. Create a matplotlib table (plt.table) with columns:
       Parameter | Value | Unit | Threshold | Status
    2. Rows:
       - Max settlement | {value} | mm | — | —
       - Min settlement | {value} | mm | — | —
       - Differential settlement | {value} | mm | — | —
       - Angular distortion β | 1/{1/value} | — | 1/500 | ✓/✗
       - Deflection ratio Δ/L | {value} | — | — | —
       - Damage category | {cat} | — | — | {description}
       - Expected crack width | {width} | mm | — | —
    3. Color the "Damage category" row background with assessment.risk_color
    4. Bold the category description
    5. Title: "Building Damage Assessment (Schade-beoordeling)"
    
    Figure size: (10, 4) inches.
    """
    ...
```

---

### [NEW] `src/bronbemaling/__init__.py`

```python
"""Bronbemaling — Ground settlement calculation for dewatering of construction pits.

Berekening van grondverzakking door bronbemaling bij bouwputten.
"""
from .models import (
    SoilLayer, SoilProfile, Well, ConstructionPit,
    DewateringConfig, Building, AquiferType, BuildingType,
)
from .hydraulics import (
    compute_drawdown_at_points, compute_drawdown_grid,
    compute_transmissivity, compute_storativity, compute_radius_of_influence,
)
from .settlement import (
    compute_initial_stress_profile, compute_stress_increase_from_drawdown,
    compute_total_settlement, compute_settlement_vs_time,
)
from .damage import assess_building_damage, DamageAssessment
from .numerical import create_grid, solve_steady_state, extract_drawdown_at_points

__version__ = "0.1.0"
```

---

### [NEW] `notebooks/example_analysis.ipynb`

A complete worked example notebook with the following cell structure:

**Cell 1 — Markdown**: Title, description, author, date  
**Cell 2 — Code**: Imports (`from bronbemaling import *`, numpy, matplotlib, plotly)  
**Cell 3 — Markdown**: "§1 Input Parameters (Invoergegevens)"  
**Cell 4 — Code**: Define the default Flemish scenario:

```python
# === Soil Profile (Grondopbouw) ===
profile = SoilProfile(
    surface_level_mtaw=5.0,  # mTAW
    gwl_mtaw=4.0,            # mTAW (1m below surface)
    layers=[
        SoilLayer("Aanvulling (Fill)", thickness=0.5, gamma=17.0, gamma_sat=19.0,
                  k_h=1e-5, e0=0.6, Cc=0.05, Cr=0.01, Eoed=15000, Cv=1e-4, OCR=3.0),
        SoilLayer("Zand (Sand)", thickness=2.0, gamma=17.5, gamma_sat=20.0,
                  k_h=1e-4, e0=0.5, Cc=0.02, Cr=0.005, Eoed=30000, Cv=1e-2, OCR=1.5),
        SoilLayer("Klei (Clay)", thickness=3.0, gamma=16.0, gamma_sat=18.5,
                  k_h=1e-9, e0=1.0, Cc=0.30, Cr=0.06, Eoed=3000, Cv=1e-7, OCR=1.5),
        SoilLayer("Zand (Sand, deep)", thickness=4.5, gamma=18.0, gamma_sat=20.5,
                  k_h=5e-4, e0=0.45, Cc=0.01, Cr=0.003, Eoed=40000, Cv=1e-2, OCR=1.0),
    ]
)

# === Construction Pit (Bouwput) ===
pit = ConstructionPit(length=10.0, width=8.0, depth=3.0, 
                      center_x=0.0, center_y=0.0, bottom_mtaw=2.0)

# === Wells (Bronnen) ===
# 6 wells evenly spaced along pit perimeter
wells = [
    Well(x=-5.5, y=-4.5, Q=0.0005, screen_top_mtaw=3.0, screen_bottom_mtaw=0.0),
    Well(x=0.0,  y=-4.5, Q=0.0005, screen_top_mtaw=3.0, screen_bottom_mtaw=0.0),
    Well(x=5.5,  y=-4.5, Q=0.0005, screen_top_mtaw=3.0, screen_bottom_mtaw=0.0),
    Well(x=-5.5, y=4.5,  Q=0.0005, screen_top_mtaw=3.0, screen_bottom_mtaw=0.0),
    Well(x=0.0,  y=4.5,  Q=0.0005, screen_top_mtaw=3.0, screen_bottom_mtaw=0.0),
    Well(x=5.5,  y=4.5,  Q=0.0005, screen_top_mtaw=3.0, screen_bottom_mtaw=0.0),
]

# === Dewatering (Bemaling) ===
dewatering = DewateringConfig(
    wells=wells,
    target_drawdown_mtaw=1.5,   # mTAW (pump down to 1.5 mTAW)
    original_gwl_mtaw=4.0,      # mTAW
    pumping_duration_days=90,
    aquifer_type=AquiferType.UNCONFINED,
)

# === Neighboring Building (Naburig Gebouw) ===
building = Building(x=12.0, y=0.0, length=10.0, width=6.0,
                    foundation_depth=0.6, building_type=BuildingType.MASONRY)
```

**Cell 5 — Markdown**: "§2 Drawdown Calculation (Verlagingsberekening)"  
**Cell 6 — Code**: Compute drawdown at building, on grid; print summary  
**Cell 7 — Code**: Plot cross-section (plot 1)  
**Cell 8 — Code**: Plot plan view with contours (plot 2)  
**Cell 9 — Code**: Plot 3D drawdown surface (plot 6 — plotly)  

**Cell 10 — Markdown**: "§3 Settlement Calculation (Zettingsberekening)"  
**Cell 11 — Code**: Compute stresses and settlement; print per-layer breakdown  
**Cell 12 — Code**: Plot effective stress profile (plot 5)  
**Cell 13 — Code**: Plot settlement trough (plot 3)  

**Cell 14 — Markdown**: "§4 Time-Dependent Consolidation (Tijdsafhankelijke Consolidatie)"  
**Cell 15 — Code**: Compute and plot time-settlement curve (plot 4)  

**Cell 16 — Markdown**: "§5 Damage Assessment (Schade-beoordeling)"  
**Cell 17 — Code**: Run damage assessment; plot summary table (plot 7)  

**Cell 18 — Markdown**: "§6 Numerical Method — Finite Difference (Numerieke Methode)"  
**Cell 19 — Code**: Run FD solver; compare analytical vs numerical  

**Cell 20 — Markdown**: "§7 Sensitivity Analysis (Gevoeligheidsanalyse)"  
**Cell 21–25 — Code**: One cell per sensitivity parameter (distance, drawdown, clay thickness, permeability, number of wells)  

**Cell 26 — Markdown**: "§8 Verification (Verificatie)"  
**Cell 27 — Code**: Hand-calculation cross-check assertions  

---

## Verification Plan

### Automated Tests
- **Verification cell** (Cell 27) in the notebook: hand-calculated drawdown and settlement for a simple single-well, single-layer case. Assert notebook results match within 5%.
- **Cross-check**: Thiem vs. Theis at $t \to \infty$ — verify convergence within 1%.
- **Numerical vs. analytical**: FD drawdown at building location within 10% of Thiem/Theis.

### Manual Verification
- Run `uv run jupyter lab` and execute all cells in a fresh kernel — all cells must pass without errors.
- Visual inspection of all 7 plots for physical plausibility.
- Default scenario should yield settlement in the range 1–50 mm (residential scale).
