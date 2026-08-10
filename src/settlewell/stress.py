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
    b : float | np.ndarray
        Width of the rectangular area [m].
    l_dim : float | np.ndarray
        Length of the rectangular area [m].
    z : float | np.ndarray
        Depth below the loaded area [m].

    Returns
    -------
    float | np.ndarray
        Vertical stress influence factor Iz [-].
    """
    b = np.asarray(b, dtype=np.float64)
    l_dim = np.asarray(l_dim, dtype=np.float64)
    z = np.asarray(z, dtype=np.float64)

    shape = np.broadcast_shapes(b.shape, l_dim.shape, z.shape)
    b = np.broadcast_to(b, shape)
    l_dim = np.broadcast_to(l_dim, shape)
    z = np.broadcast_to(z, shape)

    out = np.zeros(shape, dtype=np.float64)

    z_small = z <= 1e-6
    b_l_small = (b <= 1e-6) | (l_dim <= 1e-6)

    mask = ~(z_small | b_l_small)

    if np.any(mask):
        bm = b[mask]
        lm = l_dim[mask]
        zm = z[mask]

        m = bm / zm
        n = lm / zm
        m2 = m * m
        n2 = n * n
        v = m2 + n2 + 1.0
        v_mn = m2 * n2

        term1 = (2.0 * m * n * np.sqrt(v) / (v + v_mn)) * ((v + 1.0) / v)

        with np.errstate(divide="ignore", invalid="ignore"):
            arg2 = (2.0 * m * n * np.sqrt(v)) / (v - v_mn)

        diff = v - v_mn
        arg2_val = np.empty_like(arg2)

        diff_zero = np.abs(diff) < 1e-12
        diff_neg = diff < 0
        diff_pos = ~(diff_zero | diff_neg)

        arg2_val[diff_zero] = np.pi / 2.0
        arg2_val[diff_neg] = np.arctan(arg2[diff_neg]) + np.pi
        arg2_val[diff_pos] = np.arctan(arg2[diff_pos])

        out[mask] = (1.0 / (4.0 * np.pi)) * (term1 + arg2_val)

    out[z_small] = 0.25
    out[b_l_small & ~z_small] = 0.0

    if out.ndim == 0:
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
    q : float | np.ndarray
        Applied uniform stress [kPa].
    B : float | np.ndarray
        Width of the strip load [m].
    x_rel : float | np.ndarray
        Horizontal distance from the center of the strip [m].
    z : float | np.ndarray
        Depth below the load [m].

    Returns
    -------
    float | np.ndarray
        Vertical stress increment [kPa].
    """
    q = np.asarray(q, dtype=np.float64)
    B = np.asarray(B, dtype=np.float64)
    x_rel = np.asarray(x_rel, dtype=np.float64)
    z = np.asarray(z, dtype=np.float64)

    shape = np.broadcast_shapes(q.shape, B.shape, x_rel.shape, z.shape)
    q = np.broadcast_to(q, shape)
    B = np.broadcast_to(B, shape)
    x_rel = np.broadcast_to(x_rel, shape)
    z = np.broadcast_to(z, shape)

    out = np.zeros(shape, dtype=np.float64)

    z_small = z <= 1e-6
    mask = ~z_small

    if np.any(mask):
        qm = q[mask]
        Bm = B[mask]
        xm = x_rel[mask]
        zm = z[mask]

        x_L = xm - Bm / 2.0
        x_R = xm + Bm / 2.0

        alpha = np.arctan(x_R / zm) - np.arctan(x_L / zm)
        out[mask] = (qm / np.pi) * (alpha + np.sin(alpha) * np.cos(alpha))

    if np.any(z_small):
        x_small_z = x_rel[z_small]
        B_small_z = B[z_small]
        cond = np.abs(x_small_z) <= B_small_z / 2.0

        out_z_small = np.zeros_like(x_small_z)
        out_z_small[cond] = q[z_small][cond]
        out[z_small] = out_z_small

    if out.ndim == 0:
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
    q : float | np.ndarray
        Applied uniform stress [kPa].
    B : float | np.ndarray
        Width of the rectangular load [m].
    L : float | np.ndarray
        Length of the rectangular load [m].
    x_rel : float | np.ndarray
        Horizontal distance from the center of the load [m].
    z : float | np.ndarray
        Depth below the surface [m].

    Returns
    -------
    float | np.ndarray
        Vertical stress increment [kPa].
    """
    q = np.asarray(q, dtype=np.float64)
    B = np.asarray(B, dtype=np.float64)
    L = np.asarray(L, dtype=np.float64)
    x_rel = np.asarray(x_rel, dtype=np.float64)
    z = np.asarray(z, dtype=np.float64)

    shape = np.broadcast_shapes(q.shape, B.shape, L.shape, x_rel.shape, z.shape)
    q = np.broadcast_to(q, shape)
    B = np.broadcast_to(B, shape)
    L = np.broadcast_to(L, shape)
    x_rel = np.broadcast_to(x_rel, shape)
    z = np.broadcast_to(z, shape)

    out = np.zeros(shape, dtype=np.float64)

    y_half = L / 2.0
    abs_x = np.abs(x_rel)
    half_B = B / 2.0

    inside = abs_x <= half_B
    outside = ~inside

    if np.any(inside):
        b1 = half_B[inside] - abs_x[inside]
        b2 = half_B[inside] + abs_x[inside]
        yh = y_half[inside]
        zi = z[inside]

        Iz = 2.0 * (fadum_corner_stress(b1, yh, zi) + fadum_corner_stress(b2, yh, zi))
        out[inside] = q[inside] * Iz

    if np.any(outside):
        b_far = abs_x[outside] + half_B[outside]
        b_near = abs_x[outside] - half_B[outside]
        yh = y_half[outside]
        zo = z[outside]

        Iz = 2.0 * (
            fadum_corner_stress(b_far, yh, zo) - fadum_corner_stress(b_near, yh, zo)
        )
        out[outside] = q[outside] * Iz

    out = np.maximum(0.0, out)

    if out.ndim == 0:
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
    x_rel : float | np.ndarray
        Horizontal distance from the load's center [m].
    z : float | np.ndarray
        Depth below the surface [m].
    method : StressMethod, optional
        The stress distribution method to apply. Default is StressMethod.BOUSSINESQ.

    Returns
    -------
    float | np.ndarray
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

    z = np.asarray(z, dtype=np.float64)
    x_rel = np.asarray(x_rel, dtype=np.float64)

    depth = np.maximum(0.01, z + load.z_surface_offset)

    if method == StressMethod.TWO_TO_ONE:
        if load.type == LoadType.STRIP:
            cond = np.abs(x_rel) <= (B + depth) / 2.0
            out = np.zeros_like(x_rel, dtype=np.float64)
            out[cond] = (q * B) / (B + depth[cond])

            if out.ndim == 0:
                return float(out)
            return out
        else:
            L = max(0.1, float(load.length_L))
            cond = np.abs(x_rel) <= (B + depth) / 2.0
            out = np.zeros_like(x_rel, dtype=np.float64)
            out[cond] = (q * B * L) / ((B + depth[cond]) * (L + depth[cond]))

            if out.ndim == 0:
                return float(out)
            return out

    elif method == StressMethod.BOUSSINESQ:
        if load.type == LoadType.STRIP:
            return boussinesq_strip_stress(q, B, x_rel, depth)
        else:
            L = max(0.1, float(load.length_L))
            return boussinesq_rectangular_stress(q, B, L, x_rel, depth)

    elif method == StressMethod.WESTERGAARD:
        raise NotImplementedError("Westergaard method not yet implemented.")
    else:
        raise ValueError(f"Unsupported stress method: {method}")


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

    Z, X = np.meshgrid(z_points, x_points, indexing="ij")
    heatmap = np.zeros_like(Z, dtype=np.float64)

    for load in loads:
        X_rel = X - load.x_center
        heatmap += compute_load_stress_increment(load, X_rel, Z, method)

    return heatmap / max(1.0, float(primary_q))
