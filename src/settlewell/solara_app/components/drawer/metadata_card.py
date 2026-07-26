"""Project Metadata & Groundwater accordion card component."""

import solara

from settlewell.solara_app.state import (
    project_state,
    update_metadata,
    update_water_table,
)


@solara.component
def MetadataCard() -> solara.Element:
    """Render Project Metadata and Groundwater table input fields."""
    state = project_state.value
    meta = state.metadata
    active_sc = state.get_active_scenario()

    def on_title_change(val: str) -> None:
        update_metadata(title=val)

    def on_engineer_change(val: str) -> None:
        update_metadata(engineer=val)

    def on_date_change(val: str) -> None:
        update_metadata(date=val)

    def on_water_depth_change(val: float) -> None:
        update_water_table(val)

    return solara.Column(
        gap="16px",
        style={"padding": "8px 4px"},
        children=[
            solara.InputText(
                label="Project Title",
                value=meta.title,
                on_value=on_title_change,
            ),
            solara.Row(
                gap="12px",
                children=[
                    solara.Column(
                        style={"flex": "1"},
                        children=[
                            solara.InputText(
                                label="Engineer ID",
                                value=meta.engineer,
                                on_value=on_engineer_change,
                            )
                        ],
                    ),
                    solara.Column(
                        style={"flex": "1"},
                        children=[
                            solara.InputText(
                                label="Date",
                                value=meta.date,
                                on_value=on_date_change,
                            )
                        ],
                    ),
                ],
            ),
            solara.Markdown("---"),
            solara.Markdown("##### Groundwater Table (z_gw)"),
            solara.Row(
                gap="12px",
                style={"align-items": "center"},
                children=[
                    solara.Column(
                        style={"flex": "0 0 120px"},
                        children=[
                            solara.InputFloat(
                                label="z_gw [m]",
                                value=active_sc.water_table.depth_z,
                                on_value=on_water_depth_change,
                            )
                        ],
                    ),
                    solara.Column(
                        style={"flex": "1"},
                        children=[
                            solara.SliderFloat(
                                label="Water Level Slider",
                                value=active_sc.water_table.depth_z,
                                min=0.0,
                                max=20.0,
                                step=0.1,
                                on_value=on_water_depth_change,
                            )
                        ],
                    ),
                ],
            ),
        ],
    )
