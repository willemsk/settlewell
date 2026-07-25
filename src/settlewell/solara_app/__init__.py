"""Solara web application package for settlewell."""

import solara


@solara.component
def Page():
    """Main Solara web application page entrypoint for Jupyter notebook display and web app."""
    from settlewell.solara_app.components.drawer import DrawerContainer
    from settlewell.solara_app.state import project_state

    state = project_state.value
    active_sc = state.get_active_scenario()

    return solara.Column(
        children=[
            solara.Markdown(f"# settlewell v{state.version} Web GUI"),
            solara.Markdown(
                f"**Project:** {state.metadata.title} | **Engineer:** {state.metadata.engineer} | **Scenario:** {active_sc.name}"
            ),
            DrawerContainer(),
        ],
        style={"padding": "24px"},
    )


def main() -> None:
    """Launch the Solara web application standalone server."""
    import solara.server.app

    solara.server.app.run(app_script=f"{__name__}:Page")


__all__ = ["Page", "main"]
