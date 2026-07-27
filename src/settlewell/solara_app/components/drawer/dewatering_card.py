"""Dewatering pit geometry & well array input card component."""

import solara

from settlewell.solara_app.schemas import AquiferType, WellSchema
from settlewell.solara_app.state import (
    add_well,
    delete_well,
    duplicate_well,
    project_state,
    update_construction_pit,
    update_well,
)


@solara.component
def WellCard(index: int, well: WellSchema) -> solara.Element:
    """Render structured input card for a single dewatering well."""

    def on_field_update(**kwargs) -> None:
        updated = well.model_copy(update=kwargs)
        update_well(well.id, updated)

    return solara.Column(
        style={
            "padding": "12px",
            "margin-bottom": "12px",
            "border": "1px solid rgba(5, 150, 105, 0.3)",
            "border-radius": "8px",
            "background-color": "rgba(5, 150, 105, 0.03)",
        },
        children=[
            # Top Bar: Name & Actions
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
                                        label="Well Name",
                                        value=well.name,
                                        on_value=lambda v: on_field_update(name=v),
                                    )
                                ],
                            ),
                        ],
                    ),
                    solara.Row(
                        gap="4px",
                        children=[
                            solara.Button(
                                label="📋",
                                on_click=lambda: duplicate_well(well.id),
                                outlined=True,
                            ),
                            solara.Button(
                                label="🗑️",
                                on_click=lambda: delete_well(well.id),
                                color="error",
                                outlined=True,
                            ),
                        ],
                    ),
                ],
            ),
            # Row 1: X, Y, Q [m³/h], Casing r_w [m], Screen top/bottom
            solara.Row(
                gap="8px",
                children=[
                    solara.Column(
                        style={"flex": "1"},
                        children=[
                            solara.InputFloat(
                                label="X [m]",
                                value=well.x,
                                on_value=lambda v: on_field_update(x=float(v)),
                            )
                        ],
                    ),
                    solara.Column(
                        style={"flex": "1"},
                        children=[
                            solara.InputFloat(
                                label="Y [m]",
                                value=well.y,
                                on_value=lambda v: on_field_update(y=float(v)),
                            )
                        ],
                    ),
                    solara.Column(
                        style={"flex": "1"},
                        children=[
                            solara.InputFloat(
                                label="Q [m³/h]",
                                value=well.Q,
                                on_value=lambda v: on_field_update(
                                    Q=max(0.1, float(v))
                                ),
                            )
                        ],
                    ),
                    solara.Column(
                        style={"flex": "1"},
                        children=[
                            solara.InputFloat(
                                label="r_w [m]",
                                value=well.r_w,
                                on_value=lambda v: on_field_update(
                                    r_w=max(0.01, float(v))
                                ),
                            )
                        ],
                    ),
                ],
            ),
        ],
    )


@solara.component
def DewateringCard() -> solara.Element:
    """Render Construction Pit geometry and Dewatering Well Array card."""
    state = project_state.value
    active_sc = state.get_active_scenario()
    pit = active_sc.construction_pit
    dewatering = active_sc.dewatering

    def on_aquifer_change(val: str) -> None:
        current = project_state.value.model_copy(deep=True)
        active = current.get_active_scenario()
        active.dewatering.aquifer_type = AquiferType(val)
        project_state.set(current)

    return solara.Column(
        gap="16px",
        style={"padding": "8px 4px"},
        children=[
            solara.Markdown("##### Excavation Construction Pit Geometry"),
            solara.Row(
                gap="12px",
                children=[
                    solara.Column(
                        style={"flex": "1"},
                        children=[
                            solara.InputFloat(
                                label="Length L [m]",
                                value=pit.length,
                                on_value=lambda v: update_construction_pit(length=v),
                            )
                        ],
                    ),
                    solara.Column(
                        style={"flex": "1"},
                        children=[
                            solara.InputFloat(
                                label="Width W [m]",
                                value=pit.width,
                                on_value=lambda v: update_construction_pit(width=v),
                            )
                        ],
                    ),
                    solara.Column(
                        style={"flex": "1"},
                        children=[
                            solara.InputFloat(
                                label="Depth d [m]",
                                value=pit.depth,
                                on_value=lambda v: update_construction_pit(depth=v),
                            )
                        ],
                    ),
                ],
            ),
            solara.Markdown("##### Aquifer Hydrogeological Parameters"),
            solara.Select(
                label="Aquifer Classification",
                value=dewatering.aquifer_type.value,
                values=[t.value for t in AquiferType],
                on_value=on_aquifer_change,
            ),
            solara.Markdown("---"),
            solara.Row(
                justify="space-between",
                style={"align-items": "center", "margin-bottom": "8px"},
                children=[
                    solara.Markdown(f"**Dewatering Wells:** {len(dewatering.wells)}"),
                    solara.Button(
                        label="➕ Add Dewatering Well",
                        on_click=lambda: add_well(),
                        color="primary",
                    ),
                ],
            ),
            *[
                WellCard(index=idx + 1, well=well)
                for idx, well in enumerate(dewatering.wells)
            ],
        ],
    )
