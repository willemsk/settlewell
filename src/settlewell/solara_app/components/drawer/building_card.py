"""Neighboring building assessment input card component."""

import solara

from settlewell.solara_app.schemas import BuildingSchema, BuildingType
from settlewell.solara_app.state import (
    add_building,
    delete_building,
    project_state,
    update_building,
)


@solara.component
def BuildingItemCard(index: int, bldg: BuildingSchema) -> solara.Element:
    """Render structured input card for a single neighboring building."""

    def on_field_update(**kwargs) -> None:
        updated = bldg.model_copy(update=kwargs)
        update_building(bldg.id, updated)

    return solara.Column(
        style={
            "padding": "12px",
            "margin-bottom": "12px",
            "border": "1px solid rgba(124, 58, 237, 0.3)",
            "border-radius": "8px",
            "background-color": "rgba(124, 58, 237, 0.03)",
        },
        children=[
            # Top Bar: Name, Type & Delete
            solara.Row(
                justify="space-between",
                style={"align-items": "center", "margin-bottom": "8px"},
                children=[
                    solara.Row(
                        gap="8px",
                        style={"align-items": "center", "flex": "1"},
                        children=[
                            solara.Markdown(f"**#{index}**"),
                            solara.Column(
                                style={"flex": "1"},
                                children=[
                                    solara.InputText(
                                        label="Building Name",
                                        value=bldg.name,
                                        on_value=lambda v: on_field_update(name=v),
                                    )
                                ],
                            ),
                            solara.Column(
                                style={"flex": "0 0 150px"},
                                children=[
                                    solara.Select(
                                        label="Structural Type",
                                        value=bldg.structural_type.value,
                                        values=[t.value for t in BuildingType],
                                        on_value=lambda v: on_field_update(
                                            structural_type=BuildingType(v)
                                        ),
                                    )
                                ],
                            ),
                        ],
                    ),
                    solara.Button(
                        label="🗑️",
                        on_click=lambda: delete_building(bldg.id),
                        color="error",
                        outlined=True,
                    ),
                ],
            ),
            # Row 1: X-Center [m], Foundation depth [m], Length L [m]
            solara.Row(
                gap="8px",
                children=[
                    solara.Column(
                        style={"flex": "1"},
                        children=[
                            solara.InputFloat(
                                label="X-Center [m]",
                                value=bldg.x_center,
                                on_value=lambda v: on_field_update(x_center=float(v)),
                            )
                        ],
                    ),
                    solara.Column(
                        style={"flex": "1"},
                        children=[
                            solara.InputFloat(
                                label="Fnd Depth z [m]",
                                value=bldg.foundation_depth,
                                on_value=lambda v: on_field_update(
                                    foundation_depth=max(0.0, float(v))
                                ),
                            )
                        ],
                    ),
                    solara.Column(
                        style={"flex": "1"},
                        children=[
                            solara.InputFloat(
                                label="Length L [m]",
                                value=bldg.length,
                                on_value=lambda v: on_field_update(
                                    length=max(1.0, float(v))
                                ),
                            )
                        ],
                    ),
                ],
            ),
        ],
    )


@solara.component
def BuildingCard() -> solara.Element:
    """Render Neighboring Building Damage Assessment card."""
    state = project_state.value
    active_sc = state.get_active_scenario()
    buildings = active_sc.buildings

    return solara.Column(
        gap="12px",
        style={"padding": "8px 4px"},
        children=[
            solara.Row(
                justify="space-between",
                style={"align-items": "center", "margin-bottom": "8px"},
                children=[
                    solara.Markdown(f"**Neighboring Buildings:** {len(buildings)}"),
                    solara.Button(
                        label="➕ Add Building",
                        on_click=lambda: add_building(),
                        color="primary",
                    ),
                ],
            ),
            *[
                BuildingItemCard(index=idx + 1, bldg=bldg)
                for idx, bldg in enumerate(buildings)
            ],
        ],
    )
