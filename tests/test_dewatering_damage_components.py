"""Unit test suite for Sprint 5: Dewatering Hydraulics, Construction Pit & Building Damage Assessment."""

import reacton
from settlewell.solara_app.components.drawer.building_card import BuildingCard
from settlewell.solara_app.components.drawer.dewatering_card import DewateringCard
from settlewell.solara_app.components.viewport import (
    DamagePlotsView,
    HydraulicsPlotsView,
    ViewportContainer,
)
from settlewell.solara_app.components.viewport.damage_plots import (
    build_building_settlement_profile_fig,
    build_burland_risk_chart_fig,
)
from settlewell.solara_app.components.viewport.hydraulics_plots import (
    build_2d_drawdown_heatmap_fig,
    build_radial_drawdown_fig,
)
from settlewell.solara_app.state import (
    project_state,
    run_building_damage_solve,
    run_hydraulics_solve,
)


def test_run_hydraulics_solve() -> None:
    """Verify 2D drawdown grid and radial profile calculation."""
    state = project_state.value
    scenario = state.get_active_scenario()

    results = run_hydraulics_solve(scenario)

    assert "x_grid" in results
    assert "y_grid" in results
    assert "drawdown_matrix" in results
    assert "r_grid" in results
    assert "drawdown_radial" in results
    assert "R_influence_m" in results
    assert results["R_influence_m"] > 0.0


def test_run_building_damage_solve() -> None:
    """Verify building differential settlement, tilt, and damage classification."""
    state = project_state.value
    scenario = state.get_active_scenario()

    results = run_building_damage_solve(scenario)

    assert "buildings" in results
    assert len(results["buildings"]) > 0
    bldg_res = results["buildings"][0]
    assert "name" in bldg_res
    assert "differential_settlement_mm" in bldg_res
    assert "angular_distortion_beta" in bldg_res
    assert "deflection_ratio" in bldg_res
    assert "damage_category" in bldg_res
    assert "risk_category_name" in bldg_res


def test_hydraulics_plots_fig_generation() -> None:
    """Verify 2D drawdown heatmap and radial profile figure creation."""
    state = project_state.value
    scenario = state.get_active_scenario()
    results = run_hydraulics_solve(scenario)

    fig_2d = build_2d_drawdown_heatmap_fig(scenario, results)
    assert fig_2d is not None
    assert len(fig_2d.data) >= 1

    fig_radial = build_radial_drawdown_fig(scenario, results)
    assert fig_radial is not None
    assert len(fig_radial.data) >= 1


def test_damage_plots_fig_generation() -> None:
    """Verify Burland damage risk chart and building settlement profile figure creation."""
    state = project_state.value
    scenario = state.get_active_scenario()
    results = run_building_damage_solve(scenario)

    fig_burland = build_burland_risk_chart_fig(results)
    assert fig_burland is not None

    fig_profile = build_building_settlement_profile_fig(scenario, results)
    assert fig_profile is not None


def test_dewatering_and_building_cards_rendering() -> None:
    """Verify component tree rendering with reacton."""
    box_dewatering = reacton.render(DewateringCard())
    assert box_dewatering is not None

    box_building = reacton.render(BuildingCard())
    assert box_building is not None

    box_hydraulics_view = reacton.render(HydraulicsPlotsView())
    assert box_hydraulics_view is not None

    box_damage_view = reacton.render(DamagePlotsView())
    assert box_damage_view is not None

    box_viewport = reacton.render(ViewportContainer())
    assert box_viewport is not None
