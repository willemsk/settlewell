"""Hydraulic drawdown calculations for dewatering.

Supports both confined and unconfined aquifers, steady-state (Thiem/Dupuit)
and transient (Theis) solutions, with superposition for multiple wells.
"""
import math
import numpy as np
from scipy.special import exp1
from .models import DewateringConfig, SoilProfile, AquiferType

GAMMA_W = 9.81  # [kN/m³] Unit weight of water


def compute_transmissivity(profile: SoilProfile, config: DewateringConfig) -> float:
    """Compute aquifer transmissivity T [m²/s] from soil layers.
    
    For UNCONFINED: T = sum(k_h_i * thickness_i) for all saturated layers above total depth.
    For CONFINED: T = sum(k_h_i * thickness_i) for layers within the confined aquifer only
                  (layers below the primary confining clay layer).
    
    Returns config.T if set.
    """
    if config.T is not None:
        return config.T

    if config.aquifer_type == AquiferType.UNCONFINED:
        gwl_depth = profile.gwl_depth
        T = 0.0
        current_depth = 0.0
        for layer in profile.layers:
            top = current_depth
            bottom = current_depth + layer.thickness
            sat_top = max(top, gwl_depth)
            sat_bottom = bottom
            sat_thickness = max(0.0, sat_bottom - sat_top)
            T += layer.k_h * sat_thickness
            current_depth = bottom
        return T
    else:  # CONFINED
        # Identify confining layer as layer with minimum k_h
        min_kh_idx = min(range(len(profile.layers)), key=lambda i: profile.layers[i].k_h)
        confined_layers = profile.layers[min_kh_idx + 1:]
        if not confined_layers:
            confined_layers = profile.layers
        return sum(layer.k_h * layer.thickness for layer in confined_layers)


def compute_storativity(profile: SoilProfile, config: DewateringConfig) -> float:
    """Compute storativity S [-] from soil layers.
    
    For UNCONFINED: S = specific yield ≈ e0 / (1 + e0) for the primary aquifer layer.
    For CONFINED: S = sum(m_v_i * gamma_w * thickness_i) where m_v = 1/Eoed.
    
    Returns config.S if set.
    """
    if config.S is not None:
        return config.S

    if config.aquifer_type == AquiferType.UNCONFINED:
        # Aquifer layer is layer with maximum k_h
        aquifer_layer = max(profile.layers, key=lambda l: l.k_h)
        return aquifer_layer.e0 / (1.0 + aquifer_layer.e0)
    else:  # CONFINED
        return sum((GAMMA_W * layer.thickness) / layer.Eoed for layer in profile.layers)


def compute_radius_of_influence(config: DewateringConfig, T: float) -> float:
    """Compute radius of influence R [m] using Sichardt's empirical formula.
    
    R = 3000 * s * sqrt(k)
    
    Returns config.R if explicitly set, otherwise computes it.
    """
    if config.R is not None:
        return config.R

    s = config.target_drawdown
    # Representative k = T / total_aquifer_thickness (assume ~10m if 0)
    # Using 10m or average depth
    k_rep = T / 10.0
    R = 3000.0 * s * math.sqrt(k_rep)
    return max(R, 1.0)


def thiem_drawdown_single_well(
    r: float | np.ndarray,
    Q: float,
    T: float,
    R: float,
    H0: float,
    aquifer_type: AquiferType,
) -> float | np.ndarray:
    """Steady-state drawdown at distance r from a single well.
    
    CONFINED (Thiem, 1906):
        s(r) = Q / (2π T) * ln(R / r)
    
    UNCONFINED (Dupuit, 1863):
        h²(r) = H0² - (Q / (π K)) * ln(R / r)
        s(r) = H0 - h(r)
    """
    is_scalar = np.isscalar(r)
    r_arr = np.atleast_1d(np.asarray(r, dtype=float))
    # Clip r to minimum radius of 0.075m to avoid singularity
    r_eff = np.maximum(r_arr, 0.075)

    if aquifer_type == AquiferType.CONFINED:
        s = (Q / (2.0 * np.pi * T)) * np.log(np.maximum(R / r_eff, 1.0))
        s = np.maximum(0.0, s)
    else:  # UNCONFINED
        K = T / max(H0, 1e-3)
        ln_term = np.log(np.maximum(R / r_eff, 1.0))
        h2 = H0**2 - (Q / (np.pi * K)) * ln_term
        h = np.sqrt(np.maximum(0.0, h2))
        s = np.maximum(0.0, H0 - h)

    return float(s[0]) if is_scalar else s


def theis_drawdown_single_well(
    r: float | np.ndarray,
    t: float,
    Q: float,
    T: float,
    S: float,
) -> float | np.ndarray:
    """Transient drawdown at distance r and time t from a single well (Theis, 1935).
    
    s(r, t) = Q / (4π T) * W(u) where W(u) = exp1(u).
    """
    is_scalar = np.isscalar(r)
    r_arr = np.atleast_1d(np.asarray(r, dtype=float))
    r_eff = np.maximum(r_arr, 0.075)

    if t <= 0:
        s = np.zeros_like(r_eff)
    else:
        u = (r_eff**2 * S) / (4.0 * T * t)
        s = (Q / (4.0 * np.pi * T)) * exp1(u)
        s = np.maximum(0.0, s)

    return float(s[0]) if is_scalar else s


def compute_drawdown_at_points(
    points: list[tuple[float, float]],
    config: DewateringConfig,
    profile: SoilProfile,
    time_s: float | None = None,
) -> np.ndarray:
    """Compute total drawdown at multiple (x,y) points using superposition."""
    T = compute_transmissivity(profile, config)
    S = compute_storativity(profile, config)
    R = compute_radius_of_influence(config, T)
    H0 = profile.total_depth - profile.gwl_depth

    drawdowns = []
    for px, py in points:
        s_total = 0.0
        for well in config.wells:
            r = math.hypot(px - well.x, py - well.y)
            if time_s is None:
                s_w = thiem_drawdown_single_well(r, well.Q, T, R, H0, config.aquifer_type)
            else:
                s_w = theis_drawdown_single_well(r, time_s, well.Q, T, S)
            s_total += float(s_w)
        s_total = min(s_total, config.target_drawdown)
        s_total = max(0.0, s_total)
        drawdowns.append(s_total)

    return np.array(drawdowns, dtype=float)


def compute_drawdown_grid(
    x_range: tuple[float, float],
    y_range: tuple[float, float],
    nx: int,
    ny: int,
    config: DewateringConfig,
    profile: SoilProfile,
    time_s: float | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute drawdown on a regular 2D grid for contour plotting."""
    x = np.linspace(x_range[0], x_range[1], nx)
    y = np.linspace(y_range[0], y_range[1], ny)
    X, Y = np.meshgrid(x, y)
    points = list(zip(X.ravel(), Y.ravel()))
    S_flat = compute_drawdown_at_points(points, config, profile, time_s)
    S = S_flat.reshape((ny, nx))
    return X, Y, S
