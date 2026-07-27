"""Surface & Foundation Loads editable cards component."""

import solara

from settlewell.solara_app.schemas import LoadGeometrySchema, LoadType
from settlewell.solara_app.state import (
    add_load,
    delete_load,
    duplicate_load,
    project_state,
    update_load,
)


@solara.component
def LoadCard(index: int, load: LoadGeometrySchema) -> solara.Element:
    """Render a structured input card for a single surface load definition."""

    def on_field_update(**kwargs) -> None:
        updated = load.model_copy(update=kwargs)
        update_load(load.id, updated)

    return solara.Column(
        style={
            "padding": "12px",
            "margin-bottom": "12px",
            "border": "1px solid rgba(220, 38, 38, 0.3)",
            "border-radius": "8px",
            "background-color": "rgba(220, 38, 38, 0.03)",
        },
        children=[
            # Top Bar: Name, Type & Actions
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
                                        label="Load Name",
                                        value=load.name,
                                        on_value=lambda v: on_field_update(name=v),
                                    )
                                ],
                            ),
                            solara.Column(
                                style={"flex": "0 0 140px"},
                                children=[
                                    solara.Select(
                                        label="Geometry Type",
                                        value=load.type.value,
                                        values=[t.value for t in LoadType],
                                        on_value=lambda v: on_field_update(
                                            type=LoadType(v)
                                        ),
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
                                on_click=lambda: duplicate_load(load.id),
                                outlined=True,
                            ),
                            solara.Button(
                                label="🗑️",
                                on_click=lambda: delete_load(load.id),
                                color="error",
                                outlined=True,
                            ),
                        ],
                    ),
                ],
            ),
            # Row 1: X-Center, Z-Offset, Width B, Length L, Stress q
            solara.Row(
                gap="8px",
                children=[
                    solara.Column(
                        style={"flex": "1"},
                        children=[
                            solara.InputFloat(
                                label="X-Center [m]",
                                value=load.x_center,
                                on_value=lambda v: on_field_update(x_center=float(v)),
                            )
                        ],
                    ),
                    solara.Column(
                        style={"flex": "1"},
                        children=[
                            solara.InputFloat(
                                label="Z-Offset [m]",
                                value=load.z_surface_offset,
                                on_value=lambda v: on_field_update(
                                    z_surface_offset=float(v)
                                ),
                            )
                        ],
                    ),
                    solara.Column(
                        style={"flex": "1"},
                        children=[
                            solara.InputFloat(
                                label="Width B [m]",
                                value=load.width_B,
                                on_value=lambda v: on_field_update(
                                    width_B=max(0.1, float(v))
                                ),
                            )
                        ],
                    ),
                    solara.Column(
                        style={"flex": "1"},
                        children=[
                            solara.InputFloat(
                                label="Length L [m]",
                                value=load.length_L,
                                on_value=lambda v: on_field_update(
                                    length_L=max(0.1, float(v))
                                ),
                            )
                        ],
                    ),
                    solara.Column(
                        style={"flex": "1"},
                        children=[
                            solara.InputFloat(
                                label="Stress q [kPa]",
                                value=load.stress_q,
                                on_value=lambda v: on_field_update(
                                    stress_q=max(0.0, float(v))
                                ),
                            )
                        ],
                    ),
                ],
            ),
        ],
    )


@solara.component
def LoadsTable() -> solara.Element:
    """Render full surface foundation loads cards component."""
    state = project_state.value
    active_sc = state.get_active_scenario()
    loads = active_sc.loads

    return solara.Column(
        children=[
            solara.Row(
                justify="space-between",
                style={"align-items": "center", "margin-bottom": "12px"},
                children=[
                    solara.Markdown(f"**Applied Loads:** {len(loads)}"),
                    solara.Button(
                        label="➕ Add Surface Load",
                        on_click=lambda: add_load(),
                        color="primary",
                    ),
                ],
            ),
            *[LoadCard(index=idx + 1, load=load) for idx, load in enumerate(loads)],
        ]
    )
