# 2D Finite-Difference Groundwater Solver Specification

This document specifies the 2D finite-difference groundwater flow solver implemented in `src/settlewell/numerical.py`.

---

## Overview

The 2D finite-difference solver computes steady-state groundwater head distributions $h(x, y)$ on a regular rectangular grid mesh for complex geometries and well configurations.

---

## Mathematical Formulation

### Steady-State Governing Equation
\[
\frac{\partial}{\partial x} \left( T \frac{\partial h}{\partial x} \right) + \frac{\partial}{\partial y} \left( T \frac{\partial h}{\partial y} \right) = Q(x, y)
\]
where $T = k \cdot H_{aq}$ is transmissivity [m²/s], $h(x,y)$ is hydraulic head [mTAW], and $Q(x,y)$ represents well extraction sink/source terms [m/s].

### 5-Point Finite-Difference Discretization
For uniform grid node spacing $\Delta x = \Delta y$:
\[
T_{i+1/2, j} (h_{i+1, j} - h_{i, j}) - T_{i-1/2, j} (h_{i, j} - h_{i-1, j}) + T_{i, j+1/2} (h_{i, j+1} - h_{i, j}) - T_{i, j-1/2} (h_{i, j} - h_{i, j-1}) = Q_{i,j} \cdot \Delta x \cdot \Delta y
\]

### Boundary Conditions
- **Dirichlet Boundary (Fixed Head)**: Outer boundary grid nodes (edges) are held fixed at undisturbed groundwater head $H_0$:
  \[
  h(x, y) = H_0 \quad \forall (x, y) \in \partial\Omega
  \]

---

## Implementation Architecture (`src/settlewell/numerical.py`)

### Grid Representation (`FDGrid`)
```python
@dataclass
class FDGrid:
    x: np.ndarray  # 1D array of x coordinates [m]
    y: np.ndarray  # 1D array of y coordinates [m]
    dx: float  # Grid node spacing in x [m]
    dy: float  # Grid node spacing in y [m]
    nx: int  # Number of grid nodes in x
    ny: int  # Number of grid nodes in y
    head: np.ndarray  # 2D head solution array of shape (ny, nx) [mTAW]
```

### Core Functions

#### `create_grid(x_range: tuple[float, float], y_range: tuple[float, float], dx: float = 1.0) -> FDGrid`
Constructs a regular 2D rectangular grid mesh based on specified coordinate extents `x_range` and `y_range` and node spacing $\Delta x$. Initializes `head` array with zeros.

#### `solve_steady_state(grid: FDGrid, config: DewateringConfig, profile: SoilProfile, pit: ConstructionPit) -> FDGrid`
Solves the sparse linear system $A \cdot h = b$ using `scipy.sparse.linalg.spsolve`:
1. Computes transmissivity $T$ from `SoilProfile` and `DewateringConfig`.
2. Assembles 5-point Laplacian sparse matrix $A$ in CSR format (`scipy.sparse.lil_matrix` converted to `csr_matrix`).
3. Maps extraction well rates $Q_k$ [m³/s] to nearest grid node indices $(i, j)$ using nearest-node lookup (`np.argmin`), adding $Q_k / (\Delta x \cdot \Delta y)$ to right-hand side vector $b$.
4. Enforces Dirichlet boundary conditions ($h = H_0$) at outer boundary nodes.
5. Solves $A h = b$ and updates `grid.head` in-place.

#### `extract_drawdown_at_points(grid: FDGrid, points: list[tuple[float, float]], H0: float) -> np.ndarray`
Extracts drawdown $s = \max(0, H_0 - h)$ at arbitrary evaluation points using 2D bilinear interpolation (`scipy.interpolate.RegularGridInterpolator`). Clips resulting drawdown array to non-negative values.
