"""Solara web application package for settlewell."""

import solara

from .components.drawer import DrawerContainer
from .components.viewport import ViewportContainer
from .state import (
    create_new_scenario,
    display_elevation_mtaw,
    duplicate_scenario,
    project_state,
    save_project_json,
    set_elevation_display_mode,
    switch_active_scenario,
)


@solara.component
def TopHeaderBar() -> solara.Element:
    """Render top application header toolbar with branding, scenario management, unit toggle, and persistence controls."""
    state = project_state.value
    active_sc = state.get_active_scenario()
    scenarios = state.scenarios

    json_data = save_project_json().encode("utf-8")

    return solara.Row(
        justify="space-between",
        style={
            "align-items": "center",
            "padding": "12px 20px",
            "background-color": "rgba(2, 132, 199, 0.05)",
            "border-bottom": "1px solid rgba(2, 132, 199, 0.2)",
            "margin-bottom": "16px",
            "width": "100%",
        },
        children=[
            # Left: Logo & Branding
            solara.Row(
                gap="12px",
                style={"align-items": "center"},
                children=[
                    solara.Markdown(f"### 🌊 settlewell v{state.version} Web GUI"),
                ],
            ),
            # Center: Scenario Switcher & Actions
            solara.Row(
                gap="8px",
                style={"align-items": "center"},
                children=[
                    solara.Markdown("**Scenario:**"),
                    solara.Select(
                        label="",
                        value=active_sc.id,
                        values=[sc.id for sc in scenarios],
                        on_value=switch_active_scenario,
                    ),
                    solara.Button(
                        label="➕ New",
                        on_click=lambda: create_new_scenario(),
                        color="primary",
                        outlined=True,
                    ),
                    solara.Button(
                        label="📋 Duplicate",
                        on_click=lambda: duplicate_scenario(active_sc.id),
                        outlined=True,
                    ),
                ],
            ),
            # Right: Datum Unit Switcher & File Persistence
            solara.Row(
                gap="12px",
                style={"align-items": "center"},
                children=[
                    solara.Row(
                        gap="4px",
                        style={"align-items": "center"},
                        children=[
                            solara.Markdown("**Datum:**"),
                            solara.Button(
                                label="Depth (m)"
                                if not display_elevation_mtaw.value
                                else "Elevation (mTAW)",
                                on_click=lambda: set_elevation_display_mode(
                                    not display_elevation_mtaw.value
                                ),
                                color="primary"
                                if display_elevation_mtaw.value
                                else "default",
                                outlined=True,
                            ),
                        ],
                    ),
                    solara.FileDownload(
                        data=json_data,
                        filename=f"{state.metadata.title.replace(' ', '_')}.settle",
                        label="💾 Save .settle",
                    ),
                ],
            ),
        ],
    )


@solara.component
def Page():
    """Main Solara web application page entrypoint for Jupyter notebook display and web app."""
    return solara.Column(
        style={"padding": "0px", "width": "100%"},
        children=[
            TopHeaderBar(),
            solara.Row(
                style={
                    "flex-wrap": "nowrap",
                    "gap": "16px",
                    "align-items": "flex-start",
                    "padding": "0px 16px",
                    "width": "100%",
                },
                children=[
                    solara.Column(
                        style={
                            "flex": "0 0 480px",
                            "max-width": "550px",
                            "width": "480px",
                        },
                        children=[DrawerContainer()],
                    ),
                    solara.Column(
                        style={"flex": "1 1 auto", "min-width": "0px"},
                        children=[ViewportContainer()],
                    ),
                ],
            ),
        ],
    )


def main() -> None:
    """Launch the Solara web application standalone server."""
    import solara.server.app

    solara.server.app.run(app_script="settlewell.solara_app.app:Page")


__all__ = ["Page", "TopHeaderBar", "main"]
