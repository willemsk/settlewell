"""2D Subsoil Cross-Section Plotly graphic canvas builder and Solara component."""

import numpy as np
import plotly.graph_objects as go
import solara

from settlewell.solara_app.schemas import ScenarioSchema, SoilTypeUSCS
from settlewell.solara_app.state import project_state

USCS_COLORS = {
    SoilTypeUSCS.SAND: "#f59e0b",
    SoilTypeUSCS.CLAY: "#854d0e",
    SoilTypeUSCS.GRAVEL: "#64748b",
    SoilTypeUSCS.PEAT: "#451a03",
}


def build_subsoil_cross_section_fig(
    scenario: ScenarioSchema,
    show_dimensions: bool = True,
    show_uscs_colors: bool = True,
    show_stress_bulbs: bool = False,
    show_water_table: bool = True,
    edit_mode: bool = True,
    dark_mode: bool = False,
) -> go.Figure:
    """Construct Plotly 2D subsoil cross-section figure.

    Parameters
    ----------
    scenario : ScenarioSchema
        Active scenario configuration.
    show_dimensions : bool, default True
        Render depth and width dimension annotations.
    show_uscs_colors : bool, default True
        Render USCS soil layer colors.
    show_stress_bulbs : bool, default False
        Render Boussinesq stress bulb iso-contours.
    show_water_table : bool, default True
        Render groundwater table dashed line.
    edit_mode : bool, default True
        Toggle edit handles vs read-only rich tooltips.
    dark_mode : bool, default False
        Dark theme toggle.

    Returns
    -------
    go.Figure
        Plotly 2D cross-section Figure instance.
    """
    fig = go.Figure()

    settings = scenario.solver_settings
    x_min, x_max = settings.x_min, settings.x_max

    # 1. Render Soil Strata Rectangles
    current_depth = 0.0
    for idx, layer in enumerate(scenario.stratigraphy):
        z_top = -current_depth
        z_bot = -(current_depth + layer.thickness)
        current_depth += layer.thickness

        color = (
            USCS_COLORS.get(layer.uscs_type, "#f59e0b")
            if show_uscs_colors
            else "#94a3b8"
        )

        hover_info = (
            f"<b>{layer.name}</b> ({layer.uscs_type.value})<br>"
            f"Thickness h: {layer.thickness:.2f} m<br>"
            f"γ dry: {layer.gamma_dry:.1f} kN/m³ | γ sat: {layer.gamma_sat:.1f} kN/m³<br>"
            f"E-Modulus: {layer.E_modulus:.1f} MPa | e0: {layer.e0:.2f}<br>"
            f"Cc: {layer.Cc:.3f} | Cr: {layer.Cr:.3f} | Cv: {layer.Cv:.1f} m²/yr"
        )

        fig.add_trace(
            go.Scatter(
                x=[x_min, x_max, x_max, x_min, x_min],
                y=[z_top, z_top, z_bot, z_bot, z_top],
                fill="toself",
                fillcolor=color,
                opacity=0.6,
                line={"color": "#475569", "width": 1},
                name=layer.name,
                text=hover_info,
                hoverinfo="text" if not edit_mode else "name",
                showlegend=True,
            )
        )

        # Layer depth label text
        fig.add_annotation(
            x=x_min + 1.5,
            y=(z_top + z_bot) / 2.0,
            text=f"<b>{layer.name}</b> (h={layer.thickness}m)",
            showarrow=False,
            font={"size": 11, "color": "#1e293b" if not dark_mode else "#f8fafc"},
            align="left",
        )

    total_soil_depth = current_depth

    # 2. Render Groundwater Table Line
    if show_water_table:
        z_gw = -scenario.water_table.depth_z
        fig.add_trace(
            go.Scatter(
                x=[x_min, x_max],
                y=[z_gw, z_gw],
                mode="lines+text",
                line={"color": "#0284c7", "width": 2, "dash": "dash"},
                name="Groundwater Table (GWL)",
                text=["", f"  GWL: z = {scenario.water_table.depth_z:.2f} m"],
                textposition="top right",
                textfont={"color": "#0284c7", "size": 12},
                showlegend=True,
            )
        )

    # 3. Render Applied Surface Loads
    for load in scenario.loads:
        x_left = load.x_center - (load.width_B / 2.0)
        x_right = load.x_center + (load.width_B / 2.0)
        z_load = -load.z_surface_offset
        h_footing = 0.6

        # Footing concrete block polygon
        fig.add_trace(
            go.Scatter(
                x=[x_left, x_right, x_right, x_left, x_left],
                y=[z_load, z_load, z_load + h_footing, z_load + h_footing, z_load],
                fill="toself",
                fillcolor="#dc2626",
                opacity=0.85,
                line={"color": "#991b1b", "width": 2},
                name=f"{load.name} ({load.stress_q} kPa)",
                text=f"<b>{load.name}</b><br>Type: {load.type.value}<br>Width B: {load.width_B}m | Stress q: {load.stress_q} kPa",
                hoverinfo="text",
                showlegend=True,
            )
        )

        # Downward load arrows
        for arrow_x in np.linspace(x_left + 0.2, x_right - 0.2, num=4):
            fig.add_annotation(
                x=arrow_x,
                y=z_load,
                ax=arrow_x,
                ay=z_load + h_footing + 0.8,
                xref="x",
                yref="y",
                axref="x",
                ayref="y",
                showarrow=True,
                arrowhead=2,
                arrowsize=1.2,
                arrowcolor="#dc2626",
                arrowwidth=2,
            )

    # 4. Stress Bulb Iso-contour Overlays
    if show_stress_bulbs and scenario.loads:
        primary_load = scenario.loads[0]
        B = primary_load.width_B
        x0 = primary_load.x_center

        # Boussinesq strip load stress bulb contours (delta_sigma / q = 0.8, 0.5, 0.2, 0.1)
        ratios = [0.8, 0.5, 0.2, 0.1]
        colors = [
            "rgba(220,38,38,0.3)",
            "rgba(234,88,12,0.3)",
            "rgba(234,179,8,0.25)",
            "rgba(59,130,246,0.2)",
        ]

        for ratio, bulb_color in zip(ratios, colors, strict=False):
            depth_factor = (1.5 / ratio) * (B / 2.0)
            width_factor = (B / 2.0) * (1.2 / np.sqrt(ratio))

            theta = np.linspace(0, np.pi, 50)
            bulb_x = x0 + width_factor * np.cos(theta)
            bulb_z = -depth_factor * np.sin(theta)

            fig.add_trace(
                go.Scatter(
                    x=bulb_x,
                    y=bulb_z,
                    mode="lines",
                    line={"color": "#ef4444", "width": 1, "dash": "dot"},
                    fill="toself",
                    fillcolor=bulb_color,
                    name=f"Stress Bulb Δσ/q = {ratio:.1f}",
                    hoverinfo="name",
                    showlegend=True,
                )
            )

    # 5. Dimension Lines & Depth Markers
    if show_dimensions:
        # Left boundary depth ruler
        fig.add_trace(
            go.Scatter(
                x=[x_min - 0.5, x_min - 0.5],
                y=[0, -total_soil_depth],
                mode="lines+markers",
                line={"color": "#64748b", "width": 1.5},
                marker={"symbol": "line-ew", "size": 8},
                name="Depth Dimension",
                showlegend=False,
            )
        )

    # Axis & Layout Configuration
    template = "plotly_dark" if dark_mode else "plotly_white"
    fig.update_layout(
        template=template,
        xaxis={
            "title": "Horizontal Distance X [m]",
            "range": [x_min - 1.5, x_max + 1.5],
            "zeroline": True,
            "zerolinecolor": "#94a3b8",
            "gridcolor": "#e2e8f0" if not dark_mode else "#334155",
        },
        yaxis={
            "title": "Elevation / Depth Z [m]",
            "range": [-max(total_soil_depth + 2.0, settings.z_max), 2.5],
            "zeroline": True,
            "zerolinecolor": "#94a3b8",
            "scaleanchor": "x",
            "scaleratio": 1,
            "gridcolor": "#e2e8f0" if not dark_mode else "#334155",
        },
        margin={"l": 50, "r": 20, "t": 35, "b": 50},
        height=540,
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
def SubsoilCanvas(
    show_dimensions: bool = True,
    show_uscs_colors: bool = True,
    show_stress_bulbs: bool = False,
    show_water_table: bool = True,
) -> solara.Element:
    """Render 2D Subsoil Cross-Section Plotly Canvas."""
    state = project_state.value
    active_sc = state.get_active_scenario()

    fig = build_subsoil_cross_section_fig(
        scenario=active_sc,
        show_dimensions=show_dimensions,
        show_uscs_colors=show_uscs_colors,
        show_stress_bulbs=show_stress_bulbs,
        show_water_table=show_water_table,
        edit_mode=state.edit_mode,
        dark_mode=state.dark_mode,
    )

    return solara.FigurePlotly(fig)
