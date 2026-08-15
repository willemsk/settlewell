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

    shape = np.broadcast_shapes(np.shape(b), np.shape(l_dim), np.shape(z))
    b_arr = np.broadcast_to(b, shape)
    l_arr = np.broadcast_to(l_dim, shape)
    z_arr = np.broadcast_to(z, shape)

    out = np.zeros_like(z_arr, dtype=np.float64)

    mask_z = z_arr <= 1e-6
    mask_b = (~mask_z) & ((b_arr <= 1e-6) | (l_arr <= 1e-6))
    mask_valid = ~(mask_z | mask_b)

    out[mask_z] = 0.25
    out[mask_b] = 0.0

    if np.any(mask_valid):
        b_v = b_arr[mask_valid]
        l_v = l_arr[mask_valid]
        z_v = z_arr[mask_valid]

        m = b_v / z_v
        n = l_v / z_v
        m2 = m * m
        n2 = n * n
        v = m2 + n2 + 1.0
        v_mn = m2 * n2

        with np.errstate(divide="ignore", invalid="ignore"):
            term1 = (2.0 * m * n * np.sqrt(v) / (v + v_mn)) * ((v + 1.0) / v)
            arg2 = (2.0 * m * n * np.sqrt(v)) / (v - v_mn)

        arg2_val = np.zeros_like(v)

        diff = v - v_mn
        mask_eq = np.abs(diff) < 1e-12
        mask_lt = diff < 0
        mask_lt = mask_lt & (~mask_eq)
        mask_gt = diff > 0
        mask_gt = mask_gt & (~mask_eq)

        arg2_val[mask_eq] = np.pi / 2.0
        arg2_val[mask_lt] = np.arctan(arg2[mask_lt]) + np.pi
        arg2_val[mask_gt] = np.arctan(arg2[mask_gt])

        out[mask_valid] = (1.0 / (4.0 * np.pi)) * (term1 + arg2_val)

    if out.ndim == 0:
        return float(out)
    return out


def boussinesq_strip_stress(
    q: float, B: float, x_rel: float | np.ndarray, z: float | np.ndarray
) -> float | np.ndarray:
    """
    Calculate vertical stress increment under a Boussinesq strip load.

    Parameters
    ----------
    q : float
        Applied uniform stress [kPa].
    B : float
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
    if not isinstance(x_rel, np.ndarray) and not isinstance(z, np.ndarray):
        if z <= 1e-6:
            if abs(x_rel) <= B / 2.0:
                return float(q)
            return 0.0

        x_L = x_rel - B / 2.0
        x_R = x_rel + B / 2.0

        alpha = math.atan(x_R / z) - math.atan(x_L / z)
        return float((q / math.pi) * (alpha + math.sin(alpha) * math.cos(alpha)))

    shape = np.broadcast_shapes(np.shape(x_rel), np.shape(z))
    x_rel_arr = np.broadcast_to(x_rel, shape)
    z_arr = np.broadcast_to(z, shape)

    out = np.zeros_like(z_arr, dtype=np.float64)

    mask_z = z_arr <= 1e-6
    mask_valid = ~mask_z

    if np.any(mask_z):
        mask_in = np.abs(x_rel_arr[mask_z]) <= B / 2.0
        out[mask_z] = np.where(mask_in, float(q), 0.0)

    if np.any(mask_valid):
        x_L_arr = x_rel_arr[mask_valid] - B / 2.0
        x_R_arr = x_rel_arr[mask_valid] + B / 2.0
        z_v = z_arr[mask_valid]

        alpha = np.arctan(x_R_arr / z_v) - np.arctan(x_L_arr / z_v)
        out[mask_valid] = (q / np.pi) * (alpha + np.sin(alpha) * np.cos(alpha))

    if out.ndim == 0:
        return float(out)
    return out


def boussinesq_rectangular_stress(
    q: float, B: float, L: float, x_rel: float | np.ndarray, z: float | np.ndarray
) -> float | np.ndarray:
    """
    Calculate vertical stress increment under a Boussinesq rectangular load.

    Parameters
    ----------
    q : float
        Applied uniform stress [kPa].
    B : float
        Width of the rectangular load [m].
    L : float
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
    y_half = L / 2.0

    if not isinstance(x_rel, np.ndarray) and not isinstance(z, np.ndarray):
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

    shape = np.broadcast_shapes(np.shape(x_rel), np.shape(z))
    x_rel_arr = np.broadcast_to(x_rel, shape)
    z_arr = np.broadcast_to(z, shape)

    out = np.zeros_like(z_arr, dtype=np.float64)
    x_abs = np.abs(x_rel_arr)

    mask_in = x_abs <= B / 2.0
    mask_out = ~mask_in

    if np.any(mask_in):
        b1 = B / 2.0 - x_abs[mask_in]
        b2 = B / 2.0 + x_abs[mask_in]
        z_in = z_arr[mask_in]
        Iz_in = 2.0 * (
            fadum_corner_stress(b1, y_half, z_in)
            + fadum_corner_stress(b2, y_half, z_in)
        )
        out[mask_in] = Iz_in

    if np.any(mask_out):
        b_far = x_abs[mask_out] + B / 2.0
        b_near = x_abs[mask_out] - B / 2.0
        z_out = z_arr[mask_out]
        Iz_out = 2.0 * (
            fadum_corner_stress(b_far, y_half, z_out)
            - fadum_corner_stress(b_near, y_half, z_out)
        )
        out[mask_out] = Iz_out

    out = np.maximum(0.0, q * out)
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

    if isinstance(z, np.ndarray):
        depth = np.maximum(0.01, z + load.z_surface_offset)
    else:
        depth = max(0.01, float(z + load.z_surface_offset))

    if method == StressMethod.TWO_TO_ONE:
        if load.type == LoadType.STRIP:
            if isinstance(x_rel, np.ndarray) or isinstance(z, np.ndarray):
                shape = np.broadcast_shapes(np.shape(x_rel), np.shape(depth))
                x_rel_arr = np.broadcast_to(x_rel, shape)
                depth_arr = np.broadcast_to(depth, shape)
                out = np.zeros_like(depth_arr, dtype=np.float64)
                mask = np.abs(x_rel_arr) <= (B + depth_arr) / 2.0
                out[mask] = (q * B) / (B + depth_arr[mask])
                if out.ndim == 0:
                    return float(out)
                return out
            else:
                if abs(x_rel) <= (B + depth) / 2.0:
                    return float((q * B) / (B + depth))
                return 0.0
        else:
            L = max(0.1, float(load.length_L))
            if isinstance(x_rel, np.ndarray) or isinstance(z, np.ndarray):
                shape = np.broadcast_shapes(np.shape(x_rel), np.shape(depth))
                x_rel_arr = np.broadcast_to(x_rel, shape)
                depth_arr = np.broadcast_to(depth, shape)
                out = np.zeros_like(depth_arr, dtype=np.float64)
                mask = np.abs(x_rel_arr) <= (B + depth_arr) / 2.0
                out[mask] = (q * B * L) / (
                    (B + depth_arr[mask]) * (L + depth_arr[mask])
                )
                if out.ndim == 0:
                    return float(out)
                return out
            else:
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
