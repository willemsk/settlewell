"""Stress Profiles & Stress Bulb Heatmap visualization view component."""

import plotly.graph_objects as go
import solara

from settlewell.solara_app.schemas import ScenarioSchema
from settlewell.solara_app.state import project_state, run_fast_elastic_solve


def build_1d_stress_profile_fig(scenario: ScenarioSchema, results: dict) -> go.Figure:
    """Build Plotly chart for 1D vertical depth stress profile curves.

    Parameters
    ----------
    scenario : ScenarioSchema
        Active scenario configuration.
    results : dict
        Fast elastic solve output dictionary.

    Returns
    -------
    go.Figure
        Plotly Figure instance.
    """
    z_grid = results["z_grid"]
    sigma_v0_eff = results["sigma_v0_eff"]
    sigma_v_total = results["sigma_v_total"]
    delta_sigma_z = results["delta_sigma_z"]

    fig = go.Figure()

    # Initial Effective Stress
    fig.add_trace(
        go.Scatter(
            x=sigma_v0_eff,
            y=-z_grid,
            mode="lines",
            name="Effective Overburden σ'v0",
            line={"color": "#0284c7", "width": 2},
        )
    )

    # Initial Total Stress
    fig.add_trace(
        go.Scatter(
            x=sigma_v_total,
            y=-z_grid,
            mode="lines",
            name="Total Overburden σv0",
            line={"color": "#64748b", "width": 2, "dash": "dash"},
        )
    )

    # Induced Delta Stress
    fig.add_trace(
        go.Scatter(
            x=delta_sigma_z,
            y=-z_grid,
            mode="lines",
            name="Induced Stress Δσz",
            line={"color": "#dc2626", "width": 2.5},
        )
    )

    fig.update_layout(
        title="Vertical Stress Profiles vs. Depth Z",
        xaxis={"title": "Stress [kPa]", "zeroline": True},
        yaxis={"title": "Elevation / Depth Z [m]", "zeroline": True},
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


def build_2d_stress_heatmap_fig(scenario: ScenarioSchema, results: dict) -> go.Figure:
    """Build Plotly 2D contour heatmap of stress ratio Δσz / q.

    Parameters
    ----------
    scenario : ScenarioSchema
        Active scenario configuration.
    results : dict
        Fast elastic solve output dictionary.

    Returns
    -------
    go.Figure
        Plotly Figure instance.
    """
    z_grid = results["z_grid"]
    x_grid = results["x_grid"]
    heatmap = results["stress_heatmap"]

    fig = go.Figure(
        data=go.Contour(
            z=heatmap,
            x=x_grid,
            y=-z_grid,
            colorscale="Viridis",
            contours={"coloring": "heatmap", "showlabels": True},
            colorbar={"title": "Ratio Δσz / q"},
        )
    )

    fig.update_layout(
        title="2D Boussinesq Stress Ratio Heatmap Contour",
        xaxis={"title": "Horizontal Distance X [m]", "zeroline": True},
        yaxis={"title": "Elevation / Depth Z [m]", "zeroline": True},
        margin={"l": 50, "r": 20, "t": 40, "b": 40},
        height=480,
    )
    return fig


@solara.component
def StressPlotsView() -> solara.Element:
    """Render side-by-side dual plot layout for stress profiles and 2D contour heatmap."""
    state = project_state.value
    active_sc = state.get_active_scenario()
    results = run_fast_elastic_solve(active_sc)

    fig_1d = build_1d_stress_profile_fig(active_sc, results)
    fig_2d = build_2d_stress_heatmap_fig(active_sc, results)

    return solara.Row(
        style={"width": "100%", "gap": "16px"},
        children=[
            solara.Column(
                style={"flex": "1 1 50%", "min-width": "0px"},
                children=[solara.FigurePlotly(fig_1d)],
            ),
            solara.Column(
                style={"flex": "1 1 50%", "min-width": "0px"},
                children=[solara.FigurePlotly(fig_2d)],
            ),
        ],
    )
