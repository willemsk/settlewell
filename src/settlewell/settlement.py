"""Settlement calculation using Terzaghi 1D consolidation theory.

Computes effective stress changes from drawdown, then settlement per layer
using Cc/Cr (logarithmic) or Eoed (linear) approach, as well as time-dependent consolidation.
"""

import math

import numpy as np
from numpy.typing import NDArray

from .models import SoilLayer, SoilProfile

GAMMA_W: float = 9.81  # [kN/m³] Unit weight of water


def compute_initial_stress_profile(
    profile: SoilProfile,
    z_points: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute initial vertical effective and total stress profiles with depth.

    Parameters
    ----------
    profile : SoilProfile
        Soil profile containing layer sequence, unit weights, and groundwater table.
    z_points : numpy.ndarray, optional
        Specific depths [m] from ground surface (positive downward) at which to evaluate stresses.
        If None, stresses are evaluated at the midpoints of all soil layers.

    Returns
    -------
    z : numpy.ndarray
        Depths array [m].
    sigma_v_eff : numpy.ndarray
        Initial effective vertical stress array [kPa].
    sigma_v_total : numpy.ndarray
        Initial total vertical stress array [kPa].

    Notes
    -----
    Terzaghi, K. (1943). [DOI: 10.1002/9780470172766](https://doi.org/10.1002/9780470172766)

    Above the groundwater level ($z \\le z_{\\text{gw}}$):
        $$\\sigma_v(z) = \\sum \\gamma_{\\text{dry}} \\Delta z, \\quad u = 0, \\quad \\sigma'_v = \\sigma_v$$
    Below the groundwater level ($z > z_{\\text{gw}}$):
        $$\\sigma_v(z) = \\sigma_v(z_{\\text{gw}}) + \\sum \\gamma_{\\text{sat}} \\Delta z, \\quad u = \\gamma_w (z - z_{\\text{gw}}), \\quad \\sigma'_v = \\sigma_v - u$$
    """
    if z_points is None:
        z_mids = []
        curr = 0.0
        for layer in profile.layers:
            z_mids.append(curr + layer.thickness / 2.0)
            curr += layer.thickness
        z_eval = np.array(z_mids, dtype=float)
    else:
        z_eval = np.asarray(z_points, dtype=float)

    gwl = profile.gwl_depth
    sigma_v_list = []
    sigma_eff_list = []

    for z in z_eval:
        # Pore water pressure u
        if z <= gwl:
            u = 0.0
        else:
            u = GAMMA_W * (z - gwl)

        # Total vertical stress sigma_v
        sigma_v = 0.0
        curr_depth = 0.0
        for layer in profile.layers:
            top = curr_depth
            bot = curr_depth + layer.thickness
            if z <= top:
                break
            dz = min(z, bot) - top
            if top < gwl:
                dry_dz = min(dz, max(0.0, gwl - top))
                sat_dz = dz - dry_dz
                sigma_v += dry_dz * layer.gamma + sat_dz * layer.gamma_sat
            else:
                sigma_v += dz * layer.gamma_sat
            curr_depth = bot

        sigma_eff = max(0.0, sigma_v - u)
        sigma_v_list.append(sigma_v)
        sigma_eff_list.append(sigma_eff)

    return (
        z_eval,
        np.array(sigma_eff_list, dtype=float),
        np.array(sigma_v_list, dtype=float),
    )


def compute_stress_increase_from_drawdown(
    profile: SoilProfile,
    drawdown: float,
    z_points: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute increase in effective vertical stress due to groundwater drawdown.

    Parameters
    ----------
    profile : SoilProfile
        Soil profile containing initial groundwater table depth.
    drawdown : float
        Drawdown magnitude at location [m].
    z_points : numpy.ndarray, optional
        Depths [m] at which to evaluate stress increase. If None, layer midpoints are used.

    Returns
    -------
    z : numpy.ndarray
        Depths array [m].
    delta_sigma_eff : numpy.ndarray
        Effective stress increase array [kPa].

    Notes
    -----
    Terzaghi, K. (1943). [DOI: 10.1002/9780470172766](https://doi.org/10.1002/9780470172766)

    - For $z < z_{\\text{gw}}$: $\\Delta \\sigma'_v = 0$.
    - For $z_{\\text{gw}} \\le z < z_{\\text{gw}} + s$: $\\Delta \\sigma'_v = \\gamma_w (z - z_{\\text{gw}})$.
    - For $z \\ge z_{\\text{gw}} + s$: $\\Delta \\sigma'_v = \\gamma_w \\cdot s$.
    """
    if z_points is None:
        z_mids = []
        curr = 0.0
        for layer in profile.layers:
            z_mids.append(curr + layer.thickness / 2.0)
            curr += layer.thickness
        z_eval = np.array(z_mids, dtype=float)
    else:
        z_eval = np.asarray(z_points, dtype=float)

    gwl_orig = profile.gwl_depth
    gwl_new = gwl_orig + max(0.0, drawdown)
    dsigma_list = []

    for z in z_eval:
        if z < gwl_orig:
            dsigma = 0.0
        elif z >= gwl_new:
            dsigma = GAMMA_W * drawdown
        else:
            dsigma = GAMMA_W * (z - gwl_orig)
        dsigma_list.append(max(0.0, dsigma))

    return z_eval, np.array(dsigma_list, dtype=float)


def compute_layer_settlement_cc_cr(
    layer: SoilLayer,
    sigma_v0_eff: float,
    delta_sigma_v: float,
) -> float:
    """Compute 1D primary consolidation settlement using logarithmic Cc/Cr formulation.

    Parameters
    ----------
    layer : SoilLayer
        Soil layer properties (`Cc`, `Cr`, `e0`, `OCR`, `thickness`).
    sigma_v0_eff : float
        Initial vertical effective stress at layer midpoint [kPa].
    delta_sigma_v : float
        Increase in vertical effective stress [kPa].

    Returns
    -------
    float
        Primary consolidation settlement of this layer [m].

    Notes
    -----
    Terzaghi, K. (1943). [DOI: 10.1002/9780470172766](https://doi.org/10.1002/9780470172766)

    Preconsolidation pressure $\\sigma'_p = \\text{OCR} \\cdot \\sigma'_{v0}$.

    - **Case 1**: Fully Overconsolidated ($\\sigma'_{v0} + \\Delta \\sigma'_v \\le \\sigma'_p$)
      $$\\Delta s = \\frac{C_r}{1 + e_0} H \\log_{10}\\left(\\frac{\\sigma'_{v0} + \\Delta \\sigma'_v}{\\sigma'_{v0}}\\right)$$
    - **Case 2**: Fully Normally Consolidated ($\\sigma'_{v0} \\ge \\sigma'_p$)
      $$\\Delta s = \\frac{C_c}{1 + e_0} H \\log_{10}\\left(\\frac{\\sigma'_{v0} + \\Delta \\sigma'_v}{\\sigma'_{v0}}\\right)$$
    - **Case 3**: Transitional ($\\sigma'_{v0} < \\sigma'_p < \\sigma'_{v0} + \\Delta \\sigma'_v$)
      $$\\Delta s = \\frac{C_r}{1 + e_0} H \\log_{10}\\left(\\frac{\\sigma'_p}{\\sigma'_{v0}}\\right) + \\frac{C_c}{1 + e_0} H \\log_{10}\\left(\\frac{\\sigma'_{v0} + \\Delta \\sigma'_v}{\\sigma'_p}\\right)$$
    """
    if delta_sigma_v <= 0 or sigma_v0_eff <= 0:
        return 0.0

    H = layer.thickness
    e0 = layer.e0
    Cc = layer.Cc
    Cr = layer.Cr
    sigma_p = layer.OCR * sigma_v0_eff
    sigma_f = sigma_v0_eff + delta_sigma_v

    if sigma_f <= sigma_p:
        # Case 1: Fully OC
        ds = (Cr / (1.0 + e0)) * H * math.log10(sigma_f / sigma_v0_eff)
    elif sigma_v0_eff >= sigma_p:
        # Case 2: Fully NC
        ds = (Cc / (1.0 + e0)) * H * math.log10(sigma_f / sigma_v0_eff)
    else:
        # Case 3: Transitional
        ds_cr = (Cr / (1.0 + e0)) * H * math.log10(sigma_p / sigma_v0_eff)
        ds_cc = (Cc / (1.0 + e0)) * H * math.log10(sigma_f / sigma_p)
        ds = ds_cr + ds_cc

    return max(0.0, ds)


def compute_layer_settlement_eoed(
    layer: SoilLayer,
    delta_sigma_v: float,
) -> float:
    """Compute 1D layer settlement using linear constrained (oedometric) modulus.

    Parameters
    ----------
    layer : SoilLayer
        Soil layer properties (`Eoed`, `thickness`).
    delta_sigma_v : float
        Increase in vertical effective stress [kPa].

    Returns
    -------
    float
        Settlement of this layer [m].

    Notes
    -----
    Terzaghi, K. (1943). [DOI: 10.1002/9780470172766](https://doi.org/10.1002/9780470172766)

    $$\\Delta s = \\frac{\\Delta \\sigma'_v}{E_{\\text{oed}}} \\cdot H$$
    """
    if delta_sigma_v <= 0:
        return 0.0

    return max(0.0, (delta_sigma_v / layer.Eoed) * layer.thickness)


def compute_total_settlement(
    profile: SoilProfile,
    drawdown: float,
    method: str = "cc_cr",
) -> tuple[float, list[float]]:
    """Compute total vertical surface settlement across all soil layers.

    Parameters
    ----------
    profile : SoilProfile
        Multi-layer soil profile.
    drawdown : float
        Drawdown at location [m].
    method : str, default "cc_cr"
        Settlement computation method (`"cc_cr"` for non-linear logarithmic or `"eoed"` for linear).

    Returns
    -------
    total_settlement : float
        Total surface settlement [m].
    per_layer_settlements : list[float]
        List of settlement contributions [m] per layer.

    Raises
    ------
    ValueError
        If `method` is not `"cc_cr"` or `"eoed"`.
    """
    z_mids = []
    curr = 0.0
    for layer in profile.layers:
        z_mids.append(curr + layer.thickness / 2.0)
        curr += layer.thickness
    z_mids_arr = np.array(z_mids, dtype=float)

    _, sigma_v0_eff, _ = compute_initial_stress_profile(profile, z_points=z_mids_arr)
    _, delta_sigma_v = compute_stress_increase_from_drawdown(
        profile, drawdown, z_points=z_mids_arr
    )

    per_layer = []
    for i, layer in enumerate(profile.layers):
        if method == "cc_cr":
            ds = compute_layer_settlement_cc_cr(
                layer, sigma_v0_eff[i], delta_sigma_v[i]
            )
        elif method == "eoed":
            ds = compute_layer_settlement_eoed(layer, delta_sigma_v[i])
        else:
            raise ValueError(
                f"Unknown settlement method '{method}'. Must be 'cc_cr' or 'eoed'."
            )
        per_layer.append(ds)

    return sum(per_layer), per_layer


def compute_degree_of_consolidation(Tv: float) -> float:
    """Compute Terzaghi average degree of consolidation U(Tv).

    Parameters
    ----------
    Tv : float
        Dimensionless time factor $T_v = \\frac{C_v t}{H_{\\text{dr}}^2}$.

    Returns
    -------
    float
        Average degree of consolidation $U \\in [0, 1]$.

    Notes
    -----
    Terzaghi, K. (1943). [DOI: 10.1002/9780470172766](https://doi.org/10.1002/9780470172766)

    For $T_v \\le 0.2827$ ($U < 60\\%$):
        $$U = \\sqrt{\\frac{4 T_v}{\\pi}}$$
    For $T_v > 0.2827$ ($U \\ge 60\\%$):
        $$U = 1 - \\frac{8}{\\pi^2} \\exp\\left(-\\frac{\\pi^2 T_v}{4}\\right)$$
    """
    if Tv <= 0:
        return 0.0

    if Tv <= 0.2827:
        U = math.sqrt(4.0 * Tv / math.pi)
    else:
        U = 1.0 - (8.0 / (math.pi**2)) * math.exp(-(math.pi**2) * Tv / 4.0)

    return min(1.0, max(0.0, U))


def compute_settlement_vs_time(
    profile: SoilProfile,
    drawdown: float,
    times_days: np.ndarray,
    method: str = "cc_cr",
) -> np.ndarray:
    """Compute surface settlement development over time.

    Parameters
    ----------
    profile : SoilProfile
        Soil profile containing layer consolidation coefficients `Cv`.
    drawdown : float
        Groundwater drawdown [m].
    times_days : numpy.ndarray
        Array of elapsed times [days].
    method : str, default "cc_cr"
        Settlement method (`"cc_cr"` or `"eoed"`).

    Returns
    -------
    numpy.ndarray
        Settlement values [m] corresponding to each time step in `times_days`.
    """
    _total_ult, layer_ult = compute_total_settlement(profile, drawdown, method=method)
    times_s = np.asarray(times_days, dtype=float) * 86400.0
    settlements = np.zeros_like(times_s, dtype=float)

    for i, layer in enumerate(profile.layers):
        is_clay = layer.Cv > 0 and layer.k_h < 1e-5
        if is_clay:
            # Determine drainage condition based on adjacent permeable boundaries
            has_sand_above = (i == 0) or (profile.layers[i - 1].k_h >= 1e-6)
            has_sand_below = (i < len(profile.layers) - 1) and (
                profile.layers[i + 1].k_h >= 1e-6
            )

            if has_sand_above and has_sand_below:
                Hdr = layer.thickness / 2.0  # Double drainage
            else:
                Hdr = layer.thickness  # Single drainage

            for t_idx, t_sec in enumerate(times_s):
                if t_sec > 0:
                    Tv = layer.Cv * t_sec / (Hdr**2)
                    U = compute_degree_of_consolidation(Tv)
                    settlements[t_idx] += U * layer_ult[i]
                else:
                    settlements[t_idx] += 0.0
        else:
            # Immediate settlement in permeable sand/fill layers
            settlements += layer_ult[i]

    return settlements


def compute_elastic_settlement(
    profile: SoilProfile, delta_sigma_z: NDArray[np.float64]
) -> float:
    """Compute instant elastic settlement of the soil profile.

    Parameters
    ----------
    profile : SoilProfile
        The soil profile.
    delta_sigma_z : NDArray[np.float64]
        The stress increase at the midpoint of each layer [kPa]. Length must match profile.layers.

    Returns
    -------
    float
        Total elastic settlement [m].
    """
    s_e = 0.0
    for layer, dsigma in zip(profile.layers, delta_sigma_z):
        if layer.Eoed > 0 and dsigma > 0:
            s_e += (dsigma / layer.Eoed) * layer.thickness
    return s_e


def compute_secondary_creep(
    s_primary: float,
    c_alpha_to_cc: float,
    t_days: float,
    t_p_days: float = 365.0,
) -> float:
    """Compute secondary compression (creep) settlement.

    Parameters
    ----------
    s_primary : float
        Ultimate primary consolidation settlement [m].
    c_alpha_to_cc : float
        Ratio of secondary compression index to primary compression index (C_alpha / C_c).
    t_days : float
        Elapsed time [days].
    t_p_days : float, default 365.0
        Time for completion of primary consolidation [days].

    Returns
    -------
    float
        Creep settlement [m].
    """
    if t_days <= t_p_days or t_p_days <= 0 or s_primary <= 0:
        return 0.0

    s_creep = s_primary * c_alpha_to_cc * math.log10(t_days / t_p_days)
    return max(0.0, s_creep)


def compute_equivalent_cv(profile: SoilProfile) -> float:
    """Compute equivalent coefficient of consolidation (Cv_eq) for layered strata.

    Parameters
    ----------
    profile : SoilProfile
        The soil profile.

    Returns
    -------
    float
        Equivalent Cv [m^2/s].
    """
    H_total = sum(layer.thickness for layer in profile.layers)
    if H_total <= 0:
        return 0.0

    denom = 0.0
    for layer in profile.layers:
        cv_val = layer.Cv if layer.Cv > 0 else 1e-7
        denom += layer.thickness / math.sqrt(cv_val)

    if denom <= 0:
        return 0.0

    return (H_total**2) / (denom**2)


def compute_full_consolidation_curve(
    s_elastic: float,
    s_primary_ult: float,
    cv_eq: float,
    h_dr: float,
    times_days: NDArray[np.float64],
    c_alpha_to_cc: float = 0.05,
    t_p_days: float = 365.0,
) -> NDArray[np.float64]:
    """Compute full time-consolidation settlement curve (elastic + primary + creep).

    Parameters
    ----------
    s_elastic : float
        Instant elastic settlement [m].
    s_primary_ult : float
        Ultimate primary consolidation settlement [m].
    cv_eq : float
        Equivalent coefficient of consolidation [m^2/s].
    h_dr : float
        Drainage path length [m].
    times_days : np.ndarray
        Array of elapsed times [days].
    c_alpha_to_cc : float, default 0.05
        Ratio of secondary compression index C_alpha to primary compression index C_c.
    t_p_days : float, default 365.0
        Time to end of primary consolidation [days].

    Returns
    -------
    np.ndarray
        Total settlement at each time step [m].
    """
    times_arr = np.asarray(times_days, dtype=float)
    settlement_curve = np.zeros_like(times_arr, dtype=float)

    for i, t_days in enumerate(times_arr):
        if t_days <= 0:
            settlement_curve[i] = max(0.0, s_elastic)
            continue

        t_sec = t_days * 86400.0
        if h_dr <= 0:
            U = 1.0
        else:
            Tv = (cv_eq * t_sec) / (h_dr**2)
            U = compute_degree_of_consolidation(Tv)

        s_primary = s_primary_ult * U
        s_creep = compute_secondary_creep(
            s_primary_ult, c_alpha_to_cc, t_days, t_p_days
        )
        settlement_curve[i] = max(0.0, s_elastic + s_primary + s_creep)

    return settlement_curve
