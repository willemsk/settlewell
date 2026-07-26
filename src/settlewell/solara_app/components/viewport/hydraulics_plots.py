"""Dewatering Hydraulics & Groundwater Drawdown visualization component."""

import plotly.graph_objects as go
import solara

from settlewell.solara_app.schemas import ScenarioSchema
from settlewell.solara_app.state import project_state, run_hydraulics_solve


def build_2d_drawdown_heatmap_fig(scenario: ScenarioSchema, results: dict) -> go.Figure:
    """Build Plotly 2D spatial groundwater drawdown contour heatmap s(x, y).

    Parameters
    ----------
    scenario : ScenarioSchema
        Active scenario configuration.
    results : dict
        Hydraulics solve output dictionary.

    Returns
    -------
    go.Figure
        Plotly Figure instance.
    """
    x_grid = results["x_grid"]
    y_grid = results["y_grid"]
    drawdown = results["drawdown_matrix"]

    fig = go.Figure(
        data=go.Contour(
            z=drawdown,
            x=x_grid,
            y=y_grid,
            colorscale="Blues",
            contours={"coloring": "heatmap", "showlabels": True},
            colorbar={"title": "Drawdown s [m]"},
        )
    )

    # Well markers
    for well in scenario.dewatering.wells:
        fig.add_trace(
            go.Scatter(
                x=[well.x],
                y=[well.y],
                mode="markers+text",
                marker={"symbol": "circle", "size": 12, "color": "#059669"},
                text=[well.name],
                textposition="top center",
                name=f"{well.name} ({well.Q} m³/h)",
                showlegend=True,
            )
        )

    # Pit outline
    pit = scenario.construction_pit
    px = [
        -pit.length / 2,
        pit.length / 2,
        pit.length / 2,
        -pit.length / 2,
        -pit.length / 2,
    ]
    py = [-pit.width / 2, -pit.width / 2, pit.width / 2, pit.width / 2, -pit.width / 2]
    fig.add_trace(
        go.Scatter(
            x=px,
            y=py,
            mode="lines",
            line={"color": "#dc2626", "width": 2, "dash": "dash"},
            name="Construction Pit Boundary",
            showlegend=True,
        )
    )

    fig.update_layout(
        title="2D Groundwater Drawdown Contour Heatmap s(x, y)",
        xaxis={"title": "X Coordinate [m]", "zeroline": True},
        yaxis={
            "title": "Y Coordinate [m]",
            "zeroline": True,
            "scaleanchor": "x",
            "scaleratio": 1,
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


def build_radial_drawdown_fig(scenario: ScenarioSchema, results: dict) -> go.Figure:
    """Build Plotly chart for Radial Drawdown Profile s(r) vs Distance.

    Parameters
    ----------
    scenario : ScenarioSchema
        Active scenario configuration.
    results : dict
        Hydraulics solve output dictionary.

    Returns
    -------
    go.Figure
        Plotly Figure instance.
    """
    r_grid = results["r_grid"]
    s_radial = results["drawdown_radial"]
    R_inf = results["R_influence_m"]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=r_grid,
            y=-s_radial,
            mode="lines+markers",
            fill="tozeroy",
            fillcolor="rgba(2, 132, 199, 0.2)",
            line={"color": "#0284c7", "width": 2.5},
            name="Lowered Water Table s(r)",
        )
    )

    fig.add_vline(
        x=R_inf,
        line_dash="dot",
        line_color="#64748b",
        annotation_text=f"R_influence = {R_inf:.1f} m",
    )

    fig.update_layout(
        title="Radial Groundwater Drawdown Profile s(r)",
        xaxis={"title": "Distance r from Pit Center [m]", "zeroline": True},
        yaxis={"title": "Drawdown s [m] (Downward)", "zeroline": True},
        margin={"l": 50, "r": 20, "t": 40, "b": 40},
        height=480,
    )
    return fig


@solara.component
def HydraulicsPlotsView() -> solara.Element:
    """Render side-by-side dual plot layout for 2D drawdown contour heatmap and radial profile."""
    state = project_state.value
    active_sc = state.get_active_scenario()
    results = run_hydraulics_solve(active_sc)

    fig_2d = build_2d_drawdown_heatmap_fig(active_sc, results)
    fig_radial = build_radial_drawdown_fig(active_sc, results)

    return solara.Row(
        style={"width": "100%", "gap": "16px"},
        children=[
            solara.Column(
                style={"flex": "1 1 50%", "min-width": "0px"},
                children=[solara.FigurePlotly(fig_2d)],
            ),
            solara.Column(
                style={"flex": "1 1 50%", "min-width": "0px"},
                children=[solara.FigurePlotly(fig_radial)],
            ),
        ],
    )
