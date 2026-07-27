"""Canvas Toolbar component for toggling visual overlays and Edit/Read-Only modes."""

import solara

from settlewell.solara_app.state import project_state

# Reactive Overlay Toggle States
active_overlays = solara.reactive(["Dimensions", "USCS Colors", "Water Table"])
active_mode = solara.reactive("Edit Mode")


@solara.component
def CanvasToolbar() -> solara.Element:
    """Render toolbar with overlay multi-select buttons and Edit/Read-Only single-select mode toggle."""

    def on_mode_change(val: str) -> None:
        active_mode.set(val)
        current = project_state.value.model_copy(deep=True)
        current.edit_mode = val == "Edit Mode"
        project_state.set(current)

    return solara.Row(
        justify="space-between",
        style={
            "align-items": "center",
            "padding": "8px 12px",
            "background-color": "rgba(128, 128, 128, 0.05)",
            "border-radius": "8px",
            "flex-wrap": "wrap",
            "gap": "8px",
        },
        children=[
            solara.Row(
                gap="8px",
                style={"align-items": "center", "flex-wrap": "wrap"},
                children=[
                    solara.Markdown("**Overlays:**"),
                    solara.ToggleButtonsMultiple(
                        value=active_overlays,
                        values=[
                            "Dimensions",
                            "USCS Colors",
                            "Stress Bulbs",
                            "Water Table",
                        ],
                    ),
                ],
            ),
            solara.Row(
                gap="8px",
                style={"align-items": "center"},
                children=[
                    solara.Markdown("**Mode:**"),
                    solara.ToggleButtonsSingle(
                        value=active_mode,
                        values=["Edit Mode", "Read-Only"],
                        on_value=on_mode_change,
                    ),
                ],
            ),
        ],
    )
