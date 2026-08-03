"""Stress Profiles & Stress Bulb Heatmap visualization view component."""

import numpy as np
import plotly.graph_objects as go
import solara

from settlewell.project import ProjectResults
from settlewell.solara_app.schemas import ScenarioSchema
from settlewell.solara_app.state import project_state


def build_1d_stress_profile_fig(
    scenario: ScenarioSchema, results: ProjectResults
) -> go.Figure:
    """Build Plotly chart for 1D vertical depth stress profile curves."""
    if results.stress is not None:
        z_grid = results.stress.z
        sigma_v0_eff = results.stress.sigma_v0_eff
        delta_sigma_z = results.stress.delta_sigma_v
        sigma_v_total = sigma_v0_eff + delta_sigma_z
    else:
        z_grid = np.linspace(0, 20, 50)
        sigma_v0_eff = np.zeros_like(z_grid)
        sigma_v_total = np.zeros_like(z_grid)
        delta_sigma_z = np.zeros_like(z_grid)

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


def build_2d_stress_heatmap_fig(
    scenario: ScenarioSchema, results: ProjectResults
) -> go.Figure:
    """Build Plotly 2D contour heatmap of stress ratio Δσz / q."""
    from settlewell.stress import compute_stress_heatmap

    settings = scenario.solver_settings
    z_max = max(1.0, settings.z_max)
    dz = max(0.1, settings.delta_z)
    z_grid = np.arange(0, z_max + dz, dz)
    x_grid = np.linspace(settings.x_min, settings.x_max, 60)

    heatmap = compute_stress_heatmap(
        loads=scenario.loads,
        z_points=z_grid,
        x_points=x_grid,
        method=settings.stress_method,
    )

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
    project = active_sc.to_project()
    results = project.solve()

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
