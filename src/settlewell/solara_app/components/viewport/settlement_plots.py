"""Settlement Profiles & Time-Consolidation dashboard component."""

import numpy as np
import plotly.graph_objects as go
import solara

from settlewell.solara_app.schemas import ScenarioSchema
from settlewell.solara_app.state import (
    project_state,
    run_fast_elastic_solve,
    run_full_consolidation_solve,
)


def build_surface_settlement_bowl_fig(
    scenario: ScenarioSchema, elastic_res: dict
) -> go.Figure:
    """Build Plotly chart for Surface Settlement Bowl s(x) vs distance x.

    Parameters
    ----------
    scenario : ScenarioSchema
        Active scenario configuration.
    elastic_res : dict
        Fast elastic solve output dictionary.

    Returns
    -------
    go.Figure
        Plotly Figure instance.
    """
    settings = scenario.solver_settings
    x_grid = np.linspace(settings.x_min, settings.x_max, 80)
    s_max_mm = elastic_res["elastic_settlement_mm"]

    # Boussinesq surface settlement bowl profile s(x) = s_max / (1 + (x/B)^2)
    primary_B = scenario.loads[0].width_B if scenario.loads else 4.0
    primary_x0 = scenario.loads[0].x_center if scenario.loads else 0.0

    s_bowl_mm = s_max_mm / (
        1.0 + ((x_grid - primary_x0) / max(0.5, primary_B / 2.0)) ** 2
    )

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x_grid,
            y=-s_bowl_mm,
            fill="tozeroy",
            fillcolor="rgba(2, 132, 199, 0.2)",
            line={"color": "#0284c7", "width": 2.5},
            name="Surface Settlement s(x)",
        )
    )

    fig.update_layout(
        title="Surface Settlement Bowl s(x)",
        xaxis={"title": "Horizontal Distance X [m]", "zeroline": True},
        yaxis={"title": "Settlement s [mm] (Downward)", "zeroline": True},
        margin={"l": 50, "r": 20, "t": 40, "b": 40},
        height=280,
    )
    return fig


def build_layer_breakdown_fig(
    scenario: ScenarioSchema, consolidation_res: dict
) -> go.Figure:
    """Build layer-by-layer stacked bar chart showing Elastic, Primary, and Creep settlement components.

    Parameters
    ----------
    scenario : ScenarioSchema
        Active scenario configuration.
    consolidation_res : dict
        Full consolidation solve output dictionary.

    Returns
    -------
    go.Figure
        Plotly Figure instance.
    """
    layers_data = consolidation_res["layer_settlements"]
    layer_names = [item["name"] for item in layers_data]
    s_elastic = [item["elastic_mm"] for item in layers_data]
    s_primary = [item["consolidation_mm"] for item in layers_data]
    s_creep = [item["creep_mm"] for item in layers_data]

    fig = go.Figure(
        data=[
            go.Bar(
                name="Elastic (se)", x=layer_names, y=s_elastic, marker_color="#3b82f6"
            ),
            go.Bar(
                name="Primary Consolidation (sc)",
                x=layer_names,
                y=s_primary,
                marker_color="#f59e0b",
            ),
            go.Bar(
                name="Secondary Creep (ss)",
                x=layer_names,
                y=s_creep,
                marker_color="#84cc16",
            ),
        ]
    )

    fig.update_layout(
        barmode="stack",
        title="Layer Settlement Breakdown [mm]",
        xaxis={"title": "Soil Strata Layer"},
        yaxis={"title": "Settlement [mm]"},
        margin={"l": 50, "r": 20, "t": 40, "b": 40},
        height=280,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1.0,
        },
    )
    return fig


def build_time_consolidation_fig(
    scenario: ScenarioSchema, consolidation_res: dict
) -> go.Figure:
    """Build Plotly chart for Time-Consolidation curve (s vs log t from 1 day to 50 years).

    Parameters
    ----------
    scenario : ScenarioSchema
        Active scenario configuration.
    consolidation_res : dict
        Full consolidation solve output dictionary.

    Returns
    -------
    go.Figure
        Plotly Figure instance.
    """
    time_years = consolidation_res["time_years"]
    settlement_mm = consolidation_res["settlement_mm"]
    U_percent = consolidation_res["U_percent"]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=time_years,
            y=-settlement_mm,
            mode="lines+markers",
            name="Settlement s(t) [mm]",
            line={"color": "#dc2626", "width": 2.5},
            marker={"size": 4},
        )
    )

    fig.add_trace(
        go.Scatter(
            x=time_years,
            y=U_percent,
            mode="lines",
            name="Degree of Consolidation U [%]",
            line={"color": "#16a34a", "width": 2, "dash": "dash"},
            yaxis="y2",
        )
    )

    fig.update_layout(
        title="Settlement vs. Logarithmic Time Development (1 Day to 50 Years)",
        xaxis={"title": "Time [Years] (Log Scale)", "type": "log"},
        yaxis={"title": "Settlement s [mm] (Downward)", "zeroline": True},
        yaxis2={
            "title": "Degree of Consolidation U [%]",
            "overlaying": "y",
            "side": "right",
            "range": [0, 105],
        },
        margin={"l": 50, "r": 50, "t": 40, "b": 40},
        height=320,
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
def SettlementPlotsView() -> solara.Element:
    """Render 2x2 dashboard grid for settlement bowl, layer breakdown, and time-consolidation."""
    state = project_state.value
    active_sc = state.get_active_scenario()

    elastic_res = run_fast_elastic_solve(active_sc)
    consolidation_res = run_full_consolidation_solve(active_sc)

    fig_bowl = build_surface_settlement_bowl_fig(active_sc, elastic_res)
    fig_breakdown = build_layer_breakdown_fig(active_sc, consolidation_res)
    fig_time = build_time_consolidation_fig(active_sc, consolidation_res)

    return solara.Column(
        gap="16px",
        style={"width": "100%"},
        children=[
            solara.Row(
                style={"width": "100%", "gap": "16px"},
                children=[
                    solara.Column(
                        style={"flex": "1 1 50%", "min-width": "0px"},
                        children=[solara.FigurePlotly(fig_bowl)],
                    ),
                    solara.Column(
                        style={"flex": "1 1 50%", "min-width": "0px"},
                        children=[solara.FigurePlotly(fig_breakdown)],
                    ),
                ],
            ),
            solara.Column(
                style={"width": "100%"}, children=[solara.FigurePlotly(fig_time)]
            ),
        ],
    )
