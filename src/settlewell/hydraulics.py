"""Hydraulic drawdown calculations for construction pit dewatering.

This module provides analytical solutions for steady-state (Thiem, Dupuit) and
transient (Theis) drawdown fields around single and multi-well dewatering systems.
"""

import math
from typing import List, Optional, Tuple, Union

import numpy as np
from scipy.special import exp1

from .models import AquiferType, DewateringConfig, SoilProfile, Well

GAMMA_W: float = 9.81  # [kN/m³] Unit weight of water


def compute_transmissivity(profile: SoilProfile, config: DewateringConfig) -> float:
    """Compute overall aquifer transmissivity T from soil profile.

    Parameters
    ----------
    profile : SoilProfile
        Soil profile with layer properties and initial groundwater level.
    config : DewateringConfig
        Dewatering configuration specifying aquifer classification (`CONFINED` or `UNCONFINED`).

    Returns
    -------
    float
        Transmissivity T [m²/s].

    Notes
    -----
    Theis, C. V. (1935). [DOI: 10.1029/TR016i002p00519](https://doi.org/10.1029/TR016i002p00519)

    For `UNCONFINED` aquifers:
        $$T = \\sum_i k_{h, i} \\cdot d_{\\text{sat}, i}$$
    For `CONFINED` aquifers:
        $$T = \\sum_{i \\in \\text{confined}} k_{h, i} \\cdot H_i$$
    If `config.T` is explicitly specified, that value is returned.
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
        min_kh_idx = min(range(len(profile.layers)), key=lambda i: profile.layers[i].k_h)
        confined_layers = profile.layers[min_kh_idx + 1:]
        if not confined_layers:
            min_kh = profile.layers[min_kh_idx].k_h
            confined_layers = [l for l in profile.layers if l.k_h > min_kh * 10.0] or profile.layers
        return sum(layer.k_h * layer.thickness for layer in confined_layers)


def compute_storativity(profile: SoilProfile, config: DewateringConfig) -> float:
    """Compute storativity or specific yield S from soil profile.

    Parameters
    ----------
    profile : SoilProfile
        Soil profile containing layer void ratios and stiffness parameters.
    config : DewateringConfig
        Dewatering configuration specifying aquifer classification.

    Returns
    -------
    float
        Storativity / specific yield S [-].

    Notes
    -----
    Theis, C. V. (1935). [DOI: 10.1029/TR016i002p00519](https://doi.org/10.1029/TR016i002p00519)

    For `UNCONFINED` aquifers, S represents specific yield $S_y \\approx e_0 / (1 + e_0)$.
    For `CONFINED` aquifers, S represents elastic storativity $S = \\sum \\frac{\\gamma_w H_i}{E_{\\text{oed}, i}}$.
    If `config.S` is specified, that value is returned.
    """
    if config.S is not None:
        return config.S

    if config.aquifer_type == AquiferType.UNCONFINED:
        aquifer_layer = max(profile.layers, key=lambda l: l.k_h)
        return aquifer_layer.e0 / (1.0 + aquifer_layer.e0)
    else:  # CONFINED
        return sum((GAMMA_W * layer.thickness) / layer.Eoed for layer in profile.layers)


def compute_radius_of_influence(
    config: DewateringConfig, T: float, H0: float = 10.0
) -> float:
    """Compute radius of influence R using Sichardt's empirical equation.

    Parameters
    ----------
    config : DewateringConfig
        Dewatering configuration containing target drawdown.
    T : float
        Aquifer transmissivity [m²/s].
    H0 : float, default 10.0
        Saturated aquifer thickness [m].

    Returns
    -------
    float
        Radius of influence R [m].

    Notes
    -----
    Theis, C. V. (1935). [DOI: 10.1029/TR016i002p00519](https://doi.org/10.1029/TR016i002p00519)

    Sichardt's formula:
    $$R = 3000 \\cdot s \\cdot \\sqrt{k_{\\text{rep}}}$$
    where $s$ is target drawdown [m] and $k_{\\text{rep}} = T / H_0$ [m/s].
    """
    if config.R is not None:
        return config.R

    s = config.target_drawdown
    k_rep = T / max(H0, 1e-3)
    R = 3000.0 * s * math.sqrt(k_rep)
    return max(R, 1.0)


def thiem_drawdown_single_well(
    r: Union[float, np.ndarray],
    Q: float,
    T: float,
    R: float,
    H0: float,
    aquifer_type: AquiferType,
    r_w: float = 0.075,
) -> Union[float, np.ndarray]:
    """Calculate steady-state drawdown around a single extraction well.

    Parameters
    ----------
    r : float or numpy.ndarray
        Distance from well axis [m].
    Q : float
        Pumping extraction rate [m³/s].
    T : float
        Aquifer transmissivity [m²/s].
    R : float
        Radius of influence [m].
    H0 : float
        Initial saturated thickness of aquifer [m].
    aquifer_type : AquiferType
        Aquifer type (`CONFINED` or `UNCONFINED`).
    r_w : float, default 0.075
        Well radius [m]. Minimum evaluation distance.

    Returns
    -------
    float or numpy.ndarray
        Calculated steady-state drawdown s [m].

    Notes
    -----
    Theis, C. V. (1935). [DOI: 10.1029/TR016i002p00519](https://doi.org/10.1029/TR016i002p00519)

    Confined aquifer (Thiem, 1906):
    $$s(r) = \\frac{Q}{2\\pi T} \\ln\\left(\\frac{R}{r}\\right)$$

    Unconfined aquifer (Dupuit, 1863):
    $$h^2(r) = H_0^2 - \\frac{Q}{\\pi K} \\ln\\left(\\frac{R}{r}\\right), \\quad s(r) = H_0 - h(r)$$
    """
    is_scalar = np.isscalar(r)
    r_arr = np.atleast_1d(np.asarray(r, dtype=float))
    r_eff = np.maximum(r_arr, max(r_w, 1e-3))

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
    r: Union[float, np.ndarray],
    t: float,
    Q: float,
    T: float,
    S: float,
    r_w: float = 0.075,
) -> Union[float, np.ndarray]:
    """Calculate transient drawdown using the Theis (1935) well function.

    Parameters
    ----------
    r : float or numpy.ndarray
        Distance from well axis [m].
    t : float
        Elapsed pumping duration [seconds].
    Q : float
        Pumping rate [m³/s].
    T : float
        Transmissivity [m²/s].
    S : float
        Storativity [-].
    r_w : float, default 0.075
        Well radius [m]. Minimum evaluation distance.

    Returns
    -------
    float or numpy.ndarray
        Transient drawdown s [m].

    Notes
    -----
    Theis, C. V. (1935). [DOI: 10.1029/TR016i002p00519](https://doi.org/10.1029/TR016i002p00519)

    $$s(r, t) = \\frac{Q}{4\\pi T} W(u), \\quad u = \\frac{r^2 S}{4 T t}$$
    where $W(u) = \\text{exp1}(u)$ is the exponential integral.
    """
    is_scalar = np.isscalar(r)
    r_arr = np.atleast_1d(np.asarray(r, dtype=float))
    r_eff = np.maximum(r_arr, max(r_w, 1e-3))

    if t <= 0:
        s = np.zeros_like(r_eff)
    else:
        u = (r_eff**2 * S) / (4.0 * T * t)
        s = (Q / (4.0 * np.pi * T)) * exp1(u)
        s = np.maximum(0.0, s)

    return float(s[0]) if is_scalar else s


def compute_drawdown_at_points(
    points: List[Tuple[float, float]],
    config: DewateringConfig,
    profile: SoilProfile,
    time_s: Optional[float] = None,
) -> np.ndarray:
    """Compute total drawdown at specified (x, y) evaluation points using superposition.

    Parameters
    ----------
    points : List[Tuple[float, float]]
        List of (x, y) coordinate pairs [m].
    config : DewateringConfig
        Dewatering configuration with well coordinates and rates.
    profile : SoilProfile
        Soil profile for hydraulic property estimation.
    time_s : float, optional
        Pumping duration [seconds]. If None, steady-state drawdown is calculated.

    Returns
    -------
    numpy.ndarray
        1D array of drawdown values [m] at each point, bounded by initial saturated thickness H0.
    """
    T = compute_transmissivity(profile, config)
    S = compute_storativity(profile, config)
    H0 = profile.total_depth - profile.gwl_depth
    R = compute_radius_of_influence(config, T, H0)

    drawdowns = []

    if config.aquifer_type == AquiferType.UNCONFINED and time_s is None:
        # Exact Dupuit quadratic head superposition: h^2 = H0^2 - sum(H0^2 - h_i^2)
        for px, py in points:
            sum_h2_drop = 0.0
            for well in config.wells:
                r = math.hypot(px - well.x, py - well.y)
                s_w = float(thiem_drawdown_single_well(
                    r, well.Q, T, R, H0, AquiferType.UNCONFINED, r_w=well.r_w
                ))
                h_w = max(0.0, H0 - s_w)
                sum_h2_drop += (H0**2 - h_w**2)
            h_tot2 = max(0.0, H0**2 - sum_h2_drop)
            s_total = min(H0 - math.sqrt(h_tot2), H0)
            drawdowns.append(max(0.0, s_total))
    else:
        # Linear drawdown superposition (confined steady-state or transient)
        if time_s is None:
            def single_well_drawdown(r: float, well: Well) -> float:
                return float(thiem_drawdown_single_well(
                    r, well.Q, T, R, H0, config.aquifer_type, r_w=well.r_w
                ))
        else:
            def single_well_drawdown(r: float, well: Well) -> float:
                return float(theis_drawdown_single_well(
                    r, time_s, well.Q, T, S, r_w=well.r_w
                ))

        for px, py in points:
            s_total = sum(
                single_well_drawdown(math.hypot(px - well.x, py - well.y), well)
                for well in config.wells
            )
            s_total = min(s_total, H0)
            drawdowns.append(max(0.0, s_total))

    return np.array(drawdowns, dtype=float)


def compute_drawdown_grid(
    x_range: Tuple[float, float],
    y_range: Tuple[float, float],
    nx: int,
    ny: int,
    config: DewateringConfig,
    profile: SoilProfile,
    time_s: Optional[float] = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute drawdown distribution across a regular 2D rectangular grid.

    Parameters
    ----------
    x_range : Tuple[float, float]
        (x_min, x_max) grid extents [m].
    y_range : Tuple[float, float]
        (y_min, y_max) grid extents [m].
    nx : int
        Number of grid divisions in x-direction.
    ny : int
        Number of grid divisions in y-direction.
    config : DewateringConfig
        Dewatering configuration.
    profile : SoilProfile
        Soil profile.
    time_s : float, optional
        Pumping time [seconds]. None for steady-state.

    Returns
    -------
    Tuple[numpy.ndarray, numpy.ndarray, numpy.ndarray]
        (X, Y, S) meshgrid arrays of shape (ny, nx), where S is the 2D drawdown array [m].
    """
    x = np.linspace(x_range[0], x_range[1], nx)
    y = np.linspace(y_range[0], y_range[1], ny)
    X, Y = np.meshgrid(x, y)
    points = list(zip(X.ravel(), Y.ravel()))
    S_flat = compute_drawdown_at_points(points, config, profile, time_s)
    S = S_flat.reshape((ny, nx))
    return X, Y, S
