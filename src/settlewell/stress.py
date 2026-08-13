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
    b = np.broadcast_to(b, shape)
    l_dim = np.broadcast_to(l_dim, shape)
    z = np.broadcast_to(z, shape)

    out = np.zeros(shape, dtype=np.float64)

    mask_z0 = z <= 1e-6
    mask_0 = (b <= 1e-6) | (l_dim <= 1e-6)
    mask_valid = ~mask_z0 & ~mask_0

    out[mask_z0] = 0.25

    if np.any(mask_valid):
        bz = b[mask_valid]
        lz = l_dim[mask_valid]
        zz = z[mask_valid]

        m = bz / zz
        n = lz / zz
        m2 = m * m
        n2 = n * n
        v = m2 + n2 + 1.0
        v_mn = m2 * n2

        term1 = (2.0 * m * n * np.sqrt(v) / (v + v_mn)) * ((v + 1.0) / v)
        arg2 = (2.0 * m * n * np.sqrt(v)) / (v - v_mn)

        arg2_val = np.zeros_like(arg2)

        mask_eq = np.abs(v - v_mn) < 1e-12
        mask_lt = (v - v_mn) < 0
        mask_lt = mask_lt & ~mask_eq
        mask_else = ~mask_eq & ~mask_lt

        arg2_val[mask_eq] = np.pi / 2.0
        arg2_val[mask_lt] = np.arctan(arg2[mask_lt]) + np.pi
        arg2_val[mask_else] = np.arctan(arg2[mask_else])

        out[mask_valid] = (1.0 / (4.0 * np.pi)) * (term1 + arg2_val)

    if out.ndim == 0:
        return float(out)
    return out


def boussinesq_strip_stress(
    q: float,
    B: float,
    x_rel: float | NDArray[np.float64],
    z: float | NDArray[np.float64],
) -> float | NDArray[np.float64]:
    """
    Calculate vertical stress increment under a Boussinesq strip load.

    Parameters
    ----------
    q : float
        Applied uniform stress [kPa].
    B : float
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
    x_rel = np.broadcast_to(x_rel, shape)
    z = np.broadcast_to(z, shape)

    out = np.zeros(shape, dtype=np.float64)

    mask_z0 = z <= 1e-6
    mask_z0_inside = mask_z0 & (np.abs(x_rel) <= B / 2.0)
    out[mask_z0_inside] = float(q)

    mask_valid = ~mask_z0

    if np.any(mask_valid):
        x_rel_v = x_rel[mask_valid]
        z_v = z[mask_valid]

        x_L = x_rel_v - B / 2.0
        x_R = x_rel_v + B / 2.0

        alpha = np.arctan(x_R / z_v) - np.arctan(x_L / z_v)
        out[mask_valid] = (q / np.pi) * (alpha + np.sin(alpha) * np.cos(alpha))

    if out.ndim == 0:
        return float(out)
    return out


def boussinesq_rectangular_stress(
    q: float,
    B: float,
    L: float,
    x_rel: float | NDArray[np.float64],
    z: float | NDArray[np.float64],
) -> float | NDArray[np.float64]:
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
    x_rel : float | NDArray[np.float64]
        Horizontal distance from the center of the load [m].
    z : float | NDArray[np.float64]
        Depth below the surface [m].

    Returns
    -------
    float | NDArray[np.float64]
        Vertical stress increment [kPa].
    """
    if not isinstance(x_rel, np.ndarray) and not isinstance(z, np.ndarray):
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

    shape = np.broadcast_shapes(np.shape(x_rel), np.shape(z))
    x_rel = np.broadcast_to(x_rel, shape)
    z = np.broadcast_to(z, shape)
    y_half = L / 2.0

    out = np.zeros(shape, dtype=np.float64)

    mask_inside = np.abs(x_rel) <= B / 2.0
    mask_outside = ~mask_inside

    if np.any(mask_inside):
        x_in = x_rel[mask_inside]
        z_in = z[mask_inside]

        b1 = B / 2.0 - np.abs(x_in)
        b2 = B / 2.0 + np.abs(x_in)

        Iz_in = 2.0 * (
            fadum_corner_stress(b1, y_half, z_in)
            + fadum_corner_stress(b2, y_half, z_in)
        )
        out[mask_inside] = np.maximum(0.0, q * Iz_in)

    if np.any(mask_outside):
        x_out = x_rel[mask_outside]
        z_out = z[mask_outside]

        b_far = np.abs(x_out) + B / 2.0
        b_near = np.abs(x_out) - B / 2.0

        Iz_out = 2.0 * (
            fadum_corner_stress(b_far, y_half, z_out)
            - fadum_corner_stress(b_near, y_half, z_out)
        )
        out[mask_outside] = np.maximum(0.0, q * Iz_out)

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

    x_rel = np.asarray(x_rel)
    z = np.asarray(z)
    depth = np.maximum(0.01, z + load.z_surface_offset)

    if method == StressMethod.TWO_TO_ONE:
        out = np.zeros(np.broadcast_shapes(x_rel.shape, depth.shape), dtype=np.float64)
        mask_inside = np.abs(x_rel) <= (B + depth) / 2.0

        if load.type == LoadType.STRIP:
            if np.any(mask_inside):
                out[mask_inside] = (q * B) / (B + depth[mask_inside])
        else:
            L = max(0.1, float(load.length_L))
            if np.any(mask_inside):
                out[mask_inside] = (q * B * L) / (
                    (B + depth[mask_inside]) * (L + depth[mask_inside])
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
    X, Z = np.meshgrid(x_points, z_points)
    heatmap = np.zeros_like(X, dtype=np.float64)
    primary_q = loads[0].stress_q if loads else 100.0

    for load in loads:
        x_rel = X - load.x_center
        heatmap += compute_load_stress_increment(load, x_rel, Z, method)

    return heatmap / max(1.0, float(primary_q))
