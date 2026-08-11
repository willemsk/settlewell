import numpy as np
from numpy.typing import NDArray

from settlewell.models import LoadGeometry, LoadType, StressMethod


def fadum_corner_stress(
    b: float | np.ndarray, l_dim: float | np.ndarray, z: float | np.ndarray
) -> float | np.ndarray:
    """
    Calculate Fadum (1948) corner stress influence value Iz for a rectangle b x l_dim at depth z.

    Parameters
    ----------
    b : float or np.ndarray
        Width of the rectangular area [m].
    l_dim : float or np.ndarray
        Length of the rectangular area [m].
    z : float or np.ndarray
        Depth below the loaded area [m].

    Returns
    -------
    float or np.ndarray
        Vertical stress influence factor Iz [-].
    """
    b_arr = np.atleast_1d(np.asarray(b, dtype=float))
    l_dim_arr = np.atleast_1d(np.asarray(l_dim, dtype=float))
    z_arr = np.atleast_1d(np.asarray(z, dtype=float))

    shape = np.broadcast_shapes(b_arr.shape, l_dim_arr.shape, z_arr.shape)
    b_b = np.broadcast_to(b_arr, shape)
    l_b = np.broadcast_to(l_dim_arr, shape)
    z_b = np.broadcast_to(z_arr, shape)

    out = np.zeros(shape, dtype=float)

    mask_z = z_b <= 1e-6
    mask_bl = (b_b <= 1e-6) | (l_b <= 1e-6)

    out[mask_z] = 0.25
    out[~mask_z & mask_bl] = 0.0

    valid = ~mask_z & ~mask_bl
    if np.any(valid):
        b_v = b_b[valid]
        l_v = l_b[valid]
        z_v = z_b[valid]

        m = b_v / z_v
        n = l_v / z_v
        m2 = m * m
        n2 = n * n
        v = m2 + n2 + 1.0
        v_mn = m2 * n2

        term1 = (2.0 * m * n * np.sqrt(v) / (v + v_mn)) * ((v + 1.0) / v)

        with np.errstate(divide="ignore", invalid="ignore"):
            arg2 = (2.0 * m * n * np.sqrt(v)) / (v - v_mn)

        diff = v - v_mn
        arg2_val = np.zeros_like(diff)

        mask_eq = np.abs(diff) < 1e-12
        mask_lt = diff < 0
        mask_gt = ~(mask_eq | mask_lt)

        arg2_val[mask_eq] = np.pi / 2.0
        arg2_val[mask_lt] = np.arctan(arg2[mask_lt]) + np.pi
        arg2_val[mask_gt] = np.arctan(arg2[mask_gt])

        out[valid] = (1.0 / (4.0 * np.pi)) * (term1 + arg2_val)

    if np.isscalar(b) and np.isscalar(l_dim) and np.isscalar(z):
        return float(out.item())
    elif out.ndim == 0:
        return float(out)
    return out


def boussinesq_strip_stress(
    q: float | np.ndarray,
    B: float | np.ndarray,
    x_rel: float | np.ndarray,
    z: float | np.ndarray,
) -> float | np.ndarray:
    """
    Calculate vertical stress increment under a Boussinesq strip load.

    Parameters
    ----------
    q : float or np.ndarray
        Applied uniform stress [kPa].
    B : float or np.ndarray
        Width of the strip load [m].
    x_rel : float or np.ndarray
        Horizontal distance from the center of the strip [m].
    z : float or np.ndarray
        Depth below the load [m].

    Returns
    -------
    float or np.ndarray
        Vertical stress increment [kPa].
    """
    q_arr = np.atleast_1d(np.asarray(q, dtype=float))
    B_arr = np.atleast_1d(np.asarray(B, dtype=float))
    x_rel_arr = np.atleast_1d(np.asarray(x_rel, dtype=float))
    z_arr = np.atleast_1d(np.asarray(z, dtype=float))

    shape = np.broadcast_shapes(q_arr.shape, B_arr.shape, x_rel_arr.shape, z_arr.shape)
    q_b = np.broadcast_to(q_arr, shape)
    B_b = np.broadcast_to(B_arr, shape)
    x_rel_b = np.broadcast_to(x_rel_arr, shape)
    z_b = np.broadcast_to(z_arr, shape)

    out = np.zeros(shape, dtype=float)

    mask_z = z_b <= 1e-6
    mask_in_B = np.abs(x_rel_b) <= B_b / 2.0
    out[mask_z & mask_in_B] = q_b[mask_z & mask_in_B]
    out[mask_z & ~mask_in_B] = 0.0

    valid = ~mask_z
    if np.any(valid):
        q_v = q_b[valid]
        B_v = B_b[valid]
        x_v = x_rel_b[valid]
        z_v = z_b[valid]

        x_L = x_v - B_v / 2.0
        x_R = x_v + B_v / 2.0

        alpha = np.arctan(x_R / z_v) - np.arctan(x_L / z_v)
        out[valid] = (q_v / np.pi) * (alpha + np.sin(alpha) * np.cos(alpha))

    if np.isscalar(q) and np.isscalar(B) and np.isscalar(x_rel) and np.isscalar(z):
        return float(out.item())
    elif out.ndim == 0:
        return float(out)
    return out


def boussinesq_rectangular_stress(
    q: float | np.ndarray,
    B: float | np.ndarray,
    L: float | np.ndarray,
    x_rel: float | np.ndarray,
    z: float | np.ndarray,
) -> float | np.ndarray:
    """
    Calculate vertical stress increment under a Boussinesq rectangular load.

    Parameters
    ----------
    q : float or np.ndarray
        Applied uniform stress [kPa].
    B : float or np.ndarray
        Width of the rectangular load [m].
    L : float or np.ndarray
        Length of the rectangular load [m].
    x_rel : float or np.ndarray
        Horizontal distance from the center of the load [m].
    z : float or np.ndarray
        Depth below the surface [m].

    Returns
    -------
    float or np.ndarray
        Vertical stress increment [kPa].
    """
    q_arr = np.atleast_1d(np.asarray(q, dtype=float))
    B_arr = np.atleast_1d(np.asarray(B, dtype=float))
    L_arr = np.atleast_1d(np.asarray(L, dtype=float))
    x_rel_arr = np.atleast_1d(np.asarray(x_rel, dtype=float))
    z_arr = np.atleast_1d(np.asarray(z, dtype=float))

    shape = np.broadcast_shapes(
        q_arr.shape, B_arr.shape, L_arr.shape, x_rel_arr.shape, z_arr.shape
    )
    q_b = np.broadcast_to(q_arr, shape)
    B_b = np.broadcast_to(B_arr, shape)
    L_b = np.broadcast_to(L_arr, shape)
    x_rel_b = np.broadcast_to(x_rel_arr, shape)
    z_b = np.broadcast_to(z_arr, shape)

    out = np.zeros(shape, dtype=float)

    y_half = L_b / 2.0
    abs_x = np.abs(x_rel_b)

    mask_in = abs_x <= B_b / 2.0

    if np.any(mask_in):
        b1 = B_b[mask_in] / 2.0 - abs_x[mask_in]
        b2 = B_b[mask_in] / 2.0 + abs_x[mask_in]
        y_h = y_half[mask_in]
        z_v = z_b[mask_in]

        iz1 = np.asarray(fadum_corner_stress(b1, y_h, z_v))
        iz2 = np.asarray(fadum_corner_stress(b2, y_h, z_v))

        Iz = 2.0 * (iz1 + iz2)
        out[mask_in] = np.maximum(0.0, q_b[mask_in] * Iz)

    mask_out = ~mask_in
    if np.any(mask_out):
        b_far = abs_x[mask_out] + B_b[mask_out] / 2.0
        b_near = abs_x[mask_out] - B_b[mask_out] / 2.0
        y_h = y_half[mask_out]
        z_v = z_b[mask_out]

        iz_far = np.asarray(fadum_corner_stress(b_far, y_h, z_v))
        iz_near = np.asarray(fadum_corner_stress(b_near, y_h, z_v))

        Iz = 2.0 * (iz_far - iz_near)
        out[mask_out] = np.maximum(0.0, q_b[mask_out] * Iz)

    if (
        np.isscalar(q)
        and np.isscalar(B)
        and np.isscalar(L)
        and np.isscalar(x_rel)
        and np.isscalar(z)
    ):
        return float(out.item())
    elif out.ndim == 0:
        return float(out)
    return out


def compute_load_stress_increment(
    load: LoadGeometry,
    x_rel: float | np.ndarray,
    z: float | np.ndarray,
    method: StressMethod = StressMethod.BOUSSINESQ,
) -> float | np.ndarray:
    """
    Compute vertical stress increment delta_sigma_z under a specific surface load geometry.

    Parameters
    ----------
    load : LoadGeometry
        The load geometry definition.
    x_rel : float or np.ndarray
        Horizontal distance from the load's center [m].
    z : float or np.ndarray
        Depth below the surface [m].
    method : StressMethod, optional
        The stress distribution method to apply. Default is StressMethod.BOUSSINESQ.

    Returns
    -------
    float or np.ndarray
        Vertical stress increment [kPa].

    Raises
    ------
    NotImplementedError
        If `method` is `StressMethod.WESTERGAARD`.
    ValueError
        If `method` is not a recognized `StressMethod`.
    """
    q = max(0.0, float(load.stress_q))
    B = max(0.1, float(load.width_B))

    x_rel_arr = np.atleast_1d(np.asarray(x_rel, dtype=float))
    z_arr = np.atleast_1d(np.asarray(z, dtype=float))

    shape = np.broadcast_shapes(x_rel_arr.shape, z_arr.shape)
    x_rel_b = np.broadcast_to(x_rel_arr, shape)
    z_b = np.broadcast_to(z_arr, shape)

    depth = np.maximum(0.01, z_b + load.z_surface_offset)

    out = np.zeros(shape, dtype=float)

    if method == StressMethod.TWO_TO_ONE:
        if load.type == LoadType.STRIP:
            mask = np.abs(x_rel_b) <= (B + depth) / 2.0
            out[mask] = (q * B) / (B + depth[mask])
            out[~mask] = 0.0
        else:
            L = max(0.1, float(load.length_L))
            mask = np.abs(x_rel_b) <= (B + depth) / 2.0
            out[mask] = (q * B * L) / ((B + depth[mask]) * (L + depth[mask]))
            out[~mask] = 0.0

    elif method == StressMethod.BOUSSINESQ:
        if load.type == LoadType.STRIP:
            out = boussinesq_strip_stress(q, B, x_rel_b, depth)
        else:
            L = max(0.1, float(load.length_L))
            out = boussinesq_rectangular_stress(q, B, L, x_rel_b, depth)

    elif method == StressMethod.WESTERGAARD:
        raise NotImplementedError("Westergaard method not yet implemented.")
    else:
        raise ValueError(f"Unsupported stress method: {method}")

    out = np.asarray(out)
    if np.isscalar(x_rel) and np.isscalar(z):
        if out.ndim == 0:
            return float(out)
        return float(out.item())
    elif out.ndim == 0:
        return float(out)
    return out


def compute_stress_profile_under_loads(
    loads: list[LoadGeometry],
    z_points: NDArray[np.float64],
    x_eval: float = 0.0,
    method: StressMethod = StressMethod.BOUSSINESQ,
) -> NDArray[np.float64]:
    """
    Compute 1D vertical stress increment profile over a depth grid at a specific x coordinate.

    Parameters
    ----------
    loads : list[LoadGeometry]
        List of surface loads.
    z_points : NDArray[np.float64]
        Array of depths [m].
    x_eval : float, optional
        Absolute x-coordinate for evaluation [m]. Default is 0.0.
    method : StressMethod, optional
        Stress distribution method. Default is StressMethod.BOUSSINESQ.

    Returns
    -------
    NDArray[np.float64]
        Array of stress increments [kPa] corresponding to z_points.
    """
    delta_sigma_z = np.zeros_like(z_points, dtype=np.float64)
    for load in loads:
        x_rel = x_eval - load.x_center
        for idx, z in enumerate(z_points):
            delta_sigma_z[idx] += compute_load_stress_increment(load, x_rel, z, method)
    return delta_sigma_z


def compute_stress_heatmap(
    loads: list[LoadGeometry],
    z_points: NDArray[np.float64],
    x_points: NDArray[np.float64],
    method: StressMethod = StressMethod.BOUSSINESQ,
) -> NDArray[np.float64]:
    """
    Compute a 2D grid of stress ratios (delta sigma / primary load q).

    Parameters
    ----------
    loads : list[LoadGeometry]
        List of surface loads.
    z_points : NDArray[np.float64]
        Array of depths [m] (rows).
    x_points : NDArray[np.float64]
        Array of x-coordinates [m] (columns).
    method : StressMethod, optional
        Stress distribution method. Default is StressMethod.BOUSSINESQ.

    Returns
    -------
    NDArray[np.float64]
        2D array of stress ratios. Shape: (len(z_points), len(x_points)).
    """
    primary_q = loads[0].stress_q if loads else 100.0

    if len(z_points) == 0 or len(x_points) == 0:
        return np.zeros((len(z_points), len(x_points)), dtype=np.float64)

    Z, X = np.meshgrid(z_points, x_points, indexing="ij")

    ds_sum = np.zeros_like(Z, dtype=np.float64)
    for load in loads:
        X_rel = X - load.x_center
        ds_sum += np.asarray(compute_load_stress_increment(load, X_rel, Z, method))

    return ds_sum / max(1.0, float(primary_q))
