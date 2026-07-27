"""Subsoil Canvas Viewport package assembling CanvasToolbar and SubsoilCanvas."""

import solara

from settlewell.solara_app.components.canvas.canvas_toolbar import (
    CanvasToolbar,
    active_overlays,
)
from settlewell.solara_app.components.canvas.subsoil_canvas import (
    SubsoilCanvas,
    build_subsoil_cross_section_fig,
)


@solara.component
def SubsoilCanvasContainer() -> solara.Element:
    """Render toolbar and 2D subsoil cross-section viewport."""
    overlays = active_overlays.value

    return solara.Column(
        gap="12px",
        style={"padding": "12px", "width": "100%"},
        children=[
            CanvasToolbar(),
            SubsoilCanvas(
                show_dimensions="Dimensions" in overlays,
                show_uscs_colors="USCS Colors" in overlays,
                show_stress_bulbs="Stress Bulbs" in overlays,
                show_water_table="Water Table" in overlays,
            ),
        ],
    )


__all__ = [
    "SubsoilCanvasContainer",
    "SubsoilCanvas",
    "CanvasToolbar",
    "build_subsoil_cross_section_fig",
]
