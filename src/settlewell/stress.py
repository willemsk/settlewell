import math
import numpy as np
from numpy.typing import NDArray

from settlewell.models import LoadGeometry, LoadType, StressMethod


def fadum_corner_stress(b: float, l_dim: float, z: float) -> float:
    """
    Calculate Fadum (1948) corner stress influence value Iz for a rectangle b x l_dim at depth z.

    Parameters
    ----------
    b : float
        Width of the rectangular area [m].
    l_dim : float
        Length of the rectangular area [m].
    z : float
        Depth below the loaded area [m].

    Returns
    -------
    float
        Vertical stress influence factor Iz [-].
    """
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

    if v - v_mn < 0:
        arg2_val = math.atan(arg2) + math.pi
    else:
        arg2_val = math.atan(arg2)

    return float((1.0 / (4.0 * math.pi)) * (term1 + arg2_val))


def boussinesq_strip_stress(q: float, B: float, x_rel: float, z: float) -> float:
    """
    Calculate vertical stress increment under a Boussinesq strip load.

    Parameters
    ----------
    q : float
        Applied uniform stress [kPa].
    B : float
        Width of the strip load [m].
    x_rel : float
        Horizontal distance from the center of the strip [m].
    z : float
        Depth below the load [m].

    Returns
    -------
    float
        Vertical stress increment [kPa].
    """
    if z <= 1e-6:
        if abs(x_rel) <= B / 2.0:
            return float(q)
        return 0.0

    x_L = x_rel - B / 2.0
    x_R = x_rel + B / 2.0

    alpha = math.atan(x_R / z) - math.atan(x_L / z)
    return float((q / math.pi) * (alpha + math.sin(alpha) * math.cos(alpha)))


def boussinesq_rectangular_stress(
    q: float, B: float, L: float, x_rel: float, z: float
) -> float:
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
    x_rel : float
        Horizontal distance from the center of the load [m].
    z : float
        Depth below the surface [m].

    Returns
    -------
    float
        Vertical stress increment [kPa].
    """
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


def compute_load_stress_increment(
    load: LoadGeometry,
    x_rel: float,
    z: float,
    method: StressMethod = StressMethod.BOUSSINESQ,
) -> float:
    """
    Compute vertical stress increment delta_sigma_z under a specific surface load geometry.

    Parameters
    ----------
    load : LoadGeometry
        The load geometry definition.
    x_rel : float
        Horizontal distance from the load's center [m].
    z : float
        Depth below the surface [m].
    method : StressMethod, optional
        The stress distribution method to apply. Default is StressMethod.BOUSSINESQ.

    Returns
    -------
    float
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

    for i, z in enumerate(z_points):
        for j, x in enumerate(x_points):
            ds_sum = 0.0
            for load in loads:
                x_rel = x - load.x_center
                ds_sum += compute_load_stress_increment(load, x_rel, z, method)
            heatmap[i, j] = ds_sum / max(1.0, float(primary_q))

    return heatmap
