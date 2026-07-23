"""Settlewell — Ground settlement calculation for dewatering of construction pits.

Berekening van grondverzakking door bronbemaling bij bouwputten.
"""

from .models import (
    SoilLayer,
    SoilProfile,
    Well,
    ConstructionPit,
    DewateringConfig,
    Building,
    AquiferType,
    BuildingType,
)
from .hydraulics import (
    compute_drawdown_at_points,
    compute_drawdown_grid,
    compute_transmissivity,
    compute_storativity,
    compute_radius_of_influence,
    thiem_drawdown_single_well,
    theis_drawdown_single_well,
)
from .settlement import (
    compute_initial_stress_profile,
    compute_stress_increase_from_drawdown,
    compute_layer_settlement_cc_cr,
    compute_layer_settlement_eoed,
    compute_total_settlement,
    compute_degree_of_consolidation,
    compute_settlement_vs_time,
)
from .damage import (
    DamageAssessment,
    assess_building_damage,
    classify_damage,
    SBR_THRESHOLDS,
)
from .numerical import (
    FDGrid,
    create_grid,
    solve_steady_state,
    extract_drawdown_at_points,
)
from .plotting import (
    plot_cross_section,
    plot_plan_view,
    plot_settlement_trough,
    plot_time_settlement,
    plot_effective_stress_profile,
    plot_3d_drawdown,
    plot_damage_summary,
)

__version__ = "0.1.0"

__all__ = [
    "SoilLayer",
    "SoilProfile",
    "Well",
    "ConstructionPit",
    "DewateringConfig",
    "Building",
    "AquiferType",
    "BuildingType",
    "compute_drawdown_at_points",
    "compute_drawdown_grid",
    "compute_transmissivity",
    "compute_storativity",
    "compute_radius_of_influence",
    "thiem_drawdown_single_well",
    "theis_drawdown_single_well",
    "compute_initial_stress_profile",
    "compute_stress_increase_from_drawdown",
    "compute_layer_settlement_cc_cr",
    "compute_layer_settlement_eoed",
    "compute_total_settlement",
    "compute_degree_of_consolidation",
    "compute_settlement_vs_time",
    "DamageAssessment",
    "assess_building_damage",
    "classify_damage",
    "SBR_THRESHOLDS",
    "FDGrid",
    "create_grid",
    "solve_steady_state",
    "extract_drawdown_at_points",
    "plot_cross_section",
    "plot_plan_view",
    "plot_settlement_trough",
    "plot_time_settlement",
    "plot_effective_stress_profile",
    "plot_3d_drawdown",
    "plot_damage_summary",
    "__version__",
]
