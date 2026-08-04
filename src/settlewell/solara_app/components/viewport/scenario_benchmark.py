"""Multi-Scenario Benchmarking & Comparative Overlay view component."""

import numpy as np
import plotly.graph_objects as go
import solara

from settlewell.solara_app.schemas import ProjectState
from settlewell.solara_app.state import project_state


def build_scenario_comparison_fig(state: ProjectState) -> go.Figure:
    """Build Plotly overlay chart comparing surface settlement bowls across all scenarios."""
    fig = go.Figure()
    colors = ["#0284c7", "#f59e0b", "#16a34a", "#dc2626", "#8b5cf6"]

    for idx, sc in enumerate(state.scenarios):
        color = colors[idx % len(colors)]
        project = sc.to_project()
        res = project.solve()
        x_grid = np.linspace(sc.solver_settings.x_min, sc.solver_settings.x_max, 80)
        s_max_mm = (res.settlement.total_settlement * 1000.0) if res.settlement else 0.0
        primary_B = sc.loads[0].width_B if sc.loads else 4.0
        primary_x0 = sc.loads[0].x_center if sc.loads else 0.0

        s_bowl_mm = s_max_mm / (
            1.0 + ((x_grid - primary_x0) / max(0.5, primary_B / 2.0)) ** 2
        )

        fig.add_trace(
            go.Scatter(
                x=x_grid,
                y=-s_bowl_mm,
                mode="lines",
                name=f"{sc.name} (s_max={s_max_mm:.1f}mm)",
                line={"color": color, "width": 2.5},
            )
        )

    fig.update_layout(
        title="Multi-Scenario Surface Settlement Overlay Comparison",
        xaxis={"title": "Horizontal Distance X [m]", "zeroline": True},
        yaxis={"title": "Settlement s [mm] (Downward)", "zeroline": True},
        margin={"l": 50, "r": 20, "t": 40, "b": 40},
        height=340,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1.0,
        },
    )
    return fig


@solara.component
def ScenarioBenchmarkView() -> solara.Element:
    """Render multi-scenario comparative overlay plot and Delta Settlement Summary Table."""
    state = project_state.value
    fig_comp = build_scenario_comparison_fig(state)

    baseline_sc = state.scenarios[0] if state.scenarios else state.get_active_scenario()
    baseline_res = baseline_sc.to_project().solve()
    baseline_s_mm = (
        (baseline_res.settlement.total_settlement * 1000.0)
        if baseline_res.settlement
        else 0.0
    )

    rows = []
    for sc in state.scenarios:
        sc_res = sc.to_project().solve()
        sc_s_mm = (
            (sc_res.settlement.total_settlement * 1000.0) if sc_res.settlement else 0.0
        )
        delta_mm = sc_s_mm - baseline_s_mm
        rows.append(
            {
                "id": sc.id,
                "name": sc.name,
                "is_active": sc.id == state.active_scenario_id,
                "layers": len(sc.stratigraphy),
                "loads": len(sc.loads),
                "s_elastic_mm": f"{sc_s_mm:.2f}",
                "delta_mm": f"{delta_mm:+.2f}",
            }
        )

    return solara.Column(
        gap="16px",
        style={"width": "100%"},
        children=[
            solara.FigurePlotly(fig_comp),
            solara.Markdown("### Delta Settlement Comparison Table"),
            solara.Column(
                style={
                    "border": "1px solid rgba(128, 128, 128, 0.2)",
                    "border-radius": "8px",
                    "padding": "12px",
                    "background-color": "rgba(128, 128, 128, 0.03)",
                },
                children=[
                    solara.Row(
                        justify="space-between",
                        style={
                            "font-weight": "bold",
                            "padding-bottom": "8px",
                            "border-bottom": "1px solid rgba(128, 128, 128, 0.2)",
                        },
                        children=[
                            solara.Markdown("**Scenario Name**"),
                            solara.Markdown("**Strata Layers**"),
                            solara.Markdown("**Applied Loads**"),
                            solara.Markdown("**Elastic Settlement**"),
                            solara.Markdown("**Delta vs Baseline**"),
                        ],
                    ),
                    *[
                        solara.Row(
                            justify="space-between",
                            style={"padding": "6px 0px"},
                            children=[
                                solara.Markdown(
                                    f"**{item['name']}**"
                                    + (" (Active)" if item["is_active"] else "")
                                ),
                                solara.Markdown(str(item["layers"])),
                                solara.Markdown(str(item["loads"])),
                                solara.Markdown(f"{item['s_elastic_mm']} mm"),
                                solara.Markdown(f"`{item['delta_mm']} mm`"),
                            ],
                        )
                        for item in rows
                    ],
                ],
            ),
        ],
    )
