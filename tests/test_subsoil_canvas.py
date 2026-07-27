"""Unit tests for Solara 2D subsoil cross-section canvas and toolbar components."""

import plotly.graph_objects as go

from settlewell.solara_app.components.canvas import (
    CanvasToolbar,
    SubsoilCanvasContainer,
    build_subsoil_cross_section_fig,
)
from settlewell.solara_app.state import create_default_project_state, project_state


def test_build_subsoil_cross_section_fig_default() -> None:
    """Verify default figure generation contains expected traces and shapes."""
    project_state.set(create_default_project_state())
    active_sc = project_state.value.get_active_scenario()

    fig = build_subsoil_cross_section_fig(
        scenario=active_sc,
        show_dimensions=True,
        show_uscs_colors=True,
        show_stress_bulbs=False,
        show_water_table=True,
        edit_mode=True,
    )

    assert isinstance(fig, go.Figure)
    # Trace check: soil layer shapes/traces, groundwater line, foundation loads
    assert len(fig.data) >= 3


def test_build_subsoil_cross_section_fig_stress_bulbs() -> None:
    """Verify figure generation with stress bulb overlays enabled."""
    project_state.set(create_default_project_state())
    active_sc = project_state.value.get_active_scenario()

    fig = build_subsoil_cross_section_fig(
        scenario=active_sc,
        show_dimensions=True,
        show_uscs_colors=True,
        show_stress_bulbs=True,
        show_water_table=True,
        edit_mode=False,
    )

    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 5


def test_canvas_toolbar_component_instantiation() -> None:
    """Verify CanvasToolbar component instantiation."""
    project_state.set(create_default_project_state())
    toolbar = CanvasToolbar()
    assert toolbar is not None


def test_subsoil_canvas_component_rendering() -> None:
    """Verify SubsoilCanvasContainer renders cleanly via reacton."""
    import reacton

    project_state.set(create_default_project_state())
    container = SubsoilCanvasContainer()
    box, _ = reacton.render(container)
    assert box is not None
