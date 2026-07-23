"""Building damage assessment using Burland & Wroth and SBR classification.

Computes differential settlement, angular distortion, deflection ratio, and classifies damage
risk for neighboring buildings.
"""

import math
from dataclasses import dataclass
from typing import Callable, Dict, List, Tuple

import numpy as np

from .models import Building, BuildingType, DewateringConfig, SoilProfile
from .settlement import compute_initial_stress_profile, compute_total_settlement


@dataclass
class DamageAssessment:
    """Results of building damage assessment.

    Parameters
    ----------
    settlement_at_points : Dict[str, float]
        Dictionary mapping point names ("center", "corner_1"..."corner_4") to settlement [m].
    max_settlement : float
        Maximum settlement among evaluation points [m].
    min_settlement : float
        Minimum settlement among evaluation points [m].
    differential_settlement : float
        Differential settlement (max_settlement - min_settlement) [m].
    angular_distortion : float
        Maximum angular distortion beta = delta_s / L [-].
    deflection_ratio : float
        Deflection ratio delta / L [-].
    damage_category : int
        Damage category (0 to 5) per SBR / Burland & Wroth.
    damage_description : str
        Human-readable description of damage category.
    expected_crack_width : str
        Expected crack width description (e.g. "1 – 5 mm").
    risk_color : str
        Color code for visualization ("green", "yellow", "orange", "red", "darkred", "black").
    """

    settlement_at_points: Dict[str, float]
    max_settlement: float
    min_settlement: float
    differential_settlement: float
    angular_distortion: float
    deflection_ratio: float
    damage_category: int
    damage_description: str
    expected_crack_width: str
    risk_color: str


# SBR damage classification thresholds
# (threshold_beta, category, description_en, description_nl, crack_width, color)
SBR_THRESHOLDS: List[Tuple[float, int, str, str, str, str]] = [
    (1 / 500, 0, "Negligible", "Verwaarloosbaar", "< 0.1 mm", "green"),
    (1 / 333, 1, "Very slight", "Zeer licht", "0.1 – 1 mm", "yellow"),
    (1 / 250, 2, "Slight", "Licht", "1 – 5 mm", "orange"),
    (1 / 150, 3, "Moderate", "Matig", "5 – 15 mm", "red"),
    (1 / 75, 4, "Severe", "Ernstig", "15 – 25 mm", "darkred"),
    (float("inf"), 5, "Very severe", "Zeer ernstig", "> 25 mm", "black"),
]


def classify_damage(
    angular_distortion: float, building_type: BuildingType
) -> Tuple[int, str, str, str]:
    """Classify building damage risk from angular distortion.

    Parameters
    ----------
    angular_distortion : float
        Angular distortion beta = delta_s / L [-].
    building_type : BuildingType
        Building structure type (`MASONRY` or `CONCRETE_FRAME`).

    Returns
    -------
    category : int
        Damage category (0-5).
    description : str
        Damage category description.
    crack_width : str
        Expected crack width range.
    color : str
        Associated risk color.


    Notes
    -----
    Based on criteria from Burland & Wroth (1974) and SBRCURnet guidelines.

    For `CONCRETE_FRAME` structures, the building frame tolerates higher distortion,
    shifting the risk category down by 1 (category = max(0, category - 1)).
    """
    for max_beta, cat, desc_en, desc_nl, crack, color in SBR_THRESHOLDS:
        if angular_distortion < max_beta:
            if building_type == BuildingType.CONCRETE_FRAME:
                cat = max(0, cat - 1)
                for _, c, d_en, _, crk, col in SBR_THRESHOLDS:
                    if c == cat:
                        return cat, d_en, crk, col
            return cat, desc_en, crack, color

    last_entry = SBR_THRESHOLDS[-1]
    return last_entry[1], last_entry[2], last_entry[4], last_entry[5]


def assess_building_damage(
    building: Building,
    profile: SoilProfile,
    config: DewateringConfig,
    drawdown_func: Callable[[List[Tuple[float, float]]], np.ndarray],
    settlement_method: str = "cc_cr",
) -> DamageAssessment:
    """Perform building damage assessment.

    Parameters
    ----------
    building : Building
        Target building structure.
    profile : SoilProfile
        Soil profile.
    config : DewateringConfig
        Dewatering configuration.
    drawdown_func : Callable[[List[Tuple[float, float]]], np.ndarray]
        Function mapping list of (x, y) coordinates to drawdown array [m].
    settlement_method : str, default "cc_cr"
        Settlement method (`"cc_cr"` or `"eoed"`).

    Returns
    -------
    DamageAssessment
        Complete damage assessment results.
    """
    pts = building.evaluation_points()  # [center, corner1, corner2, corner3, corner4]
    drawdowns = drawdown_func(pts)

    # Precompute layer midpoints and initial stresses to avoid redundant calculations
    z_mids = []
    curr = 0.0
    for layer in profile.layers:
        z_mids.append(curr + layer.thickness / 2.0)
        curr += layer.thickness
    z_mids_arr = np.array(z_mids, dtype=float)

    _, sigma_v0_eff, _ = compute_initial_stress_profile(profile, z_points=z_mids_arr)

    settlements = [
        compute_total_settlement(
            profile,
            max(0.0, float(d)),
            method=settlement_method,
            sigma_v0_eff=sigma_v0_eff,
            z_mids_arr=z_mids_arr,
        )[0]
        for d in drawdowns
    ]

    keys = ["center", "corner_1", "corner_2", "corner_3", "corner_4"]
    s_dict = {keys[i]: settlements[i] for i in range(len(pts))}

    max_s = max(settlements)
    min_s = min(settlements)
    diff_s = max_s - min_s

    # Compute maximum angular distortion beta between any pair of evaluation points
    max_beta = 0.0
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            p1, p2 = pts[i], pts[j]
            dist = math.hypot(p1[0] - p2[0], p1[1] - p2[1])
            if dist > 1e-6:
                beta = abs(settlements[i] - settlements[j]) / dist
                if beta > max_beta:
                    max_beta = beta

    # Deflection ratio Delta / L (max settlement relative to average foundation level)
    corner_avg = sum(settlements[1:]) / 4.0 if len(settlements) > 1 else settlements[0]
    delta = abs(max_s - corner_avg)
    diag_length = math.hypot(building.length, building.width)
    deflection_ratio = delta / max(diag_length, 1e-3)

    cat, desc, crack_width, color = classify_damage(max_beta, building.building_type)

    return DamageAssessment(
        settlement_at_points=s_dict,
        max_settlement=max_s,
        min_settlement=min_s,
        differential_settlement=diff_s,
        angular_distortion=max_beta,
        deflection_ratio=deflection_ratio,
        damage_category=cat,
        damage_description=desc,
        expected_crack_width=crack_width,
        risk_color=color,
    )
