import math
import numpy as np
from numpy.typing import NDArray

from settlewell.models import LoadGeometry, LoadType, StressMethod


def fadum_corner_stress(
    b: float | NDArray[np.float64],
    l_dim: float | NDArray[np.float64],
    z: float | NDArray[np.float64],
) -> float | NDArray[np.float64]:
    """
    Calculate Fadum (1948) corner stress influence value Iz for a rectangle b x l_dim at depth z.

    Parameters
    ----------
    b : float or NDArray[np.float64]
        Width of the rectangular area [m].
    l_dim : float or NDArray[np.float64]
        Length of the rectangular area [m].
    z : float or NDArray[np.float64]
        Depth below the loaded area [m].

    Returns
    -------
    float or NDArray[np.float64]
        Vertical stress influence factor Iz [-].
    """
    if (
        not isinstance(b, np.ndarray)
        and not isinstance(l_dim, np.ndarray)
        and not isinstance(z, np.ndarray)
    ):
        if z <= 1e-6:
            return 0.25
        if b <= 1e-6 or l_dim <= 1e-6:
            return 0.0

        m = b / z
        n = l_dim / z
        m2 = m * m
        n2 = n * n
        v = m2 + n2 + 1.0
        v_mn = m2 * n2

        term1 = (2.0 * m * n * math.sqrt(v) / (v + v_mn)) * ((v + 1.0) / v)
        arg2 = (2.0 * m * n * math.sqrt(v)) / (v - v_mn)

        if abs(v - v_mn) < 1e-12:
            arg2_val = math.pi / 2.0
        elif v - v_mn < 0:
            arg2_val = math.atan(arg2) + math.pi
        else:
            arg2_val = math.atan(arg2)

        return float((1.0 / (4.0 * math.pi)) * (term1 + arg2_val))

    b_arr = np.asarray(b, dtype=float)
    l_dim_arr = np.asarray(l_dim, dtype=float)
    z_arr = np.asarray(z, dtype=float)

    b_arr, l_dim_arr, z_arr = np.broadcast_arrays(b_arr, l_dim_arr, z_arr)

    out = np.zeros(b_arr.shape, dtype=float)

    mask_z = z_arr <= 1e-6
    mask_dim = (b_arr <= 1e-6) | (l_dim_arr <= 1e-6)

    out[mask_z] = 0.25
    out[mask_dim & ~mask_z] = 0.0

    mask = ~mask_z & ~mask_dim
    if not np.any(mask):
        return float(out) if out.ndim == 0 else out

    b_m = b_arr[mask]
    l_m = l_dim_arr[mask]
    z_m = z_arr[mask]

    m = b_m / z_m
    n = l_m / z_m

    m2 = m * m
    n2 = n * n
    v = m2 + n2 + 1.0
    v_mn = m2 * n2

    term1 = (2.0 * m * n * np.sqrt(v) / (v + v_mn)) * ((v + 1.0) / v)

    with np.errstate(divide="ignore", invalid="ignore"):
        arg2 = (2.0 * m * n * np.sqrt(v)) / (v - v_mn)

    arg2_val = np.empty_like(arg2)
    mask_eq = np.abs(v - v_mn) < 1e-12
    mask_lt = (v - v_mn) < 0
    mask_gt = ~mask_eq & ~mask_lt

    arg2_val[mask_eq] = np.pi / 2.0
    arg2_val[mask_lt] = np.arctan(arg2[mask_lt]) + np.pi
    arg2_val[mask_gt] = np.arctan(arg2[mask_gt])

    out[mask] = (1.0 / (4.0 * np.pi)) * (term1 + arg2_val)
    return float(out) if out.ndim == 0 else out


def boussinesq_strip_stress(
    q: float | NDArray[np.float64],
    B: float | NDArray[np.float64],
    x_rel: float | NDArray[np.float64],
    z: float | NDArray[np.float64],
) -> float | NDArray[np.float64]:
    """
    Calculate vertical stress increment under a Boussinesq strip load.

    Parameters
    ----------
    q : float or NDArray[np.float64]
        Applied uniform stress [kPa].
    B : float or NDArray[np.float64]
        Width of the strip load [m].
    x_rel : float or NDArray[np.float64]
        Horizontal distance from the center of the strip [m].
    z : float or NDArray[np.float64]
        Depth below the load [m].

    Returns
    -------
    float or NDArray[np.float64]
        Vertical stress increment [kPa].
    """
    if (
        not isinstance(q, np.ndarray)
        and not isinstance(B, np.ndarray)
        and not isinstance(x_rel, np.ndarray)
        and not isinstance(z, np.ndarray)
    ):
        if z <= 1e-6:
            if abs(x_rel) <= B / 2.0:
                return float(q)
            return 0.0

        x_L = x_rel - B / 2.0
        x_R = x_rel + B / 2.0

        alpha = math.atan(x_R / z) - math.atan(x_L / z)
        return float((q / math.pi) * (alpha + math.sin(alpha) * math.cos(alpha)))

    q_arr = np.asarray(q, dtype=float)
    B_arr = np.asarray(B, dtype=float)
    x_rel_arr = np.asarray(x_rel, dtype=float)
    z_arr = np.asarray(z, dtype=float)

    q_arr, B_arr, x_rel_arr, z_arr = np.broadcast_arrays(q_arr, B_arr, x_rel_arr, z_arr)

    out = np.zeros(q_arr.shape, dtype=float)

    mask_z = z_arr <= 1e-6
    abs_x = np.abs(x_rel_arr)
    B_half = B_arr / 2.0

    mask_in = abs_x <= B_half

    out[mask_z & mask_in] = q_arr[mask_z & mask_in]
    out[mask_z & ~mask_in] = 0.0

    mask = ~mask_z
    if not np.any(mask):
        return float(out) if out.ndim == 0 else out

    x_rel_m = x_rel_arr[mask]
    z_m = z_arr[mask]
    B_half_m = B_half[mask]
    q_m = q_arr[mask]

    x_L = x_rel_m - B_half_m
    x_R = x_rel_m + B_half_m

    alpha = np.arctan(x_R / z_m) - np.arctan(x_L / z_m)
    out[mask] = (q_m / np.pi) * (alpha + np.sin(alpha) * np.cos(alpha))

    return float(out) if out.ndim == 0 else out


def boussinesq_rectangular_stress(
    q: float | NDArray[np.float64],
    B: float | NDArray[np.float64],
    L: float | NDArray[np.float64],
    x_rel: float | NDArray[np.float64],
    z: float | NDArray[np.float64],
) -> float | NDArray[np.float64]:
    """
    Calculate vertical stress increment under a Boussinesq rectangular load.

    Parameters
    ----------
    q : float or NDArray[np.float64]
        Applied uniform stress [kPa].
    B : float or NDArray[np.float64]
        Width of the rectangular load [m].
    L : float or NDArray[np.float64]
        Length of the rectangular load [m].
    x_rel : float or NDArray[np.float64]
        Horizontal distance from the center of the load [m].
    z : float or NDArray[np.float64]
        Depth below the surface [m].

    Returns
    -------
    float or NDArray[np.float64]
        Vertical stress increment [kPa].
    """
    if (
        not isinstance(q, np.ndarray)
        and not isinstance(B, np.ndarray)
        and not isinstance(L, np.ndarray)
        and not isinstance(x_rel, np.ndarray)
        and not isinstance(z, np.ndarray)
    ):
        y_half = L / 2.0
        if abs(x_rel) <= B / 2.0:
            b1 = B / 2.0 - abs(x_rel)
            b2 = B / 2.0 + abs(x_rel)
            Iz = 2.0 * (
                fadum_corner_stress(b1, y_half, z) + fadum_corner_stress(b2, y_half, z)
            )
        else:
            b_far = abs(x_rel) + B / 2.0
            b_near = abs(x_rel) - B / 2.0
            Iz = 2.0 * (
                fadum_corner_stress(b_far, y_half, z)
                - fadum_corner_stress(b_near, y_half, z)
            )
        return max(0.0, float(q * Iz))

    q_arr = np.asarray(q, dtype=float)
    B_arr = np.asarray(B, dtype=float)
    L_arr = np.asarray(L, dtype=float)
    x_rel_arr = np.asarray(x_rel, dtype=float)
    z_arr = np.asarray(z, dtype=float)

    q_arr, B_arr, L_arr, x_rel_arr, z_arr = np.broadcast_arrays(
        q_arr, B_arr, L_arr, x_rel_arr, z_arr
    )

    y_half = L_arr / 2.0
    abs_x = np.abs(x_rel_arr)
    B_half = B_arr / 2.0

    mask_in = abs_x <= B_half
    mask_out = ~mask_in

    Iz = np.zeros(q_arr.shape, dtype=float)

    if np.any(mask_in):
        b1 = B_half[mask_in] - abs_x[mask_in]
        b2 = B_half[mask_in] + abs_x[mask_in]
        z_in = z_arr[mask_in]
        y_in = y_half[mask_in]
        Iz[mask_in] = 2.0 * (
            fadum_corner_stress(b1, y_in, z_in) + fadum_corner_stress(b2, y_in, z_in)
        )

    if np.any(mask_out):
        b_far = abs_x[mask_out] + B_half[mask_out]
        b_near = abs_x[mask_out] - B_half[mask_out]
        z_out = z_arr[mask_out]
        y_out = y_half[mask_out]
        Iz[mask_out] = 2.0 * (
            fadum_corner_stress(b_far, y_out, z_out)
            - fadum_corner_stress(b_near, y_out, z_out)
        )

    out = np.maximum(0.0, q_arr * Iz)
    return float(out) if out.ndim == 0 else out


def compute_load_stress_increment(
    load: LoadGeometry,
    x_rel: float | NDArray[np.float64],
    z: float | NDArray[np.float64],
    method: StressMethod = StressMethod.BOUSSINESQ,
) -> float | NDArray[np.float64]:
    """
    Compute vertical stress increment delta_sigma_z under a specific surface load geometry.

    Parameters
    ----------
    load : LoadGeometry
        The load geometry definition.
    x_rel : float or NDArray[np.float64]
        Horizontal distance from the load's center [m].
    z : float or NDArray[np.float64]
        Depth below the surface [m].
    method : StressMethod, optional
        The stress distribution method to apply. Default is StressMethod.BOUSSINESQ.

    Returns
    -------
    float or NDArray[np.float64]
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

    is_scalar = not isinstance(x_rel, np.ndarray) and not isinstance(z, np.ndarray)

    if is_scalar:
        depth = max(0.01, float(z + load.z_surface_offset))
        if method == StressMethod.TWO_TO_ONE:
            if load.type == LoadType.STRIP:
                if abs(x_rel) <= (B + depth) / 2.0:
                    return float((q * B) / (B + depth))
                return 0.0
            else:
                L = max(0.1, float(load.length_L))
                if abs(x_rel) <= (B + depth) / 2.0:
                    return float((q * B * L) / ((B + depth) * (L + depth)))
                return 0.0
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

    x_rel_arr = np.asarray(x_rel, dtype=float)
    z_arr = np.asarray(z, dtype=float)
    x_rel_arr, z_arr = np.broadcast_arrays(x_rel_arr, z_arr)

    depth = np.maximum(0.01, z_arr + load.z_surface_offset)

    if method == StressMethod.TWO_TO_ONE:
        out = np.zeros(depth.shape, dtype=float)
        if load.type == LoadType.STRIP:
            mask = np.abs(x_rel_arr) <= (B + depth) / 2.0
            out[mask] = (q * B) / (B + depth[mask])
        else:
            L = max(0.1, float(load.length_L))
            mask = np.abs(x_rel_arr) <= (B + depth) / 2.0
            d_m = depth[mask]
            out[mask] = (q * B * L) / ((B + d_m) * (L + d_m))
        return float(out) if out.ndim == 0 else out

    elif method == StressMethod.BOUSSINESQ:
        if load.type == LoadType.STRIP:
            return boussinesq_strip_stress(q, B, x_rel_arr, depth)
        else:
            L = max(0.1, float(load.length_L))
            return boussinesq_rectangular_stress(q, B, L, x_rel_arr, depth)

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
        x_rels = X - load.x_center
        heatmap += compute_load_stress_increment(load, x_rels, Z, method)

    return heatmap / max(1.0, float(primary_q))
