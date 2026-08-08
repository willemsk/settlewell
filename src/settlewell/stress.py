import math
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
    b : float or numpy.ndarray
        Width of the rectangular area [m].
    l_dim : float or numpy.ndarray
        Length of the rectangular area [m].
    z : float or numpy.ndarray
        Depth below the loaded area [m].

    Returns
    -------
    float or numpy.ndarray
        Vertical stress influence factor Iz [-].
    """
    is_scalar = np.isscalar(b) and np.isscalar(l_dim) and np.isscalar(z)
    if is_scalar:
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

    b_arr = np.asarray(b)
    l_dim_arr = np.asarray(l_dim)
    z_arr = np.asarray(z)

    b_shapes = np.broadcast_shapes(b_arr.shape, l_dim_arr.shape, z_arr.shape)
    b_arr = np.broadcast_to(b_arr, b_shapes)
    l_dim_arr = np.broadcast_to(l_dim_arr, b_shapes)
    z_arr = np.broadcast_to(z_arr, b_shapes)

    z_safe = np.where(z_arr > 1e-6, z_arr, 1.0)

    m = b_arr / z_safe
    n = l_dim_arr / z_safe
    m2 = m * m
    n2 = n * n
    v = m2 + n2 + 1.0
    v_mn = m2 * n2

    term1 = (2.0 * m * n * np.sqrt(v) / (v + v_mn)) * ((v + 1.0) / v)

    with np.errstate(divide="ignore", invalid="ignore"):
        arg2 = (2.0 * m * n * np.sqrt(v)) / (v - v_mn)

    v_minus_v_mn = v - v_mn
    arg2_val = np.empty_like(term1)

    cond1 = np.abs(v_minus_v_mn) < 1e-12
    cond2 = (~cond1) & (v_minus_v_mn < 0)
    cond3 = (~cond1) & (v_minus_v_mn >= 0)

    arg2_val[cond1] = np.pi / 2.0
    arg2_val[cond2] = np.arctan(arg2[cond2]) + np.pi
    arg2_val[cond3] = np.arctan(arg2[cond3])

    result = (1.0 / (4.0 * np.pi)) * (term1 + arg2_val)

    z_mask = z_arr <= 1e-6
    bl_mask = (b_arr <= 1e-6) | (l_dim_arr <= 1e-6)

    result = np.where(z_mask, 0.25, result)
    result = np.where(~z_mask & bl_mask, 0.0, result)

    if result.ndim == 0:
        return float(result)
    return result


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
    q : float or numpy.ndarray
        Applied uniform stress [kPa].
    B : float or numpy.ndarray
        Width of the strip load [m].
    x_rel : float or numpy.ndarray
        Horizontal distance from the center of the strip [m].
    z : float or numpy.ndarray
        Depth below the load [m].

    Returns
    -------
    float or numpy.ndarray
        Vertical stress increment [kPa].
    """
    is_scalar = (
        np.isscalar(q) and np.isscalar(B) and np.isscalar(x_rel) and np.isscalar(z)
    )
    if is_scalar:
        if z <= 1e-6:
            if abs(x_rel) <= B / 2.0:
                return float(q)
            return 0.0

        x_L = x_rel - B / 2.0
        x_R = x_rel + B / 2.0

        alpha = math.atan(x_R / z) - math.atan(x_L / z)
        return float((q / math.pi) * (alpha + math.sin(alpha) * math.cos(alpha)))

    q_arr = np.asarray(q)
    B_arr = np.asarray(B)
    x_rel_arr = np.asarray(x_rel)
    z_arr = np.asarray(z)

    b_shapes = np.broadcast_shapes(
        q_arr.shape, B_arr.shape, x_rel_arr.shape, z_arr.shape
    )
    q_arr = np.broadcast_to(q_arr, b_shapes)
    B_arr = np.broadcast_to(B_arr, b_shapes)
    x_rel_arr = np.broadcast_to(x_rel_arr, b_shapes)
    z_arr = np.broadcast_to(z_arr, b_shapes)

    x_L = x_rel_arr - B_arr / 2.0
    x_R = x_rel_arr + B_arr / 2.0

    z_safe = np.where(z_arr > 1e-6, z_arr, 1.0)
    alpha = np.arctan(x_R / z_safe) - np.arctan(x_L / z_safe)

    result = (q_arr / np.pi) * (alpha + np.sin(alpha) * np.cos(alpha))

    z_mask = z_arr <= 1e-6
    x_mask = np.abs(x_rel_arr) <= B_arr / 2.0

    result = np.where(z_mask & x_mask, q_arr, result)
    result = np.where(z_mask & ~x_mask, 0.0, result)

    if result.ndim == 0:
        return float(result)
    return result


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
    q : float or numpy.ndarray
        Applied uniform stress [kPa].
    B : float or numpy.ndarray
        Width of the rectangular load [m].
    L : float or numpy.ndarray
        Length of the rectangular load [m].
    x_rel : float or numpy.ndarray
        Horizontal distance from the center of the load [m].
    z : float or numpy.ndarray
        Depth below the surface [m].

    Returns
    -------
    float or numpy.ndarray
        Vertical stress increment [kPa].
    """
    is_scalar = (
        np.isscalar(q)
        and np.isscalar(B)
        and np.isscalar(L)
        and np.isscalar(x_rel)
        and np.isscalar(z)
    )
    if is_scalar:
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

    q_arr = np.asarray(q)
    B_arr = np.asarray(B)
    L_arr = np.asarray(L)
    x_rel_arr = np.asarray(x_rel)
    z_arr = np.asarray(z)

    b_shapes = np.broadcast_shapes(
        q_arr.shape, B_arr.shape, L_arr.shape, x_rel_arr.shape, z_arr.shape
    )
    q_arr = np.broadcast_to(q_arr, b_shapes)
    B_arr = np.broadcast_to(B_arr, b_shapes)
    L_arr = np.broadcast_to(L_arr, b_shapes)
    x_rel_arr = np.broadcast_to(x_rel_arr, b_shapes)
    z_arr = np.broadcast_to(z_arr, b_shapes)

    y_half = L_arr / 2.0
    abs_x_rel = np.abs(x_rel_arr)
    B_half = B_arr / 2.0

    inside_mask = abs_x_rel <= B_half

    b1 = np.where(inside_mask, B_half - abs_x_rel, 0.0)
    b2 = np.where(inside_mask, B_half + abs_x_rel, 0.0)
    b_far = np.where(~inside_mask, abs_x_rel + B_half, 0.0)
    b_near = np.where(~inside_mask, abs_x_rel - B_half, 0.0)

    Iz = np.zeros_like(x_rel_arr, dtype=float)

    if np.any(inside_mask):
        y_half_inside = np.broadcast_to(y_half, x_rel_arr.shape)[inside_mask]
        Iz_inside = 2.0 * (
            fadum_corner_stress(b1[inside_mask], y_half_inside, z_arr[inside_mask])
            + fadum_corner_stress(b2[inside_mask], y_half_inside, z_arr[inside_mask])
        )
        Iz[inside_mask] = Iz_inside

    if np.any(~inside_mask):
        y_half_outside = np.broadcast_to(y_half, x_rel_arr.shape)[~inside_mask]
        Iz_outside = 2.0 * (
            fadum_corner_stress(
                b_far[~inside_mask], y_half_outside, z_arr[~inside_mask]
            )
            - fadum_corner_stress(
                b_near[~inside_mask], y_half_outside, z_arr[~inside_mask]
            )
        )
        Iz[~inside_mask] = Iz_outside

    result = np.maximum(0.0, q_arr * Iz)

    if result.ndim == 0:
        return float(result)
    return result


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
    x_rel : float or numpy.ndarray
        Horizontal distance from the load's center [m].
    z : float or numpy.ndarray
        Depth below the surface [m].
    method : StressMethod, optional
        The stress distribution method to apply. Default is StressMethod.BOUSSINESQ.

    Returns
    -------
    float or numpy.ndarray
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

    if np.isscalar(x_rel) and np.isscalar(z):
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

    x_rel_arr = np.asarray(x_rel)
    z_arr = np.asarray(z)
    depth_arr = np.maximum(0.01, z_arr + load.z_surface_offset)

    if method == StressMethod.TWO_TO_ONE:
        if load.type == LoadType.STRIP:
            cond = np.abs(x_rel_arr) <= (B + depth_arr) / 2.0
            val = (q * B) / (B + depth_arr)
            result = np.where(cond, val, 0.0)
        else:
            L = max(0.1, float(load.length_L))
            cond = np.abs(x_rel_arr) <= (B + depth_arr) / 2.0
            val = (q * B * L) / ((B + depth_arr) * (L + depth_arr))
            result = np.where(cond, val, 0.0)
    elif method == StressMethod.BOUSSINESQ:
        if load.type == LoadType.STRIP:
            result = boussinesq_strip_stress(q, B, x_rel_arr, depth_arr)
        else:
            L = max(0.1, float(load.length_L))
            result = boussinesq_rectangular_stress(q, B, L, x_rel_arr, depth_arr)
    elif method == StressMethod.WESTERGAARD:
        raise NotImplementedError("Westergaard method not yet implemented.")
    else:
        raise ValueError(f"Unsupported stress method: {method}")

    if result.ndim == 0:
        return float(result)
    return result


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
    ds_sum = np.zeros_like(Z, dtype=np.float64)

    for load in loads:
        X_rel = X - load.x_center
        ds_sum += compute_load_stress_increment(load, X_rel, Z, method)

    return ds_sum / max(1.0, float(primary_q))
