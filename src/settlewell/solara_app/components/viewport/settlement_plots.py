"""Settlement Profiles & Time-Consolidation dashboard component."""

import numpy as np
import plotly.graph_objects as go
import solara

from settlewell.project import ProjectResults
from settlewell.solara_app.schemas import ScenarioSchema
from settlewell.solara_app.state import project_state


def build_surface_settlement_bowl_fig(
    scenario: ScenarioSchema, results: ProjectResults
) -> go.Figure:
    """Build Plotly chart for Surface Settlement Bowl s(x) vs distance x."""
    settings = scenario.solver_settings
    x_grid = np.linspace(settings.x_min, settings.x_max, 80)
    s_max_mm = (
        (results.settlement.total_settlement * 1000.0) if results.settlement else 0.0
    )

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
    scenario: ScenarioSchema, results: ProjectResults
) -> go.Figure:
    """Build layer-by-layer stacked bar chart showing settlement per layer."""
    layer_names = [layer.name for layer in scenario.stratigraphy]
    
    if results.settlement:
        s_elastic = [val * 1000.0 for val in results.settlement.per_layer_elastic]
        s_primary = [val * 1000.0 for val in results.settlement.per_layer_settlements]
        s_creep = [val * 1000.0 for val in results.settlement.per_layer_creep]
    else:
        s_elastic = [0.0] * len(layer_names)
        s_primary = [0.0] * len(layer_names)
        s_creep = [0.0] * len(layer_names)

    fig = go.Figure(
        data=[
            go.Bar(
                name="Elastic Settlement (se)",
                x=layer_names,
                y=s_elastic,
                marker_color="#3b82f6",
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
                marker_color="#ef4444",
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
    scenario: ScenarioSchema, results: ProjectResults
) -> go.Figure:
    """Build Plotly chart for Time-Consolidation curve (s vs log t)."""
    if (
        results.settlement
        and results.settlement.times_days is not None
        and results.settlement.time_settlement_curve is not None
    ):
        times_years = results.settlement.times_days / 365.25
        settlement_mm = results.settlement.time_settlement_curve * 1000.0
        u_curve = results.settlement.degree_of_consolidation_curve
    else:
        times_years = np.linspace(0.01, 50.0, 50)
        settlement_mm = np.zeros_like(times_years)
        u_curve = np.zeros_like(times_years)

    from plotly.subplots import make_subplots

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(
            x=times_years,
            y=-settlement_mm,
            mode="lines+markers",
            name="Settlement s(t) [mm]",
            line={"color": "#dc2626", "width": 2.5},
            marker={"size": 4},
        ),
        secondary_y=False,
    )

    if u_curve is not None:
        fig.add_trace(
            go.Scatter(
                x=times_years,
                y=u_curve,
                mode="lines",
                name="Degree of Consolidation U [%]",
                line={"color": "#10b981", "width": 2, "dash": "dot"},
            ),
            secondary_y=True,
        )

    fig.update_layout(
        title="Settlement vs. Logarithmic Time Development (1 Day to 50 Years)",
        xaxis={"title": "Time [Years] (Log Scale)", "type": "log"},
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
    
    fig.update_yaxes(title_text="Settlement s [mm] (Downward)", zeroline=True, secondary_y=False)
    fig.update_yaxes(title_text="U [%]", range=[0, 105], secondary_y=True)
    
    return fig


@solara.component
def SettlementPlotsView() -> solara.Element:
    """Render 2x2 dashboard grid for settlement bowl, layer breakdown, and time-consolidation."""
    state = project_state.value
    active_sc = state.get_active_scenario()
    project = active_sc.to_project()
    results = project.solve()

    fig_bowl = build_surface_settlement_bowl_fig(active_sc, results)
    fig_breakdown = build_layer_breakdown_fig(active_sc, results)
    fig_time = build_time_consolidation_fig(active_sc, results)

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
