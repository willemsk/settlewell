"""2D finite-difference groundwater flow solver.

Solves the steady-state groundwater flow equation ∇²h = 0 (or with source/sink terms for wells)
on a regular grid, then feeds the resulting drawdown field into the settlement engine.
"""

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
from scipy import sparse
from scipy.interpolate import RegularGridInterpolator
from scipy.sparse.linalg import spsolve

from .hydraulics import compute_transmissivity
from .models import ConstructionPit, DewateringConfig, SoilProfile


@dataclass
class FDGrid:
    """Finite-difference grid definition for 2D groundwater flow.

    Parameters
    ----------
    x : numpy.ndarray
        1D array of node x-coordinates [m].
    y : numpy.ndarray
        1D array of node y-coordinates [m].
    dx : float
        Grid spacing in x-direction [m].
    dy : float
        Grid spacing in y-direction [m].
    nx : int
        Number of grid nodes along x-axis.
    ny : int
        Number of grid nodes along y-axis.
    head : numpy.ndarray
        2D array of hydraulic head values [m], shape (ny, nx).
    """

    x: np.ndarray
    y: np.ndarray
    dx: float
    dy: float
    nx: int
    ny: int
    head: np.ndarray


def create_grid(
    x_range: Tuple[float, float],
    y_range: Tuple[float, float],
    dx: float = 1.0,
) -> FDGrid:
    """Create a regular 2D finite-difference grid.

    Parameters
    ----------
    x_range : Tuple[float, float]
        (x_min, x_max) grid extents [m].
    y_range : Tuple[float, float]
        (y_min, y_max) grid extents [m].
    dx : float, default 1.0
        Uniform grid node spacing [m] (used for both dx and dy).

    References
    ----------
    Harbaugh, A. W. (2005). MODFLOW-2005.

    Returns
    -------
    FDGrid
        Initialized finite-difference grid with head initialized to 0.
    """
    x = np.arange(x_range[0], x_range[1] + dx / 2.0, dx)
    y = np.arange(y_range[0], y_range[1] + dx / 2.0, dx)
    nx = len(x)
    ny = len(y)
    head = np.zeros((ny, nx), dtype=float)

    return FDGrid(x=x, y=y, dx=dx, dy=dx, nx=nx, ny=ny, head=head)


def solve_steady_state(
    grid: FDGrid,
    config: DewateringConfig,
    profile: SoilProfile,
    pit: ConstructionPit,
) -> FDGrid:
    """Solve steady-state 2D groundwater flow equation on the grid.

    Governing partial differential equation:
    $$T \\left( \\frac{\\partial^2 h}{\\partial x^2} + \\frac{\\partial^2 h}{\\partial y^2} \\right) = - \\sum_w Q_w \\delta(x_w, y_w)$$

    Parameters
    ----------
    grid : FDGrid
        Grid definition (modified in place, head array updated).
    config : DewateringConfig
        Dewatering configuration specifying well coordinates and extraction rates.
    profile : SoilProfile
        Soil profile for transmissivity computation.
    pit : ConstructionPit
        Construction pit geometry.

    References
    ----------
    Harbaugh, A. W. (2005). MODFLOW-2005.

    Returns
    -------
    FDGrid
        Updated grid with solved hydraulic head field [mTAW].
    """
    T = compute_transmissivity(profile, config)
    H0 = config.original_gwl_mtaw
    nx, ny = grid.nx, grid.ny
    dx, dy = grid.dx, grid.dy
    N = nx * ny

    # Build sparse coefficient matrix A in LIL format, vector b
    A = sparse.lil_matrix((N, N), dtype=float)
    b = np.zeros(N, dtype=float)

    inv_dx2 = 1.0 / (dx * dx)
    inv_dy2 = 1.0 / (dy * dy)

    for i in range(ny):
        for j in range(nx):
            k = i * nx + j

            # Boundary nodes: Dirichlet BC h = H0
            if i == 0 or i == ny - 1 or j == 0 or j == nx - 1:
                A[k, k] = 1.0
                b[k] = H0
            else:
                # Interior nodes: 5-point Laplacian stencil
                A[k, k] = -2.0 * T * (inv_dx2 + inv_dy2)
                A[k, k - 1] += T * inv_dx2  # Left: (i, j-1)
                A[k, k + 1] += T * inv_dx2  # Right: (i, j+1)
                A[k, k - nx] += T * inv_dy2  # Bottom: (i-1, j)
                A[k, k + nx] += T * inv_dy2  # Top: (i+1, j)
                b[k] = 0.0

    # Add well extraction sink terms
    for well in config.wells:
        # Find nearest grid node (iw, jw)
        jw = int(np.argmin(np.abs(grid.x - well.x)))
        iw = int(np.argmin(np.abs(grid.y - well.y)))

        # Apply source term to interior nodes
        if 0 < iw < ny - 1 and 0 < jw < nx - 1:
            kw = iw * nx + jw
            b[kw] += well.Q / (dx * dy)
        else:
            import warnings

            warnings.warn(
                f"Well at ({well.x}, {well.y}) is located on or outside grid boundary. "
                "Expand grid extents to include well inside interior nodes."
            )

    # Solve sparse linear system A * h = b
    A_csr = A.tocsr()
    h_flat = spsolve(A_csr, b)

    grid.head = h_flat.reshape((ny, nx))
    return grid


def extract_drawdown_at_points(
    grid: FDGrid,
    points: List[Tuple[float, float]],
    H0: float,
) -> np.ndarray:
    """Extract drawdown at arbitrary (x, y) coordinates using bilinear interpolation.

    Parameters
    ----------
    grid : FDGrid
        Grid containing solved hydraulic head field.
    points : List[Tuple[float, float]]
        List of (x, y) coordinate pairs [m].
    H0 : float
        Undisturbed groundwater head [mTAW].

    References
    ----------
    Harbaugh, A. W. (2005). MODFLOW-2005.

    Returns
    -------
    numpy.ndarray
        1D array of drawdown values s = H0 - h [m].
    """
    interpolator = RegularGridInterpolator(
        (grid.y, grid.x),
        grid.head,
        method="linear",
        bounds_error=False,
        fill_value=H0,
    )

    eval_pts = np.array([(py, px) for px, py in points], dtype=float)
    h_interp = interpolator(eval_pts)
    s = H0 - h_interp
    return np.maximum(0.0, s)
