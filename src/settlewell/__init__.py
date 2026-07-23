"""Settlewell — Ground settlement calculation for dewatering of construction pits.

Berekening van grondverzakking door bronbemaling bij bouwputten.
"""

from .damage import (
    SBR_THRESHOLDS,
    DamageAssessment,
    assess_building_damage,
    classify_damage,
)
from .hydraulics import (
    compute_drawdown_at_points,
    compute_drawdown_grid,
    compute_radius_of_influence,
    compute_storativity,
    compute_transmissivity,
    theis_drawdown_single_well,
    thiem_drawdown_single_well,
)
from .models import (
    AquiferType,
    Building,
    BuildingType,
    ConstructionPit,
    DewateringConfig,
    SoilLayer,
    SoilProfile,
    Well,
)
from .numerical import (
    FDGrid,
    create_grid,
    extract_drawdown_at_points,
    solve_steady_state,
)
from .plotting import (
    plot_3d_drawdown,
    plot_cross_section,
    plot_damage_summary,
    plot_effective_stress_profile,
    plot_plan_view,
    plot_settlement_trough,
    plot_time_settlement,
)
from .settlement import (
    compute_degree_of_consolidation,
    compute_initial_stress_profile,
    compute_layer_settlement_cc_cr,
    compute_layer_settlement_eoed,
    compute_settlement_vs_time,
    compute_stress_increase_from_drawdown,
    compute_total_settlement,
)

__version__ = "0.1.0"

__all__ = [
    "SBR_THRESHOLDS",
    "AquiferType",
    "Building",
    "BuildingType",
    "ConstructionPit",
    "DamageAssessment",
    "DewateringConfig",
    "FDGrid",
    "SoilLayer",
    "SoilProfile",
    "Well",
    "__version__",
    "assess_building_damage",
    "classify_damage",
    "compute_degree_of_consolidation",
    "compute_drawdown_at_points",
    "compute_drawdown_grid",
    "compute_initial_stress_profile",
    "compute_layer_settlement_cc_cr",
    "compute_layer_settlement_eoed",
    "compute_radius_of_influence",
    "compute_settlement_vs_time",
    "compute_storativity",
    "compute_stress_increase_from_drawdown",
    "compute_total_settlement",
    "compute_transmissivity",
    "create_grid",
    "extract_drawdown_at_points",
    "plot_3d_drawdown",
    "plot_cross_section",
    "plot_damage_summary",
    "plot_effective_stress_profile",
    "plot_plan_view",
    "plot_settlement_trough",
    "plot_time_settlement",
    "solve_steady_state",
    "theis_drawdown_single_well",
    "thiem_drawdown_single_well",
]
