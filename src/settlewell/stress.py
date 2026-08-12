import math
import numpy as np
from numpy.typing import NDArray

from settlewell.models import LoadGeometry, LoadType, StressMethod


def _is_scalar(x):
    return not isinstance(x, np.ndarray)


def fadum_corner_stress(
    b: float | NDArray[np.float64],
    l_dim: float | NDArray[np.float64],
    z: float | NDArray[np.float64],
) -> float | NDArray[np.float64]:
    """
    Calculate Fadum (1948) corner stress influence value Iz for a rectangle b x l_dim at depth z.

    Parameters
    ----------
    b : float | NDArray[np.float64]
        Width of the rectangular area [m].
    l_dim : float | NDArray[np.float64]
        Length of the rectangular area [m].
    z : float | NDArray[np.float64]
        Depth below the loaded area [m].

    Returns
    -------
    float | NDArray[np.float64]
        Vertical stress influence factor Iz [-].
    """
    if _is_scalar(b) and _is_scalar(l_dim) and _is_scalar(z):
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

    shape = np.broadcast_shapes(np.shape(b), np.shape(l_dim), np.shape(z))
    b_arr = np.broadcast_to(b, shape)
    l_arr = np.broadcast_to(l_dim, shape)
    z_arr = np.broadcast_to(z, shape)

    out = np.zeros(shape, dtype=np.float64)

    mask_z = z_arr <= 1e-6
    out[mask_z] = 0.25

    mask_b_l = (b_arr <= 1e-6) | (l_arr <= 1e-6)
    mask_b_l = mask_b_l & ~mask_z
    out[mask_b_l] = 0.0

    mask_calc = ~(mask_z | mask_b_l)
    if np.any(mask_calc):
        b_c = b_arr[mask_calc]
        l_c = l_arr[mask_calc]
        z_c = z_arr[mask_calc]

        m = b_c / z_c
        n = l_c / z_c
        m2 = m * m
        n2 = n * n
        v = m2 + n2 + 1.0
        v_mn = m2 * n2

        term1 = (2.0 * m * n * np.sqrt(v) / (v + v_mn)) * ((v + 1.0) / v)

        with np.errstate(divide="ignore", invalid="ignore"):
            arg2 = (2.0 * m * n * np.sqrt(v)) / (v - v_mn)

        diff = v - v_mn

        arg2_val = np.where(
            np.abs(diff) < 1e-12,
            np.pi / 2.0,
            np.where(diff < 0, np.arctan(arg2) + np.pi, np.arctan(arg2)),
        )
        out[mask_calc] = (1.0 / (4.0 * np.pi)) * (term1 + arg2_val)

    if out.ndim == 0:
        return float(out)
    return out


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
    q : float | NDArray[np.float64]
        Applied uniform stress [kPa].
    B : float | NDArray[np.float64]
        Width of the strip load [m].
    x_rel : float | NDArray[np.float64]
        Horizontal distance from the center of the strip [m].
    z : float | NDArray[np.float64]
        Depth below the load [m].

    Returns
    -------
    float | NDArray[np.float64]
        Vertical stress increment [kPa].
    """
    if _is_scalar(q) and _is_scalar(B) and _is_scalar(x_rel) and _is_scalar(z):
        if z <= 1e-6:
            if abs(x_rel) <= B / 2.0:
                return float(q)
            return 0.0

        x_L = x_rel - B / 2.0
        x_R = x_rel + B / 2.0

        alpha = math.atan(x_R / z) - math.atan(x_L / z)
        return float((q / math.pi) * (alpha + math.sin(alpha) * math.cos(alpha)))

    shape = np.broadcast_shapes(np.shape(q), np.shape(B), np.shape(x_rel), np.shape(z))
    q_arr = np.broadcast_to(q, shape)
    B_arr = np.broadcast_to(B, shape)
    x_rel_arr = np.broadcast_to(x_rel, shape)
    z_arr = np.broadcast_to(z, shape)

    out = np.zeros(shape, dtype=np.float64)

    mask_z = z_arr <= 1e-6
    mask_z_inside = mask_z & (np.abs(x_rel_arr) <= B_arr / 2.0)
    out[mask_z_inside] = q_arr[mask_z_inside]

    mask_calc = ~mask_z
    if np.any(mask_calc):
        q_c = q_arr[mask_calc]
        B_c = B_arr[mask_calc]
        x_rel_c = x_rel_arr[mask_calc]
        z_c = z_arr[mask_calc]

        x_L = x_rel_c - B_c / 2.0
        x_R = x_rel_c + B_c / 2.0

        alpha = np.arctan(x_R / z_c) - np.arctan(x_L / z_c)
        out[mask_calc] = (q_c / np.pi) * (alpha + np.sin(alpha) * np.cos(alpha))

    if out.ndim == 0:
        return float(out)
    return out


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
    q : float | NDArray[np.float64]
        Applied uniform stress [kPa].
    B : float | NDArray[np.float64]
        Width of the rectangular load [m].
    L : float | NDArray[np.float64]
        Length of the rectangular load [m].
    x_rel : float | NDArray[np.float64]
        Horizontal distance from the center of the load [m].
    z : float | NDArray[np.float64]
        Depth below the surface [m].

    Returns
    -------
    float | NDArray[np.float64]
        Vertical stress increment [kPa].
    """
    if (
        _is_scalar(q)
        and _is_scalar(B)
        and _is_scalar(L)
        and _is_scalar(x_rel)
        and _is_scalar(z)
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

    shape = np.broadcast_shapes(
        np.shape(q), np.shape(B), np.shape(L), np.shape(x_rel), np.shape(z)
    )
    q_arr = np.broadcast_to(q, shape)
    B_arr = np.broadcast_to(B, shape)
    L_arr = np.broadcast_to(L, shape)
    x_rel_arr = np.broadcast_to(x_rel, shape)
    z_arr = np.broadcast_to(z, shape)

    out = np.zeros(shape, dtype=np.float64)

    y_half = L_arr / 2.0
    abs_x_rel = np.abs(x_rel_arr)

    mask_inside = abs_x_rel <= B_arr / 2.0

    if np.any(mask_inside):
        b1 = B_arr[mask_inside] / 2.0 - abs_x_rel[mask_inside]
        b2 = B_arr[mask_inside] / 2.0 + abs_x_rel[mask_inside]
        z_in = z_arr[mask_inside]
        y_half_in = y_half[mask_inside]
        Iz = 2.0 * (
            fadum_corner_stress(b1, y_half_in, z_in)
            + fadum_corner_stress(b2, y_half_in, z_in)
        )
        out[mask_inside] = q_arr[mask_inside] * Iz

    mask_outside = ~mask_inside
    if np.any(mask_outside):
        b_far = abs_x_rel[mask_outside] + B_arr[mask_outside] / 2.0
        b_near = abs_x_rel[mask_outside] - B_arr[mask_outside] / 2.0
        z_out = z_arr[mask_outside]
        y_half_out = y_half[mask_outside]
        Iz = 2.0 * (
            fadum_corner_stress(b_far, y_half_out, z_out)
            - fadum_corner_stress(b_near, y_half_out, z_out)
        )
        out[mask_outside] = q_arr[mask_outside] * Iz

    out = np.maximum(0.0, out)

    if out.ndim == 0:
        return float(out)
    return out


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
    x_rel : float | NDArray[np.float64]
        Horizontal distance from the load's center [m].
    z : float | NDArray[np.float64]
        Depth below the surface [m].
    method : StressMethod, optional
        The stress distribution method to apply. Default is StressMethod.BOUSSINESQ.

    Returns
    -------
    float | NDArray[np.float64]
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

    if _is_scalar(z):
        depth = max(0.01, float(z + load.z_surface_offset))
    else:
        depth = np.maximum(0.01, z + load.z_surface_offset)

    if method == StressMethod.TWO_TO_ONE:
        if _is_scalar(x_rel) and _is_scalar(depth):
            if load.type == LoadType.STRIP:
                if abs(x_rel) <= (B + depth) / 2.0:
                    return float((q * B) / (B + depth))
                return 0.0
            else:
                L = max(0.1, float(load.length_L))
                if abs(x_rel) <= (B + depth) / 2.0:
                    return float((q * B * L) / ((B + depth) * (L + depth)))
                return 0.0

        shape = np.broadcast_shapes(np.shape(x_rel), np.shape(depth))
        x_rel_arr = np.broadcast_to(x_rel, shape)
        depth_arr = np.broadcast_to(depth, shape)
        out = np.zeros(shape, dtype=np.float64)

        if load.type == LoadType.STRIP:
            mask = np.abs(x_rel_arr) <= (B + depth_arr) / 2.0
            out[mask] = (q * B) / (B + depth_arr[mask])
        else:
            L = max(0.1, float(load.length_L))
            mask = np.abs(x_rel_arr) <= (B + depth_arr) / 2.0
            out[mask] = (q * B * L) / ((B + depth_arr[mask]) * (L + depth_arr[mask]))

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
    primary_q = loads[0].stress_q if loads else 100.0

    Z, X = np.meshgrid(z_points, x_points, indexing="ij")
    ds_sum = np.zeros_like(Z, dtype=np.float64)

    for load in loads:
        X_rel = X - load.x_center
        ds_sum += compute_load_stress_increment(load, X_rel, Z, method)

    return ds_sum / max(1.0, float(primary_q))
