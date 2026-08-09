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
    b_arr, l_dim_arr, z_arr = np.broadcast_arrays(b, l_dim, z)
    out = np.zeros_like(b_arr, dtype=np.float64)

    mask_z_zero = z_arr <= 1e-6
    mask_b_l_zero = (b_arr <= 1e-6) | (l_dim_arr <= 1e-6)

    out[mask_z_zero] = 0.25
    out[~mask_z_zero & mask_b_l_zero] = 0.0

    mask_calc = ~mask_z_zero & ~mask_b_l_zero

    if np.any(mask_calc):
        b_c = b_arr[mask_calc]
        l_c = l_dim_arr[mask_calc]
        z_c = z_arr[mask_calc]

        m = b_c / z_c
        n = l_c / z_c
        m2 = m * m
        n2 = n * n
        v = m2 + n2 + 1.0
        v_mn = m2 * n2

        term1 = (2.0 * m * n * np.sqrt(v) / (v + v_mn)) * ((v + 1.0) / v)

        with np.errstate(divide='ignore', invalid='ignore'):
            arg2 = (2.0 * m * n * np.sqrt(v)) / (v - v_mn)

        arg2_val = np.empty_like(arg2)
        diff = v - v_mn

        mask_eq = np.abs(diff) < 1e-12
        mask_lt = (diff < 0) & ~mask_eq
        mask_gt = ~(mask_eq | mask_lt)

        arg2_val[mask_eq] = np.pi / 2.0
        arg2_val[mask_lt] = np.arctan(arg2[mask_lt]) + np.pi
        arg2_val[mask_gt] = np.arctan(arg2[mask_gt])

        out[mask_calc] = (1.0 / (4.0 * np.pi)) * (term1 + arg2_val)

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
    x_rel : float or np.ndarray
        Horizontal distance from the center of the strip [m].
    z : float or np.ndarray
        Depth below the load [m].

    Returns
    -------
    float or np.ndarray
        Vertical stress increment [kPa].
    """
    x_arr, z_arr = np.broadcast_arrays(x_rel, z)
    out = np.zeros_like(x_arr, dtype=np.float64)

    mask_z_zero = z_arr <= 1e-6
    mask_in_strip = np.abs(x_arr) <= B / 2.0

    out[mask_z_zero & mask_in_strip] = float(q)
    out[mask_z_zero & ~mask_in_strip] = 0.0

    mask_calc = ~mask_z_zero

    if np.any(mask_calc):
        x_c = x_arr[mask_calc]
        z_c = z_arr[mask_calc]

        x_L = x_c - B / 2.0
        x_R = x_c + B / 2.0

        alpha = np.arctan(x_R / z_c) - np.arctan(x_L / z_c)
        out[mask_calc] = (q / np.pi) * (alpha + np.sin(alpha) * np.cos(alpha))

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
    x_rel : float or np.ndarray
        Horizontal distance from the center of the load [m].
    z : float or np.ndarray
        Depth below the surface [m].

    Returns
    -------
    float or np.ndarray
        Vertical stress increment [kPa].
    """
    x_arr, z_arr = np.broadcast_arrays(x_rel, z)
    out = np.zeros_like(x_arr, dtype=np.float64)

    y_half = L / 2.0
    abs_x = np.abs(x_arr)

    mask_inside = abs_x <= B / 2.0
    mask_outside = ~mask_inside

    if np.any(mask_inside):
        b1 = B / 2.0 - abs_x[mask_inside]
        b2 = B / 2.0 + abs_x[mask_inside]
        z_in = z_arr[mask_inside]
        Iz = 2.0 * (
            fadum_corner_stress(b1, y_half, z_in)
            + fadum_corner_stress(b2, y_half, z_in)
        )
        out[mask_inside] = Iz

    if np.any(mask_outside):
        b_far = abs_x[mask_outside] + B / 2.0
        b_near = abs_x[mask_outside] - B / 2.0
        z_out = z_arr[mask_outside]
        Iz = 2.0 * (
            fadum_corner_stress(b_far, y_half, z_out)
            - fadum_corner_stress(b_near, y_half, z_out)
        )
        out[mask_outside] = Iz

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

    if np.isscalar(z):
        depth = max(0.01, float(z + load.z_surface_offset))
    else:
        depth = np.maximum(0.01, z + load.z_surface_offset)

    if method == StressMethod.TWO_TO_ONE:
        x_arr, depth_arr = np.broadcast_arrays(x_rel, depth)
        out = np.zeros_like(x_arr, dtype=np.float64)

        mask = np.abs(x_arr) <= (B + depth_arr) / 2.0

        if load.type == LoadType.STRIP:
            if np.any(mask):
                out[mask] = (q * B) / (B + depth_arr[mask])
        else:
            L = max(0.1, float(load.length_L))
            if np.any(mask):
                out[mask] = (q * B * L) / (
                    (B + depth_arr[mask]) * (L + depth_arr[mask])
                )

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
    heatmap = np.zeros((len(z_points), len(x_points)), dtype=np.float64)
    primary_q = loads[0].stress_q if loads else 100.0

    if not loads:
        return heatmap

    X, Z = np.meshgrid(x_points, z_points)

    ds_sum = np.zeros_like(X, dtype=np.float64)
    for load in loads:
        x_rel = X - load.x_center
        ds_sum += compute_load_stress_increment(load, x_rel, Z, method)

    heatmap = ds_sum / max(1.0, float(primary_q))

    return heatmap
