"""Solara web application package for settlewell."""


def Page():
    """Main Solara web application page entrypoint for Jupyter notebook display and web app."""
    import solara

    from .state import project_state

    state = project_state.value
    active_sc = state.get_active_scenario()

    return solara.Column(
        children=[
            solara.Markdown(f"# settlewell v{state.version} Web GUI"),
            solara.Markdown(
                f"**Project:** {state.metadata.title} | **Engineer:** {state.metadata.engineer}"
            ),
            solara.Markdown(
                f"**Active Scenario:** {active_sc.name} ({len(active_sc.stratigraphy)} layers, {len(active_sc.loads)} loads)"
            ),
        ],
        style={"padding": "24px"},
    )


def main() -> None:
    """Launch the Solara web application standalone server."""
    import solara.server.app

    solara.server.app.run(app_script=f"{__name__}:Page")


__all__ = ["Page", "main"]
