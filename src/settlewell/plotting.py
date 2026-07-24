"""Visualization functions for dewatering settlement analysis.

All functions return Figure objects (matplotlib or plotly) — they do NOT call plt.show().
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go

from .damage import DamageAssessment
from .models import Building, ConstructionPit, DewateringConfig, SoilProfile

SOIL_COLORS: dict[str, str] = {
    "Aanvulling": "#D2B48C",  # Light brown / tan
    "Fill": "#D2B48C",
    "Zand": "#F4D03F",  # Yellow
    "Sand": "#F4D03F",
    "Klei": "#8FBC8F",  # Green-gray / Dark Sea Green
    "Clay": "#8FBC8F",
    "Veen": "#654321",  # Dark brown
    "Peat": "#654321",
}


def _get_soil_color(name: str) -> str:
    """Helper to return color based on soil layer name."""
    for key, color in SOIL_COLORS.items():
        if key.lower() in name.lower():
            return color
    return "#B0C4DE"  # Light steel blue default


def plot_cross_section(
    profile: SoilProfile,
    pit: ConstructionPit,
    config: DewateringConfig,
    building: Building,
    drawdown_at_building: float,
) -> plt.Figure:
    """Cross-section showing soil layers, water tables, pit, and building foundation.

    Parameters
    ----------
    profile : SoilProfile
        Soil profile.
    pit : ConstructionPit
        Construction pit geometry.
    config : DewateringConfig
        Dewatering configuration.
    building : Building
        Neighboring building.
    drawdown_at_building : float
        Drawdown magnitude at building location [m].

    Returns
    -------
    matplotlib.figure.Figure
        Matplotlib figure object of cross-section.
    """
    fig, ax = plt.subplots(figsize=(14, 8))

    x_min = -pit.length - 10.0
    x_max = building.x + building.length + 10.0

    # 1. Draw soil layers as horizontal bands
    curr_depth = 0.0
    for layer in profile.layers:
        top_elev = profile.surface_level_mtaw - curr_depth
        bot_elev = top_elev - layer.thickness
        color = _get_soil_color(layer.name)
        rect = mpatches.Rectangle(
            (x_min, bot_elev),
            x_max - x_min,
            layer.thickness,
            facecolor=color,
            edgecolor="gray",
            linestyle="--",
            alpha=0.6,
        )
        ax.add_patch(rect)
        ax.text(
            x_min + 2.0,
            (top_elev + bot_elev) / 2.0,
            f"{layer.name} ({layer.thickness}m)",
            va="center",
            ha="left",
            fontsize=10,
            weight="bold",
        )
        curr_depth += layer.thickness

    # 2. Draw original GWL line
    ax.axhline(
        profile.gwl_mtaw,
        color="blue",
        linestyle="--",
        linewidth=2,
        label=f"Initieel GWL ({profile.gwl_mtaw:.1f} mTAW)",
    )

    # 3. Draw lowered GWL cone (approximate curve from pit to building)
    x_cone = np.linspace(x_min, x_max, 200)
    # Simple conceptual drawdown curve for section plot
    r_pit = pit.length / 2.0
    gwl_lowered = np.zeros_like(x_cone)
    for i, x in enumerate(x_cone):
        r = abs(x - pit.center_x)
        if r <= r_pit:
            s = config.target_drawdown
        else:
            R = config.R if config.R is not None else 100.0
            s = config.target_drawdown * max(
                0.0, 1.0 - np.log(max(1.0, r / r_pit)) / np.log(max(2.0, R / r_pit))
            )
        gwl_lowered[i] = profile.gwl_mtaw - min(s, config.target_drawdown)

    ax.plot(
        x_cone,
        gwl_lowered,
        color="darkblue",
        linewidth=2.5,
        label="Verlaagd GWL (Na bemaling)",
    )
    ax.fill_between(
        x_cone,
        profile.gwl_mtaw,
        gwl_lowered,
        color="skyblue",
        alpha=0.3,
        hatch="//",
        label="Verlaagde zone",
    )

    # 4. Draw construction pit
    pit_left = pit.center_x - pit.length / 2.0
    pit_top = profile.surface_level_mtaw
    pit_bot = profile.surface_level_mtaw - pit.depth
    pit_rect = mpatches.Rectangle(
        (pit_left, pit_bot),
        pit.length,
        pit.depth,
        facecolor="white",
        edgecolor="black",
        linewidth=2,
        label="Bouwput (Pit)",
    )
    ax.add_patch(pit_rect)
    ax.text(
        pit.center_x,
        (pit_top + pit_bot) / 2.0,
        f"Bouwput\n({pit.length}m × {pit.depth}m diep)",
        ha="center",
        va="center",
        weight="bold",
    )

    # 5. Draw building and foundation
    b_left = building.x - building.length / 2.0
    b_top = profile.surface_level_mtaw + 4.0  # roof height for visual
    b_found = profile.surface_level_mtaw - building.foundation_depth
    b_rect = mpatches.Rectangle(
        (b_left, b_found),
        building.length,
        b_top - b_found,
        facecolor="lightgray",
        edgecolor="black",
        linewidth=1.5,
        label="Naburig Gebouw",
    )
    ax.add_patch(b_rect)
    # Foundation line
    ax.plot(
        [b_left, b_left + building.length],
        [b_found, b_found],
        color="black",
        linewidth=4,
        label="Fundering",
    )
    ax.text(
        building.x,
        (b_top + b_found) / 2.0,
        "Gebouw",
        ha="center",
        va="center",
        weight="bold",
    )

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(
        profile.surface_level_mtaw - profile.total_depth - 1.0,
        profile.surface_level_mtaw + 6.0,
    )
    ax.set_xlabel("Afstand (Distance) [m]", fontsize=12)
    ax.set_ylabel("Niveau (Elevation) [mTAW]", fontsize=12)
    ax.set_title(
        "Geotechnisch Profiel & Geometrie (Cross-Section)", fontsize=14, weight="bold"
    )
    ax.legend(loc="upper right", framealpha=0.9)
    ax.grid(True, linestyle=":", alpha=0.6)

    fig.tight_layout()
    return fig


def plot_plan_view(
    pit: ConstructionPit,
    config: DewateringConfig,
    building: Building,
    X_grid: np.ndarray,
    Y_grid: np.ndarray,
    drawdown_grid: np.ndarray,
    assessment: DamageAssessment,
) -> plt.Figure:
    """Plan view with pit, wells, drawdown contours, and building footprint.

    Parameters
    ----------
    pit : ConstructionPit
        Construction pit.
    config : DewateringConfig
        Dewatering configuration.
    building : Building
        Neighboring building.
    X_grid : numpy.ndarray
        2D grid X-coordinates [m].
    Y_grid : numpy.ndarray
        2D grid Y-coordinates [m].
    drawdown_grid : numpy.ndarray
        2D drawdown array [m].
    assessment : DamageAssessment
        Damage assessment object for building color.

    Returns
    -------
    matplotlib.figure.Figure
        Matplotlib figure object of plan view.
    """
    fig, ax = plt.subplots(figsize=(12, 10))

    # 1. Contour plot of drawdown
    cf = ax.contourf(X_grid, Y_grid, drawdown_grid, levels=15, cmap="Blues")
    cbar = fig.colorbar(cf, ax=ax)
    cbar.set_label("Verlaging (Drawdown) [m]", fontsize=12)

    cs = ax.contour(
        X_grid, Y_grid, drawdown_grid, levels=8, colors="darkblue", linewidths=0.8
    )
    ax.clabel(cs, inline=True, fmt="%.2fm", fontsize=9)

    # 2. Pit outline
    pit_left = pit.center_x - pit.length / 2.0
    pit_bot = pit.center_y - pit.width / 2.0
    pit_rect = mpatches.Rectangle(
        (pit_left, pit_bot),
        pit.length,
        pit.width,
        facecolor="none",
        edgecolor="black",
        linewidth=2.5,
        linestyle="-",
        label="Bouwput",
    )
    ax.add_patch(pit_rect)

    # 3. Well markers
    for i, w in enumerate(config.wells):
        ax.scatter(w.x, w.y, color="red", s=80, zorder=5, edgecolors="black")
        ax.text(
            w.x + 0.5, w.y + 0.5, f"W{i + 1}", color="red", weight="bold", fontsize=9
        )

    # 4. Building footprint
    corners = building.corner_coordinates()
    polygon = plt.Polygon(
        corners,
        closed=True,
        facecolor=assessment.risk_color,
        edgecolor="black",
        linewidth=2,
        alpha=0.8,
        label=f"Gebouw (Risico: {assessment.damage_description})",
    )
    ax.add_patch(polygon)

    # Annotate building corners with settlement values
    building.evaluation_points()  # [center, c1, c2, c3, c4]
    corner_keys = ["corner_1", "corner_2", "corner_3", "corner_4"]
    for idx, (cx, cy) in enumerate(corners):
        key = corner_keys[idx]
        s_mm = assessment.settlement_at_points.get(key, 0.0) * 1000.0
        ax.text(cx, cy, f" {s_mm:.1f}mm", fontsize=9, weight="bold", color="darkred")

    ax.set_xlabel("X-coördinaat [m]", fontsize=12)
    ax.set_ylabel("Y-coördinaat [m]", fontsize=12)
    ax.set_title(
        "Grondplan Bemaling & Verlaging (Plan View Contours)",
        fontsize=14,
        weight="bold",
    )
    ax.legend(loc="upper left")
    ax.set_aspect("equal", "box")
    ax.grid(True, linestyle=":", alpha=0.5)

    fig.tight_layout()
    return fig


def plot_settlement_trough(
    profile: SoilProfile,
    config: DewateringConfig,
    pit: ConstructionPit,
    building: Building,
    x_transect: np.ndarray,
    settlements: np.ndarray,
) -> plt.Figure:
    """Settlement profile along a transect from pit center through building.

    Parameters
    ----------
    profile : SoilProfile
        Soil profile.
    config : DewateringConfig
        Dewatering configuration.
    pit : ConstructionPit
        Construction pit.
    building : Building
        Building.
    x_transect : numpy.ndarray
        Transect distance array [m].
    settlements : numpy.ndarray
        Settlement array [m] along transect.

    Returns
    -------
    matplotlib.figure.Figure
        Matplotlib figure object.
    """
    fig, ax = plt.subplots(figsize=(14, 6))

    settlements_mm = np.asarray(settlements) * 1000.0

    # Pit extent shading
    pit_left = pit.center_x - pit.length / 2.0
    pit_right = pit.center_x + pit.length / 2.0
    ax.axvspan(pit_left, pit_right, color="gray", alpha=0.3, label="Bouwput zone")

    # Building extent shading
    b_left = building.x - building.length / 2.0
    b_right = building.x + building.length / 2.0
    ax.axvspan(b_left, b_right, color="khaki", alpha=0.4, label="Gebouw zone")

    # Plot settlement trough curve
    ax.plot(
        x_transect,
        settlements_mm,
        color="purple",
        linewidth=2.5,
        marker="o",
        markersize=4,
        label="Zetting (Settlement)",
    )

    # Invert y-axis so settlement goes downward
    ax.invert_yaxis()

    ax.set_xlabel("Afstand t.o.v. centrum bouwput [m]", fontsize=12)
    ax.set_ylabel("Zetting (Settlement) [mm]", fontsize=12)
    ax.set_title(
        "Zettingstroog Profiel (Settlement Trough Profile)", fontsize=14, weight="bold"
    )
    ax.legend(loc="lower right")
    ax.grid(True, linestyle=":", alpha=0.6)

    fig.tight_layout()
    return fig


def plot_time_settlement(
    times_days: np.ndarray,
    settlements_at_corners: dict[str, np.ndarray],
    pumping_duration_days: float,
) -> plt.Figure:
    """Time-settlement consolidation curves over time.

    Parameters
    ----------
    times_days : numpy.ndarray
        Time array [days].
    settlements_at_corners : dict[str, np.ndarray]
        Dictionary mapping point names to settlement arrays [m] over time.
    pumping_duration_days : float
        Pumping duration in days.

    Returns
    -------
    matplotlib.figure.Figure
        Matplotlib figure object.
    """
    fig, ax1 = plt.subplots(figsize=(12, 6))

    for name, s_arr in settlements_at_corners.items():
        s_mm = np.asarray(s_arr) * 1000.0
        ax1.plot(times_days, s_mm, linewidth=2, label=f"Punt: {name}")

    ax1.axvline(
        pumping_duration_days,
        color="red",
        linestyle="--",
        linewidth=1.5,
        label=f"Einde bemaling ({pumping_duration_days:.0f} dagen)",
    )

    ax1.invert_yaxis()
    ax1.set_xlabel("Tijd (Time) [dagen]", fontsize=12)
    ax1.set_ylabel("Zetting (Settlement) [mm]", fontsize=12)
    ax1.set_title(
        "Tijdsafhankelijke Consolidatie (Time-Settlement Curve)",
        fontsize=14,
        weight="bold",
    )
    ax1.legend(loc="lower right")
    ax1.grid(True, linestyle=":", alpha=0.6)

    fig.tight_layout()
    return fig


def plot_effective_stress_profile(
    profile: SoilProfile,
    z: np.ndarray,
    sigma_eff_initial: np.ndarray,
    sigma_eff_final: np.ndarray,
) -> plt.Figure:
    """Vertical effective stress profile with depth before and after drawdown.

    Parameters
    ----------
    profile : SoilProfile
        Soil profile.
    z : numpy.ndarray
        Depth array [m].
    sigma_eff_initial : numpy.ndarray
        Initial effective stress [kPa].
    sigma_eff_final : numpy.ndarray
        Final effective stress [kPa].

    Returns
    -------
    matplotlib.figure.Figure
        Matplotlib figure object.
    """
    fig, ax = plt.subplots(figsize=(8, 10))

    ax.plot(
        sigma_eff_initial,
        z,
        color="blue",
        linewidth=2.5,
        label="Initieel (Before drawdown)",
    )
    ax.plot(
        sigma_eff_final,
        z,
        color="red",
        linewidth=2.5,
        label="Na verlaging (After drawdown)",
    )

    ax.fill_betweenx(
        z,
        sigma_eff_initial,
        sigma_eff_final,
        color="lightcoral",
        alpha=0.4,
        label="Spanningstoename (Δσ')",
    )

    # Layer boundary lines
    curr_depth = 0.0
    for layer in profile.layers:
        curr_depth += layer.thickness
        ax.axhline(curr_depth, color="gray", linestyle=":", linewidth=1)
        ax.text(
            max(sigma_eff_final) * 0.05,
            curr_depth - layer.thickness / 2.0,
            layer.name,
            fontsize=9,
            style="italic",
        )

    ax.invert_yaxis()
    ax.set_xlabel("Effectieve Korrelspanning σ'v [kPa]", fontsize=12)
    ax.set_ylabel("Diepte (Depth) [m]", fontsize=12)
    ax.set_title(
        "Effectieve Spanning vs Diepte (Effective Stress Profile)",
        fontsize=14,
        weight="bold",
    )
    ax.legend(loc="lower right")
    ax.grid(True, linestyle=":", alpha=0.6)

    fig.tight_layout()
    return fig


def plot_3d_drawdown(
    X_grid: np.ndarray,
    Y_grid: np.ndarray,
    drawdown_grid: np.ndarray,
    pit: ConstructionPit,
    building: Building,
) -> go.Figure:
    """Interactive 3D surface plot of the drawdown cone using Plotly.

    Parameters
    ----------
    X_grid : numpy.ndarray
        2D X grid array [m].
    Y_grid : numpy.ndarray
        2D Y grid array [m].
    drawdown_grid : numpy.ndarray
        2D drawdown array [m].
    pit : ConstructionPit
        Construction pit.
    building : Building
        Building.

    Returns
    -------
    plotly.graph_objects.Figure
        Plotly 3D Figure object.
    """
    fig = go.Figure()

    # Drawdown cone surface (inverted z so drawdown goes down)
    fig.add_trace(
        go.Surface(
            x=X_grid,
            y=Y_grid,
            z=-drawdown_grid,
            colorscale="Blues",
            reversescale=True,
            name="Verlaging (Drawdown)",
            colorbar={"title": "Drawdown [m]"},
        )
    )

    fig.update_layout(
        title="3D Groundwater Drawdown Surface (Bemalingskegel)",
        scene={
            "xaxis_title": "X [m]",
            "yaxis_title": "Y [m]",
            "zaxis_title": "Verlaging [m]",
            "camera": {"eye": {"x": 1.5, "y": 1.5, "z": 1.2}},
        },
        margin={"l": 0, "r": 0, "b": 0, "t": 40},
    )

    return fig


def plot_3d_drawdown_mpl(
    X_grid: np.ndarray,
    Y_grid: np.ndarray,
    drawdown_grid: np.ndarray,
    pit: ConstructionPit = None,
) -> plt.Figure:
    """Native Matplotlib 3D surface plot of the drawdown cone for Qt embedding.

    Parameters
    ----------
    X_grid : numpy.ndarray
        2D X grid array [m].
    Y_grid : numpy.ndarray
        2D Y grid array [m].
    drawdown_grid : numpy.ndarray
        2D drawdown array [m].
    pit : ConstructionPit, optional
        Construction pit.

    Returns
    -------
    matplotlib.figure.Figure
        Matplotlib 3D Figure object.
    """
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection="3d")

    # Invert drawdown for z-axis so depth cone points down
    surf = ax.plot_surface(
        X_grid,
        Y_grid,
        -drawdown_grid,
        cmap="Blues_r",
        edgecolor="none",
        alpha=0.85,
    )

    ax.set_title("3D Groundwater Drawdown Surface (Bemalingskegel)")
    ax.set_xlabel("X [m]")
    ax.set_ylabel("Y [m]")
    ax.set_zlabel("Verlaging [m]")

    fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10, label="Drawdown [m]")
    fig.tight_layout()
    return fig


def plot_damage_summary(
    assessment: DamageAssessment,
) -> plt.Figure:
    """Styled summary table figure displaying damage assessment metrics.

    Parameters
    ----------
    assessment : DamageAssessment
        Damage assessment results.

    Returns
    -------
    matplotlib.figure.Figure
        Matplotlib figure object containing styled table.
    """
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.axis("off")

    table_data = [
        ["Parameter", "Waarde", "Eenheid", "Drempelwaarde", "Status"],
        [
            "Max. zetting (Max settlement)",
            f"{assessment.max_settlement * 1000.0:.1f}",
            "mm",
            "—",
            "—",
        ],
        [
            "Min. zetting (Min settlement)",
            f"{assessment.min_settlement * 1000.0:.1f}",
            "mm",
            "—",
            "—",
        ],
        [
            "Diff. zetting (Differential settlement)",
            f"{assessment.differential_settlement * 1000.0:.1f}",
            "mm",
            "—",
            "—",
        ],
        [
            "Hoekverdraaiing β (Angular distortion)",
            f"1 / {int(1.0 / max(assessment.angular_distortion, 1e-9))}",
            "—",
            "1 / 500",
            "OK" if assessment.damage_category <= 1 else "Aandacht",
        ],
        [
            "Relatieve doorbuiging Δ/L (Deflection ratio)",
            f"{assessment.deflection_ratio:.5f}",
            "—",
            "—",
            "—",
        ],
        [
            "Schadeklasse (Damage category)",
            f"Klasse {assessment.damage_category}",
            "—",
            "—",
            assessment.damage_description,
        ],
        [
            "Verwachte scheurwijdte (Crack width)",
            assessment.expected_crack_width,
            "mm",
            "—",
            "—",
        ],
    ]

    table = ax.table(
        cellText=table_data,
        loc="center",
        cellLoc="center",
        colWidths=[0.35, 0.15, 0.12, 0.18, 0.20],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.4)

    # Style header row
    for i in range(5):
        table[(0, i)].set_facecolor("#404040")
        table[(0, i)].set_text_props(color="white", weight="bold")

    # Style category row with risk color
    cat_row_idx = 6
    for j in range(5):
        table[(cat_row_idx, j)].set_facecolor(assessment.risk_color)
        table[(cat_row_idx, j)].set_text_props(
            color="white"
            if assessment.risk_color in ["red", "darkred", "black"]
            else "black",
            weight="bold",
        )

    ax.set_title(
        "Gebouw Schade-beoordeling Samenvatting (Building Damage Summary)",
        fontsize=13,
        weight="bold",
        pad=20,
    )
    fig.tight_layout()
    return fig
