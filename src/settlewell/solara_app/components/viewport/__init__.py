"""Right Viewport multi-tab results dashboard component container."""

import time

import solara

from settlewell.solara_app.components.canvas import SubsoilCanvasContainer
from settlewell.solara_app.components.viewport.damage_plots import (
    DamagePlotsView,
    build_building_settlement_profile_fig,
    build_burland_risk_chart_fig,
)
from settlewell.solara_app.components.viewport.export_view import ExportView
from settlewell.solara_app.components.viewport.hydraulics_plots import (
    HydraulicsPlotsView,
    build_2d_drawdown_heatmap_fig,
    build_radial_drawdown_fig,
)
from settlewell.solara_app.components.viewport.scenario_benchmark import (
    ScenarioBenchmarkView,
    build_scenario_comparison_fig,
)
from settlewell.solara_app.components.viewport.settlement_plots import (
    SettlementPlotsView,
    build_layer_breakdown_fig,
    build_surface_settlement_bowl_fig,
    build_time_consolidation_fig,
)
from settlewell.solara_app.components.viewport.stress_plots import (
    StressPlotsView,
    build_1d_stress_profile_fig,
    build_2d_stress_heatmap_fig,
)
from settlewell.solara_app.state import (
    project_state,
)

# Reactive active tab selection index and progress state
active_tab = solara.reactive(0)
is_solving = solara.reactive(False)
solve_progress = solara.reactive(0.0)


@solara.component
def ViewportContainer() -> solara.Element:
    """Render right viewport containing top Vuetify icon tabs and bottom solver status bar."""
    state = project_state.value
    active_sc = state.get_active_scenario()
    project = active_sc.to_project()
    res = project.solve()
    s_elastic_mm = (res.settlement.total_settlement * 1000.0) if res.settlement else 0.0

    def trigger_deep_solve() -> None:
        is_solving.set(True)
        solve_progress.set(10.0)
        time.sleep(0.05)
        solve_progress.set(50.0)
        project.solve()
        solve_progress.set(100.0)
        time.sleep(0.05)
        is_solving.set(False)

    return solara.Column(
        gap="12px",
        style={"width": "100%"},
        children=[
            # Top Icon Tabs Bar
            solara.v.Tabs(
                v_model=active_tab.value,
                on_v_model=active_tab.set,
                children=[
                    solara.v.Tab(children=["📐 2D Subsoil Canvas"]),
                    solara.v.Tab(children=["📊 Stress Profiles & Bulbs"]),
                    solara.v.Tab(children=["📉 Settlement & Consolidation"]),
                    solara.v.Tab(children=["💧 Dewatering Hydraulics"]),
                    solara.v.Tab(children=["🏚️ Building Damage"]),
                    solara.v.Tab(children=["🔀 Scenario Benchmarks"]),
                    solara.v.Tab(children=["📄 PDF, DXF & Data Export"]),
                ],
            ),
            # Progress Linear Bar
            solara.ProgressLinear(
                value=solve_progress.value if is_solving.value else 0.0,
                color="primary",
            ),
            # Selected Tab View Content
            solara.Column(
                style={"padding": "8px 0px", "width": "100%"},
                children=[
                    SubsoilCanvasContainer()
                    if active_tab.value == 0
                    else solara.Column(),
                    StressPlotsView() if active_tab.value == 1 else solara.Column(),
                    SettlementPlotsView() if active_tab.value == 2 else solara.Column(),
                    HydraulicsPlotsView() if active_tab.value == 3 else solara.Column(),
                    DamagePlotsView() if active_tab.value == 4 else solara.Column(),
                    ScenarioBenchmarkView()
                    if active_tab.value == 5
                    else solara.Column(),
                    ExportView() if active_tab.value == 6 else solara.Column(),
                ],
            ),
            # Bottom Solver Status Bar
            solara.Row(
                justify="space-between",
                style={
                    "align-items": "center",
                    "padding": "10px 16px",
                    "background-color": "rgba(2, 132, 199, 0.06)",
                    "border": "1px solid rgba(2, 132, 199, 0.2)",
                    "border-radius": "8px",
                    "margin-top": "8px",
                },
                children=[
                    solara.Row(
                        gap="8px",
                        style={"align-items": "center"},
                        children=[
                            solara.Markdown("⚡ **Real-Time Settlement:**"),
                            solara.Markdown(f"`s_total = {s_elastic_mm:.1f} mm`"),
                        ],
                    ),
                    solara.Button(
                        label="▶ Run Full Solve",
                        on_click=trigger_deep_solve,
                        color="primary",
                    ),
                ],
            ),
        ],
    )


__all__ = [
    "ViewportContainer",
    "StressPlotsView",
    "SettlementPlotsView",
    "HydraulicsPlotsView",
    "DamagePlotsView",
    "ScenarioBenchmarkView",
    "ExportView",
    "build_1d_stress_profile_fig",
    "build_2d_stress_heatmap_fig",
    "build_surface_settlement_bowl_fig",
    "build_layer_breakdown_fig",
    "build_time_consolidation_fig",
    "build_2d_drawdown_heatmap_fig",
    "build_radial_drawdown_fig",
    "build_burland_risk_chart_fig",
    "build_building_settlement_profile_fig",
    "build_scenario_comparison_fig",
]
