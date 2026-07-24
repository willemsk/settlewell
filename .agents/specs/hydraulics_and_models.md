# Hydraulics & Data Models Specification

This document specifies the core input data structures (`src/settlewell/models.py`) and analytical groundwater hydraulics engines (`src/settlewell/hydraulics.py`).

---

## Dataclass Models (`src/settlewell/models.py`)

### Enums
- **`AquiferType`**: `CONFINED` ("confined"), `UNCONFINED` ("unconfined").
- **`BuildingType`**: `MASONRY` ("masonry"), `CONCRETE_FRAME` ("concrete_frame").

### Dataclasses

#### `SoilLayer`
Defines a single stratigraphical soil layer.
```python
@dataclass
class SoilLayer:
    name: str  # Layer name (e.g. "Klei" or "Zand")
    thickness: float  # [m] Layer thickness
    gamma: float  # [kN/m³] Dry unit weight
    gamma_sat: float  # [kN/m³] Saturated unit weight
    k_h: float  # [m/s] Horizontal hydraulic conductivity
    e0: float  # [-] Initial void ratio
    Cc: float  # [-] Primary compression index
    Cr: float  # [-] Recompression index
    Eoed: float  # [kPa] Oedometer modulus
    Cv: float  # [m²/s] Coefficient of consolidation
    OCR: float = 1.0  # [-] Overconsolidation ratio
```
*Validation*: `thickness > 0`, `gamma > 0`, `gamma_sat >= gamma`, `k_h > 0`, `e0 > 0`, `Cc >= 0`, `Cr >= 0`, `Cr <= Cc`, `Eoed > 0`, `Cv >= 0`, `OCR >= 1.0`.

#### `SoilProfile`
Ordered vertical sequence of soil layers.
```python
@dataclass
class SoilProfile:
    layers: list[SoilLayer]  # Ordered top to bottom
    gwl_mtaw: float  # [mTAW] Groundwater level
    surface_level_mtaw: float  # [mTAW] Ground surface level
```
*Validation*: `layers` must not be empty, `surface_level_mtaw >= gwl_mtaw`. Includes helper properties `gwl_depth`, `total_depth`, and conversion methods `mtaw_to_depth`, `depth_to_mtaw`.

#### `Well`
A single dewatering extraction well.
```python
@dataclass
class Well:
    x: float  # [m] x-coordinate
    y: float  # [m] y-coordinate
    Q: float  # [m³/s] Extraction discharge rate
    r_w: float = 0.075  # [m] Well casing radius
    screen_top_mtaw: float = 0.0  # [mTAW] Screen top level
    screen_bottom_mtaw: float = 0.0  # [mTAW] Screen bottom level
```
*Validation*: `r_w > 0`, `screen_top_mtaw >= screen_bottom_mtaw`.

#### `ConstructionPit`
Geometry of excavation construction pit.
```python
@dataclass
class ConstructionPit:
    length: float  # [m] Excavation length (parallel to x)
    width: float  # [m] Excavation width (parallel to y)
    depth: float  # [m] Excavation depth
    center_x: float = 0.0  # [m] Pit center x-coordinate
    center_y: float = 0.0  # [m] Pit center y-coordinate
    bottom_mtaw: float = 0.0  # [mTAW] Pit excavation bottom level
```

#### `DewateringConfig`
Layout and target parameters for the dewatering system.
```python
@dataclass
class DewateringConfig:
    wells: list[Well]
    target_drawdown_mtaw: float  # [mTAW] Target pit water level
    original_gwl_mtaw: float  # [mTAW] Original undisturbed GWL
    pumping_duration_days: float  # [days] Dewatering duration
    aquifer_type: AquiferType = AquiferType.UNCONFINED
    R: float | None = None  # [m] Radius of influence
    T: float | None = None  # [m²/s] Transmissivity
    S: float | None = None  # [-] Storativity
```
*Property*: `target_drawdown = original_gwl_mtaw - target_drawdown_mtaw` [m].

#### `Building`
Neighboring structure evaluated for settlement damage.
```python
@dataclass
class Building:
    x: float  # [m] Center x-coordinate
    y: float  # [m] Center y-coordinate
    length: float  # [m] Dimension parallel to x (at 0° rot)
    width: float  # [m] Dimension parallel to y (at 0° rot)
    orientation_deg: float = 0.0  # [deg] Rotation counter-clockwise
    foundation_depth: float = 0.6  # [m] Foundation depth below surface
    building_type: BuildingType = BuildingType.MASONRY
```
*Methods*: `corner_coordinates()` returns 4 corner coordinates; `evaluation_points()` returns 5 evaluation points `[center, corner1, corner2, corner3, corner4]`.

---

## Analytical Hydraulics (`src/settlewell/hydraulics.py`)

### Core Equations

#### Sichardt Formula (Radius of Influence $R$)
\[
R = 3000 \cdot s_{pit} \cdot \sqrt{k_{\text{rep}}}
\]
where $k_{\text{rep}} = T / H_0$ [m/s] is representative conductivity, $s_{pit} = H_{gwl} - H_{target}$ [m] is pit drawdown, clamped to $R \ge 1.0\text{ m}$.

#### Thiem Equation (Steady-State Radial Drawdown)
- **Unconfined Aquifer**:
  \[
  h(r)^2 = H_0^2 - \frac{Q}{\pi k} \ln\left(\frac{R}{r}\right) \implies s(r) = H_0 - \sqrt{\max\left(0, H_0^2 - \frac{Q}{\pi k} \ln\left(\frac{R}{r}\right)\right)}
  \]
- **Confined Aquifer**:
  \[
  s(r) = \frac{Q}{2\pi T} \ln\left(\frac{R}{r}\right)
  \]

#### Theis Equation (Unsteady-State Drawdown)
\[
s(r, t) = \frac{Q}{4\pi T} W(u), \quad u = \frac{r^2 S}{4 T t}
\]
where $W(u) = E_1(u)$ is evaluated via `scipy.special.exp1(u)`.

#### Principle of Superposition
- **Confined / Transient**: $s_{\text{tot}}(x,y) = \sum_{i=1}^N s_i(r_i, t)$
- **Unconfined Steady-State (Dupuit)**: $h^2_{\text{tot}}(x,y) = H_0^2 - \sum_{i=1}^N (H_0^2 - h_i^2(r_i))$

### Key Functions
- `compute_radius_of_influence(config: DewateringConfig, T: float, H0: float = 10.0) -> float`
- `compute_transmissivity(profile: SoilProfile, config: DewateringConfig) -> float`
- `compute_storativity(profile: SoilProfile, config: DewateringConfig) -> float`
- `thiem_drawdown_single_well(r: float | np.ndarray, Q: float, T: float, R: float, H0: float, aquifer_type: AquiferType, r_w: float = 0.075) -> float | np.ndarray`
- `theis_drawdown_single_well(r: float | np.ndarray, t: float, Q: float, T: float, S: float, r_w: float = 0.075) -> float | np.ndarray`
- `compute_drawdown_at_points(points: list[tuple[float, float]], config: DewateringConfig, profile: SoilProfile, time_s: float | None = None) -> np.ndarray`
- `compute_drawdown_grid(x_range: tuple[float, float], y_range: tuple[float, float], nx: int, ny: int, config: DewateringConfig, profile: SoilProfile, time_s: float | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray]`
