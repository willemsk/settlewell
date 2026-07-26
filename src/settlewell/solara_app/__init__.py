"""Solara web application package for settlewell."""

import solara

from settlewell.solara_app.components.canvas import SubsoilCanvasContainer
from settlewell.solara_app.components.drawer import DrawerContainer
from settlewell.solara_app.state import project_state


@solara.component
def Page():
    """Main Solara web application page entrypoint for Jupyter notebook display and web app."""
    state = project_state.value
    active_sc = state.get_active_scenario()

    return solara.Column(
        style={"padding": "16px", "width": "100%"},
        children=[
            solara.Row(
                justify="space-between",
                style={"align-items": "center", "margin-bottom": "8px"},
                children=[
                    solara.Markdown(f"### 🌊 settlewell v{state.version} Web GUI"),
                    solara.Markdown(
                        f"**Project:** {state.metadata.title} | **Engineer:** {state.metadata.engineer} | **Scenario:** `{active_sc.name}`"
                    ),
                ],
            ),
            solara.Row(
                style={
                    "flex-wrap": "nowrap",
                    "gap": "16px",
                    "align-items": "flex-start",
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
                        children=[SubsoilCanvasContainer()],
                    ),
                ],
            ),
        ],
    )


def main() -> None:
    """Launch the Solara web application standalone server."""
    import solara.server.app

    solara.server.app.run(app_script="settlewell.solara_app.app:Page")


__all__ = ["Page", "main"]
