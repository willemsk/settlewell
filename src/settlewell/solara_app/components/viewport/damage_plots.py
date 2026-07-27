"""Neighboring Building Damage Assessment & Burland Risk Classification component."""

import numpy as np
import plotly.graph_objects as go
import solara

from settlewell.solara_app.schemas import ScenarioSchema
from settlewell.solara_app.state import project_state, run_building_damage_solve


def build_burland_risk_chart_fig(results: dict) -> go.Figure:
    """Build Plotly Burland / Boscardin & Cording Damage Severity Classification scatter chart.

    Parameters
    ----------
    results : dict
        Building damage solve output dictionary.

    Returns
    -------
    go.Figure
        Plotly Figure instance.
    """
    fig = go.Figure()

    # Risk zones background bands (Angular distortion beta: 1/500, 1/300, 1/150, 1/100)
    fig.add_shape(
        type="rect",
        x0=0,
        x1=1 / 500,
        y0=0,
        y1=0.005,
        fillcolor="rgba(22, 163, 74, 0.15)",
        line_width=0,
    )
    fig.add_shape(
        type="rect",
        x0=1 / 500,
        x1=1 / 300,
        y0=0,
        y1=0.005,
        fillcolor="rgba(132, 204, 22, 0.15)",
        line_width=0,
    )
    fig.add_shape(
        type="rect",
        x0=1 / 300,
        x1=1 / 150,
        y0=0,
        y1=0.005,
        fillcolor="rgba(234, 179, 8, 0.15)",
        line_width=0,
    )
    fig.add_shape(
        type="rect",
        x0=1 / 150,
        x1=1 / 100,
        y0=0,
        y1=0.005,
        fillcolor="rgba(234, 88, 12, 0.15)",
        line_width=0,
    )
    fig.add_shape(
        type="rect",
        x0=1 / 100,
        x1=0.015,
        y0=0,
        y1=0.005,
        fillcolor="rgba(220, 38, 38, 0.15)",
        line_width=0,
    )

    # Plot building data points
    for bldg in results["buildings"]:
        fig.add_trace(
            go.Scatter(
                x=[bldg["angular_distortion_beta"]],
                y=[bldg["deflection_ratio"]],
                mode="markers+text",
                marker={"symbol": "diamond", "size": 14, "color": bldg["risk_color"]},
                text=[bldg["name"]],
                textposition="top right",
                name=f"{bldg['name']} ({bldg['risk_category_name']})",
                showlegend=True,
            )
        )

    fig.update_layout(
        title="Burland & Wroth / Boscardin Building Damage Risk Severity Chart",
        xaxis={
            "title": "Angular Distortion β = Δs / L [-]",
            "range": [0, 0.012],
            "zeroline": True,
        },
        yaxis={
            "title": "Deflection Ratio Δ / L [-]",
            "range": [0, 0.004],
            "zeroline": True,
        },
        margin={"l": 50, "r": 20, "t": 40, "b": 40},
        height=480,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1.0,
        },
    )
    return fig


def build_building_settlement_profile_fig(
    scenario: ScenarioSchema, results: dict
) -> go.Figure:
    """Build Plotly chart showing settlement profile under building foundation s(x_bldg).

    Parameters
    ----------
    scenario : ScenarioSchema
        Active scenario configuration.
    results : dict
        Building damage solve output dictionary.

    Returns
    -------
    go.Figure
        Plotly Figure instance.
    """
    fig = go.Figure()

    primary_B = scenario.loads[0].width_B if scenario.loads else 4.0

    for bldg in scenario.buildings:
        L_bldg = max(1.0, bldg.length)
        x_pts = np.linspace(
            bldg.x_center - L_bldg / 2.0, bldg.x_center + L_bldg / 2.0, 30
        )
        s_pts_mm = 41.2 / (1.0 + (x_pts / max(0.5, primary_B / 2.0)) ** 2)

        fig.add_trace(
            go.Scatter(
                x=x_pts,
                y=-s_pts_mm,
                mode="lines+markers",
                name=f"{bldg.name} Foundation Profile",
                line={"width": 2.5},
            )
        )

    fig.update_layout(
        title="Building Foundation Settlement Profile s(x_bldg)",
        xaxis={"title": "Horizontal Distance X [m]", "zeroline": True},
        yaxis={"title": "Settlement s [mm] (Downward)", "zeroline": True},
        margin={"l": 50, "r": 20, "t": 40, "b": 40},
        height=260,
    )
    return fig


@solara.component
def DamagePlotsView() -> solara.Element:
    """Render side-by-side layout for Burland severity chart and Building Risk Summary cards."""
    state = project_state.value
    active_sc = state.get_active_scenario()
    results = run_building_damage_solve(active_sc)

    fig_burland = build_burland_risk_chart_fig(results)
    fig_profile = build_building_settlement_profile_fig(active_sc, results)

    bldgs = results["buildings"]

    return solara.Row(
        style={"width": "100%", "gap": "16px"},
        children=[
            solara.Column(
                style={"flex": "1 1 55%", "min-width": "0px"},
                children=[solara.FigurePlotly(fig_burland)],
            ),
            solara.Column(
                style={"flex": "1 1 45%", "min-width": "0px", "gap": "12px"},
                children=[
                    solara.FigurePlotly(fig_profile),
                    solara.Markdown(
                        "### Neighboring Building Damage Assessment Summary"
                    ),
                    *[
                        solara.Column(
                            style={
                                "padding": "12px",
                                "margin-bottom": "8px",
                                "border": f"1px solid {bldg['risk_color']}",
                                "border-radius": "8px",
                                "background-color": "rgba(128, 128, 128, 0.03)",
                            },
                            children=[
                                solara.Row(
                                    justify="space-between",
                                    children=[
                                        solara.Markdown(f"**{bldg['name']}**"),
                                        solara.Markdown(
                                            f"`{bldg['risk_category_name']}`"
                                        ),
                                    ],
                                ),
                                solara.Row(
                                    justify="space-between",
                                    style={"margin-top": "4px"},
                                    children=[
                                        solara.Markdown(
                                            f"Diff Settlement Δs: **{bldg['differential_settlement_mm']:.2f} mm**"
                                        ),
                                        solara.Markdown(
                                            f"Max Tilt β: **1/{max(1.0, 1.0 / max(1e-6, bldg['angular_distortion_beta'])):.0f}**"
                                        ),
                                        solara.Markdown(
                                            f"Expected Cracks: **{bldg['expected_crack_width']}**"
                                        ),
                                    ],
                                ),
                            ],
                        )
                        for bldg in bldgs
                    ],
                ],
            ),
        ],
    )
