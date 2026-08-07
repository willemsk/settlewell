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
    b = np.asarray(b)
    l_dim = np.asarray(l_dim)
    z = np.asarray(z)

    # Broadcast shapes
    b, l_dim, z = np.broadcast_arrays(b, l_dim, z)

    out = np.zeros_like(b, dtype=float)

    mask_z = z <= 1e-6
    out[mask_z] = 0.25

    mask_zero = (~mask_z) & ((b <= 1e-6) | (l_dim <= 1e-6))
    out[mask_zero] = 0.0

    calc_mask = ~(mask_z | mask_zero)

    if np.any(calc_mask):
        bz = b[calc_mask]
        lz = l_dim[calc_mask]
        zz = z[calc_mask]

        m = bz / zz
        n = lz / zz
        m2 = m * m
        n2 = n * n
        v = m2 + n2 + 1.0
        v_mn = m2 * n2

        sqrt_v = np.sqrt(v)
        term1 = (2.0 * m * n * sqrt_v / (v + v_mn)) * ((v + 1.0) / v)
        arg2 = (2.0 * m * n * sqrt_v) / (v - v_mn)

        v_diff = v - v_mn

        arg2_val = np.empty_like(arg2)

        mask_eq = np.abs(v_diff) < 1e-12
        mask_lt = v_diff < 0
        mask_other = ~(mask_eq | mask_lt)

        arg2_val[mask_eq] = np.pi / 2.0
        arg2_val[mask_lt] = np.arctan(arg2[mask_lt]) + np.pi
        arg2_val[mask_other] = np.arctan(arg2[mask_other])

        out[calc_mask] = (1.0 / (4.0 * np.pi)) * (term1 + arg2_val)

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
    q = np.asarray(q)
    B = np.asarray(B)
    x_rel = np.asarray(x_rel)
    z = np.asarray(z)

    # Broadcast
    q, B, x_rel, z = np.broadcast_arrays(q, B, x_rel, z)

    out = np.zeros_like(x_rel, dtype=float)

    mask_z = z <= 1e-6
    mask_in = np.abs(x_rel) <= B / 2.0

    mask_z_in = mask_z & mask_in
    if np.any(mask_z_in):
        out[mask_z_in] = q[mask_z_in] if q.ndim > 0 else q

    calc_mask = ~mask_z

    if np.any(calc_mask):
        x_r = x_rel[calc_mask]
        z_c = z[calc_mask]
        q_c = q[calc_mask] if q.ndim > 0 else q
        B_c = B[calc_mask] if B.ndim > 0 else B

        x_L = x_r - B_c / 2.0
        x_R = x_r + B_c / 2.0

        alpha = np.arctan(x_R / z_c) - np.arctan(x_L / z_c)
        out[calc_mask] = (q_c / np.pi) * (alpha + np.sin(alpha) * np.cos(alpha))

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
    q = np.asarray(q)
    B = np.asarray(B)
    L = np.asarray(L)
    x_rel = np.asarray(x_rel)
    z = np.asarray(z)

    # Broadcast shapes
    q, B, L, x_rel, z = np.broadcast_arrays(q, B, L, x_rel, z)

    y_half = L / 2.0
    abs_x_rel = np.abs(x_rel)
    B_half = B / 2.0

    Iz = np.zeros_like(x_rel, dtype=float)

    mask_inside = abs_x_rel <= B_half

    if np.any(mask_inside):
        b1 = (B_half if B_half.ndim == 0 else B_half[mask_inside]) - abs_x_rel[
            mask_inside
        ]
        b2 = (B_half if B_half.ndim == 0 else B_half[mask_inside]) + abs_x_rel[
            mask_inside
        ]
        y_in = y_half if y_half.ndim == 0 else y_half[mask_inside]
        z_in = z if z.ndim == 0 else z[mask_inside]
        Iz[mask_inside] = 2.0 * (
            fadum_corner_stress(b1, y_in, z_in) + fadum_corner_stress(b2, y_in, z_in)
        )

    mask_outside = ~mask_inside
    if np.any(mask_outside):
        b_far = abs_x_rel[mask_outside] + (
            B_half if B_half.ndim == 0 else B_half[mask_outside]
        )
        b_near = abs_x_rel[mask_outside] - (
            B_half if B_half.ndim == 0 else B_half[mask_outside]
        )
        y_out = y_half if y_half.ndim == 0 else y_half[mask_outside]
        z_out = z if z.ndim == 0 else z[mask_outside]
        Iz[mask_outside] = 2.0 * (
            fadum_corner_stress(b_far, y_out, z_out)
            - fadum_corner_stress(b_near, y_out, z_out)
        )

    out = np.maximum(0.0, q * Iz)
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
    x_rel = np.asarray(x_rel)
    z = np.asarray(z)

    # Broadcast x_rel and z
    x_rel, z = np.broadcast_arrays(x_rel, z)

    q = max(0.0, float(load.stress_q))
    B = max(0.1, float(load.width_B))
    depth = np.maximum(0.01, z + load.z_surface_offset)

    if method == StressMethod.TWO_TO_ONE:
        if load.type == LoadType.STRIP:
            mask = np.abs(x_rel) <= (B + depth) / 2.0
            out = np.zeros_like(x_rel, dtype=float)
            if np.any(mask):
                depth_m = depth[mask] if depth.ndim > 0 else depth
                out[mask] = (q * B) / (B + depth_m)
            if out.ndim == 0:
                return float(out)
            return out
        else:
            L = max(0.1, float(load.length_L))
            mask = np.abs(x_rel) <= (B + depth) / 2.0
            out = np.zeros_like(x_rel, dtype=float)
            if np.any(mask):
                depth_m = depth[mask] if depth.ndim > 0 else depth
                out[mask] = (q * B * L) / ((B + depth_m) * (L + depth_m))
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
        delta_sigma_z += compute_load_stress_increment(load, x_rel, z_points, method)
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
    heatmap = np.zeros((len(z_points), len(x_points)), dtype=np.float64)
    primary_q = loads[0].stress_q if loads else 100.0

    X, Z = np.meshgrid(x_points, z_points)

    for load in loads:
        x_rel = X - load.x_center
        heatmap += compute_load_stress_increment(load, x_rel, Z, method)

    return heatmap / max(1.0, float(primary_q))
