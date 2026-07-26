"""Unit test suite for Sprint 4: Viewport Components, Core Solver Integration & Plotly Figures."""

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
    run_fast_elastic_solve,
    run_full_consolidation_solve,
)


def test_run_fast_elastic_solve() -> None:
    """Verify real-time fast elastic stress and settlement calculation."""
    state = project_state.value
    scenario = state.get_active_scenario()

    results = run_fast_elastic_solve(scenario)

    assert "z_grid" in results
    assert "sigma_v0_eff" in results
    assert "delta_sigma_z" in results
    assert "elastic_settlement_mm" in results
    assert len(results["z_grid"]) > 0
    assert results["elastic_settlement_mm"] >= 0.0


def test_run_full_consolidation_solve() -> None:
    """Verify deep numerical time-consolidation solve."""
    state = project_state.value
    scenario = state.get_active_scenario()

    results = run_full_consolidation_solve(scenario)

    assert "time_years" in results
    assert "settlement_mm" in results
    assert "U_percent" in results
    assert "layer_settlements" in results
    assert len(results["time_years"]) > 0
    assert len(results["layer_settlements"]) == len(scenario.stratigraphy)


def test_stress_plots_fig_generation() -> None:
    """Verify Plotly 1D stress curve and 2D contour heatmap creation."""
    state = project_state.value
    scenario = state.get_active_scenario()
    results = run_fast_elastic_solve(scenario)

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
    elastic_res = run_fast_elastic_solve(scenario)
    consolidation_res = run_full_consolidation_solve(scenario)

    fig_bowl = build_surface_settlement_bowl_fig(scenario, elastic_res)
    assert fig_bowl is not None

    fig_breakdown = build_layer_breakdown_fig(scenario, consolidation_res)
    assert fig_breakdown is not None

    fig_time = build_time_consolidation_fig(scenario, consolidation_res)
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
