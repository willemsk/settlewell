"""Unit test suite for Dewatering Hydraulics, Construction Pit & Building Damage Assessment."""

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
)


def test_project_hydraulics_solve() -> None:
    """Verify 2D drawdown grid and radial profile calculation via Project."""
    state = project_state.value
    scenario = state.get_active_scenario()
    project = scenario.to_project()

    results = project.solve_hydraulics()

    assert results.T > 0.0
    assert results.R > 0.0


def test_project_building_damage_solve() -> None:
    """Verify building differential settlement, tilt, and damage classification via Project."""
    state = project_state.value
    scenario = state.get_active_scenario()
    project = scenario.to_project()

    results = project.solve()

    assert results.damage is not None
    assert len(results.damage.assessments) > 0


def test_hydraulics_plots_fig_generation() -> None:
    """Verify 2D drawdown heatmap and radial profile figure creation."""
    state = project_state.value
    scenario = state.get_active_scenario()
    project = scenario.to_project()
    results = project.solve_hydraulics()

    fig_2d = build_2d_drawdown_heatmap_fig(scenario, results)
    assert fig_2d is not None

    fig_radial = build_radial_drawdown_fig(scenario, results)
    assert fig_radial is not None


def test_damage_plots_fig_generation() -> None:
    """Verify Burland damage risk chart and building settlement profile figure creation."""
    state = project_state.value
    scenario = state.get_active_scenario()
    project = scenario.to_project()
    results = project.solve()

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
