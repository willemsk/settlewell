"""2D finite-difference groundwater flow solver.

Solves the steady-state groundwater flow equation ∇²h = 0 (or with source/sink terms for wells)
on a regular grid, then feeds the resulting drawdown field into the settlement engine.
"""

from dataclasses import dataclass

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
    x_range: tuple[float, float],
    y_range: tuple[float, float],
    dx: float = 1.0,
) -> FDGrid:
    """Create a regular 2D finite-difference grid.

    Parameters
    ----------
    x_range : tuple[float, float]
        (x_min, x_max) grid extents [m].
    y_range : tuple[float, float]
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

    # Build right hand side vector b
    b = np.zeros(N, dtype=float)
    inv_dx2 = 1.0 / (dx * dx)
    inv_dy2 = 1.0 / (dy * dy)

    # Identify boundary nodes
    is_boundary = np.zeros(N, dtype=bool)
    is_boundary[:nx] = True  # Bottom row
    is_boundary[-nx:] = True  # Top row
    is_boundary[::nx] = True  # Left column
    is_boundary[nx - 1 :: nx] = True  # Right column

    b[is_boundary] = H0

    # Build sparse coefficient matrix A using diags
    main_diag = np.full(N, -2.0 * T * (inv_dx2 + inv_dy2))
    main_diag[is_boundary] = 1.0

    left_diag = np.full(N - 1, T * inv_dx2)
    left_diag[is_boundary[1:]] = 0.0

    right_diag = np.full(N - 1, T * inv_dx2)
    right_diag[is_boundary[:-1]] = 0.0

    bottom_diag = np.full(N - nx, T * inv_dy2)
    bottom_diag[is_boundary[nx:]] = 0.0

    top_diag = np.full(N - nx, T * inv_dy2)
    top_diag[is_boundary[:-nx]] = 0.0

    A_csr = sparse.diags(
        [bottom_diag, left_diag, main_diag, right_diag, top_diag],
        [-nx, -1, 0, 1, nx],
        shape=(N, N),
        format="csr",
    )

    # Add well extraction sink terms
    if config.wells:
        wells_x = np.array([w.x for w in config.wells])
        wells_y = np.array([w.y for w in config.wells])
        wells_Q = np.array([w.Q for w in config.wells])

        # Find nearest grid node (iw, jw) for all wells
        diff_x = np.abs(grid.x[:, np.newaxis] - wells_x)
        jws = np.argmin(diff_x, axis=0)

        diff_y = np.abs(grid.y[:, np.newaxis] - wells_y)
        iws = np.argmin(diff_y, axis=0)

        valid = (iws > 0) & (iws < ny - 1) & (jws > 0) & (jws < nx - 1)

        # Apply source term to interior nodes
        valid_iws = iws[valid]
        valid_jws = jws[valid]
        valid_Qs = wells_Q[valid]
        kws = valid_iws * nx + valid_jws

        np.add.at(b, kws, valid_Qs / (dx * dy))

        # Handle warnings for invalid wells
        invalid_indices = np.where(~valid)[0]
        if len(invalid_indices) > 0:
            import warnings

            for idx in invalid_indices:
                w_x, w_y = wells_x[idx], wells_y[idx]
                warnings.warn(
                    f"Well at ({w_x}, {w_y}) is located on or outside grid boundary. "
                    "Expand grid extents to include well inside interior nodes."
                )

    # Solve sparse linear system A * h = b
    h_flat = spsolve(A_csr, b)

    grid.head = h_flat.reshape((ny, nx))
    return grid


def extract_drawdown_at_points(
    grid: FDGrid,
    points: list[tuple[float, float]],
    H0: float,
) -> np.ndarray:
    """Extract drawdown at arbitrary (x, y) coordinates using bilinear interpolation.

    Parameters
    ----------
    grid : FDGrid
        Grid containing solved hydraulic head field.
    points : list[tuple[float, float]]
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
