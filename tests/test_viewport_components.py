"""Unit test suite for Viewport Components, Core Solver Integration & Plotly Figures."""

import reacton

from settlewell.solara_app.components.viewport import (
    ScenarioBenchmarkView,
    SettlementPlotsView,
    StressPlotsView,
    ViewportContainer,
)
from settlewell.solara_app.components.viewport.scenario_benchmark import (
    build_scenario_comparison_fig,
)
from settlewell.solara_app.components.viewport.settlement_plots import (
    build_layer_breakdown_fig,
    build_surface_settlement_bowl_fig,
    build_time_consolidation_fig,
)
from settlewell.solara_app.components.viewport.stress_plots import (
    build_1d_stress_profile_fig,
    build_2d_stress_heatmap_fig,
)
from settlewell.solara_app.state import (
    project_state,
)


def test_project_solve_integration() -> None:
    """Verify real-time stress and settlement calculation via Project."""
    state = project_state.value
    scenario = state.get_active_scenario()
    project = scenario.to_project()

    results = project.solve()

    assert results.stress is not None
    assert results.settlement is not None
    assert len(results.stress.z) > 0
    assert results.settlement.total_settlement >= 0.0


def test_stress_plots_fig_generation() -> None:
    """Verify Plotly 1D stress curve and 2D contour heatmap creation."""
    state = project_state.value
    scenario = state.get_active_scenario()
    project = scenario.to_project()
    results = project.solve()

    fig_1d = build_1d_stress_profile_fig(scenario, results)
    assert fig_1d is not None
    assert len(fig_1d.data) >= 3  # sigma_v0, sigma_total, delta_sigma

    fig_2d = build_2d_stress_heatmap_fig(scenario, results)
    assert fig_2d is not None
    assert len(fig_2d.data) >= 1  # heatmap contour trace


def test_settlement_plots_fig_generation() -> None:
    """Verify Plotly settlement bowl, layer breakdown, and time-consolidation figure creation."""
    state = project_state.value
    scenario = state.get_active_scenario()
    project = scenario.to_project()
    results = project.solve()

    fig_bowl = build_surface_settlement_bowl_fig(scenario, results)
    assert fig_bowl is not None

    fig_breakdown = build_layer_breakdown_fig(scenario, results)
    assert fig_breakdown is not None

    fig_time = build_time_consolidation_fig(scenario, results)
    assert fig_time is not None


def test_scenario_comparison_fig_generation() -> None:
    """Verify multi-scenario overlay plot generation."""
    state = project_state.value

    fig_comp = build_scenario_comparison_fig(state)
    assert fig_comp is not None
    assert len(fig_comp.data) >= 1


def test_viewport_components_rendering() -> None:
    """Verify component tree rendering with reacton."""
    box_stress = reacton.render(StressPlotsView())
    assert box_stress is not None

    box_settlement = reacton.render(SettlementPlotsView())
    assert box_settlement is not None

    box_benchmark = reacton.render(ScenarioBenchmarkView())
    assert box_benchmark is not None

    box_viewport = reacton.render(ViewportContainer())
    assert box_viewport is not None
