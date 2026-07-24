# Visualization Suite Specification

This document specifies the visualization suite implemented in `src/settlewell/plotting.py`.

---

## Overview

The plotting suite provides Matplotlib and Plotly figures for geotechnical cross-sections, 2D/3D drawdown contours, settlement trough profiles, time-settlement curves, effective stress distributions, and building damage summaries.

---

## Core Plotting Functions (`src/settlewell/plotting.py`)

### 1. Soil Profile Cross-Section (`plot_cross_section`)
```python
def plot_cross_section(
    profile: SoilProfile,
    pit: ConstructionPit,
    config: DewateringConfig,
    building: Building,
    drawdown_at_building: float,
) -> plt.Figure
```
- **Description**: Generates a 2D vertical elevation cross-section showing soil stratigraphy layers (color-coded by soil type in `SOIL_COLORS`), initial undisturbed GWL line (dashed blue), lowered GWL drawdown cone, construction pit excavation rectangle, and neighboring building foundation footprint.
- **Return**: Matplotlib `plt.Figure`.

### 2. 2D Plan View Contour Map (`plot_plan_view`)
```python
def plot_plan_view(
    pit: ConstructionPit,
    config: DewateringConfig,
    building: Building,
    X_grid: np.ndarray,
    Y_grid: np.ndarray,
    drawdown_grid: np.ndarray,
    assessment: DamageAssessment,
) -> plt.Figure
```
- **Description**: Displays 2D spatial drawdown contours (`plt.contourf` with `Blues` colormap), extraction well markers (`W1`, `W2`), construction pit outline, and rotated building footprint labeled with corner settlement values and risk severity color.
- **Return**: Matplotlib `plt.Figure`.

### 3. Interactive 3D Drawdown Surface (`plot_3d_drawdown`)
```python
def plot_3d_drawdown(
    X_grid: np.ndarray,
    Y_grid: np.ndarray,
    drawdown_grid: np.ndarray,
    pit: ConstructionPit,
    building: Building,
) -> go.Figure
```
- **Description**: Interactive 3D inverted cone surface map using Plotly (`go.Surface` with `Blues` colorscale) featuring pit and building 3D mesh overlays.
- **Return**: Plotly `plotly.graph_objects.Figure`.

### 4. Matplotlib 3D Drawdown Surface (`plot_3d_drawdown_mpl`)
```python
def plot_3d_drawdown_mpl(
    X_grid: np.ndarray,
    Y_grid: np.ndarray,
    drawdown_grid: np.ndarray,
    pit: ConstructionPit | None = None,
) -> plt.Figure
```
- **Description**: Static 3D Matplotlib surface plot (`ax.plot_surface`) with inverted drawdown z-axis.
- **Return**: Matplotlib `plt.Figure`.

### 5. Settlement Trough Profile (`plot_settlement_trough`)
```python
def plot_settlement_trough(
    profile: SoilProfile,
    config: DewateringConfig,
    pit: ConstructionPit,
    building: Building,
    x_transect: np.ndarray,
    settlements: np.ndarray,
) -> plt.Figure
```
- **Description**: Plots 1D settlement trough curve $s(x)$ [mm] along a spatial transect, highlighting pit zone (`gray`) and building extent (`khaki`).
- **Return**: Matplotlib `plt.Figure`.

### 6. Time-Settlement Consolidation Curves (`plot_time_settlement`)
```python
def plot_time_settlement(
    times_days: np.ndarray,
    settlements_at_corners: dict[str, np.ndarray],
    pumping_duration_days: float,
) -> plt.Figure
```
- **Description**: Plots time-dependent settlement curves $s(t)$ for building evaluation points (center and 4 corners), marking end of dewatering pumping duration with a vertical red dashed line.
- **Return**: Matplotlib `plt.Figure`.

### 7. Vertical Effective Stress Profile (`plot_effective_stress_profile`)
```python
def plot_effective_stress_profile(
    profile: SoilProfile,
    z: np.ndarray,
    sigma_eff_initial: np.ndarray,
    sigma_eff_final: np.ndarray,
) -> plt.Figure
```
- **Description**: Displays initial and final vertical effective stress profiles $\sigma'_v$ [kPa] vs depth $z$ [m].
- **Return**: Matplotlib `plt.Figure`.

### 8. Damage Assessment Summary Card (`plot_damage_summary`)
```python
def plot_damage_summary(assessment: DamageAssessment) -> plt.Figure
```
- **Description**: Generates a clean tabular summary card displaying max settlement, differential settlement, angular distortion $\beta$, deflection ratio, SBR category (0–5), and crack width range.
- **Return**: Matplotlib `plt.Figure`.
