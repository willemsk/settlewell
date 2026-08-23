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
        not isinstance(z, np.ndarray)
        and not isinstance(b, np.ndarray)
        and not isinstance(l_dim, np.ndarray)
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

    b_arr = np.atleast_1d(b).astype(np.float64)
    l_arr = np.atleast_1d(l_dim).astype(np.float64)
    z_arr = np.atleast_1d(z).astype(np.float64)

    shape = np.broadcast_shapes(b_arr.shape, l_arr.shape, z_arr.shape)
    b_arr = np.broadcast_to(b_arr, shape)
    l_arr = np.broadcast_to(l_arr, shape)
    z_arr = np.broadcast_to(z_arr, shape)

    out = np.zeros_like(b_arr, dtype=np.float64)

    mask_z0 = z_arr <= 1e-6
    mask_b0 = (b_arr <= 1e-6) | (l_arr <= 1e-6)
    mask_b0 = mask_b0 & ~mask_z0

    out[mask_z0] = 0.25
    out[mask_b0] = 0.0

    mask_calc = ~(mask_z0 | mask_b0)

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
        arg2_val = np.empty_like(arg2)

        mask_eq = np.abs(diff) < 1e-12
        mask_lt = (diff < 0) & ~mask_eq
        mask_gt = (diff >= 0) & ~mask_eq & ~mask_lt

        arg2_val[mask_eq] = np.pi / 2.0
        arg2_val[mask_lt] = np.arctan(arg2[mask_lt]) + np.pi
        arg2_val[mask_gt] = np.arctan(arg2[mask_gt])

        res = (1.0 / (4.0 * np.pi)) * (term1 + arg2_val)
        out[mask_calc] = res

    if out.ndim == 1 and np.isscalar(b) and np.isscalar(l_dim) and np.isscalar(z):
        return float(out[0])
    elif np.isscalar(b) and np.isscalar(l_dim) and np.isscalar(z):
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

    q_arr = np.atleast_1d(q).astype(np.float64)
    B_arr = np.atleast_1d(B).astype(np.float64)
    x_rel_arr = np.atleast_1d(x_rel).astype(np.float64)
    z_arr = np.atleast_1d(z).astype(np.float64)

    shape = np.broadcast_shapes(q_arr.shape, B_arr.shape, x_rel_arr.shape, z_arr.shape)
    q_arr = np.broadcast_to(q_arr, shape)
    B_arr = np.broadcast_to(B_arr, shape)
    x_rel_arr = np.broadcast_to(x_rel_arr, shape)
    z_arr = np.broadcast_to(z_arr, shape)

    out = np.zeros_like(q_arr, dtype=np.float64)

    mask_z0 = z_arr <= 1e-6
    mask_in = mask_z0 & (np.abs(x_rel_arr) <= B_arr / 2.0)
    out[mask_in] = q_arr[mask_in]

    mask_calc = ~mask_z0
    if np.any(mask_calc):
        qc = q_arr[mask_calc]
        Bc = B_arr[mask_calc]
        xc = x_rel_arr[mask_calc]
        zc = z_arr[mask_calc]

        x_L = xc - Bc / 2.0
        x_R = xc + Bc / 2.0

        alpha = np.arctan(x_R / zc) - np.arctan(x_L / zc)
        out[mask_calc] = (qc / np.pi) * (alpha + np.sin(alpha) * np.cos(alpha))

    if (
        out.ndim == 1
        and np.isscalar(q)
        and np.isscalar(B)
        and np.isscalar(x_rel)
        and np.isscalar(z)
    ):
        return float(out[0])
    elif np.isscalar(q) and np.isscalar(B) and np.isscalar(x_rel) and np.isscalar(z):
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

    q_arr = np.atleast_1d(q).astype(np.float64)
    B_arr = np.atleast_1d(B).astype(np.float64)
    L_arr = np.atleast_1d(L).astype(np.float64)
    x_rel_arr = np.atleast_1d(x_rel).astype(np.float64)
    z_arr = np.atleast_1d(z).astype(np.float64)

    shape = np.broadcast_shapes(
        q_arr.shape, B_arr.shape, L_arr.shape, x_rel_arr.shape, z_arr.shape
    )
    q_arr = np.broadcast_to(q_arr, shape)
    B_arr = np.broadcast_to(B_arr, shape)
    L_arr = np.broadcast_to(L_arr, shape)
    x_rel_arr = np.broadcast_to(x_rel_arr, shape)
    z_arr = np.broadcast_to(z_arr, shape)

    y_half = L_arr / 2.0
    Iz = np.zeros_like(q_arr, dtype=np.float64)

    mask_inside = np.abs(x_rel_arr) <= B_arr / 2.0
    mask_outside = ~mask_inside

    if np.any(mask_inside):
        b1 = B_arr[mask_inside] / 2.0 - np.abs(x_rel_arr[mask_inside])
        b2 = B_arr[mask_inside] / 2.0 + np.abs(x_rel_arr[mask_inside])
        y_h = y_half[mask_inside]
        zc = z_arr[mask_inside]

        Iz[mask_inside] = 2.0 * (
            fadum_corner_stress(b1, y_h, zc) + fadum_corner_stress(b2, y_h, zc)
        )

    if np.any(mask_outside):
        b_far = np.abs(x_rel_arr[mask_outside]) + B_arr[mask_outside] / 2.0
        b_near = np.abs(x_rel_arr[mask_outside]) - B_arr[mask_outside] / 2.0
        y_h = y_half[mask_outside]
        zc = z_arr[mask_outside]

        Iz[mask_outside] = 2.0 * (
            fadum_corner_stress(b_far, y_h, zc) - fadum_corner_stress(b_near, y_h, zc)
        )

    out = np.maximum(0.0, q_arr * Iz)

    if (
        out.ndim == 1
        and np.isscalar(q)
        and np.isscalar(B)
        and np.isscalar(L)
        and np.isscalar(x_rel)
        and np.isscalar(z)
    ):
        return float(out[0])
    elif (
        np.isscalar(q)
        and np.isscalar(B)
        and np.isscalar(L)
        and np.isscalar(x_rel)
        and np.isscalar(z)
    ):
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

    if not isinstance(x_rel, np.ndarray) and not isinstance(z, np.ndarray):
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

    x_rel_arr = np.atleast_1d(x_rel).astype(np.float64)
    z_arr = np.atleast_1d(z).astype(np.float64)

    shape = np.broadcast_shapes(x_rel_arr.shape, z_arr.shape)
    x_rel_arr = np.broadcast_to(x_rel_arr, shape)
    z_arr = np.broadcast_to(z_arr, shape)

    depth_arr = np.maximum(0.01, z_arr + load.z_surface_offset)
    out = np.zeros_like(x_rel_arr, dtype=np.float64)

    if method == StressMethod.TWO_TO_ONE:
        mask_in = np.abs(x_rel_arr) <= (B + depth_arr) / 2.0
        if load.type == LoadType.STRIP:
            if np.any(mask_in):
                out[mask_in] = (q * B) / (B + depth_arr[mask_in])
        else:
            L = max(0.1, float(load.length_L))
            if np.any(mask_in):
                out[mask_in] = (q * B * L) / (
                    (B + depth_arr[mask_in]) * (L + depth_arr[mask_in])
                )

    elif method == StressMethod.BOUSSINESQ:
        if load.type == LoadType.STRIP:
            res = boussinesq_strip_stress(q, B, x_rel_arr, depth_arr)
            out[:] = res
        else:
            L = max(0.1, float(load.length_L))
            res = boussinesq_rectangular_stress(q, B, L, x_rel_arr, depth_arr)
            out[:] = res
    elif method == StressMethod.WESTERGAARD:
        raise NotImplementedError("Westergaard method not yet implemented.")
    else:
        raise ValueError(f"Unsupported stress method: {method}")

    if out.ndim == 1 and np.isscalar(x_rel) and np.isscalar(z):
        return float(out[0])
    elif np.isscalar(x_rel) and np.isscalar(z):
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

    ds_sum = np.zeros_like(X, dtype=np.float64)
    for load in loads:
        x_rel = X - load.x_center
        ds_sum += compute_load_stress_increment(load, x_rel, Z, method)

    heatmap = ds_sum / max(1.0, float(primary_q))
    return heatmap
