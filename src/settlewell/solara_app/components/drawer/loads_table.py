"""Surface & Foundation Loads editable table accordion card component."""

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
def LoadRow(load: LoadGeometrySchema) -> solara.Element:
    """Render a single editable surface load definition row."""

    def on_field_update(**kwargs) -> None:
        updated = load.model_copy(update=kwargs)
        update_load(load.id, updated)

    return solara.Row(
        gap="8px",
        style={
            "align-items": "center",
            "padding": "4px 0",
            "border-bottom": "1px solid rgba(128,128,128,0.2)",
        },
        children=[
            solara.InputText(
                label="Load Name",
                value=load.name,
                on_value=lambda v: on_field_update(name=v),
            ),
            solara.Select(
                label="Geometry Type",
                value=load.type.value,
                values=[t.value for t in LoadType],
                on_value=lambda v: on_field_update(type=LoadType(v)),
            ),
            solara.InputFloat(
                label="X-Center [m]",
                value=load.x_center,
                on_value=lambda v: on_field_update(x_center=float(v)),
            ),
            solara.InputFloat(
                label="Z-Offset [m]",
                value=load.z_surface_offset,
                on_value=lambda v: on_field_update(z_surface_offset=float(v)),
            ),
            solara.InputFloat(
                label="Width B [m]",
                value=load.width_B,
                on_value=lambda v: on_field_update(width_B=max(0.1, float(v))),
            ),
            solara.InputFloat(
                label="Length L [m]",
                value=load.length_L,
                on_value=lambda v: on_field_update(length_L=max(0.1, float(v))),
            ),
            solara.InputFloat(
                label="Stress q [kPa]",
                value=load.stress_q,
                on_value=lambda v: on_field_update(stress_q=max(0.0, float(v))),
            ),
            solara.Button(
                label="📋 Copy",
                on_click=lambda: duplicate_load(load.id),
                outlined=True,
            ),
            solara.Button(
                label="🗑️ Delete",
                on_click=lambda: delete_load(load.id),
                color="error",
                outlined=True,
            ),
        ],
    )


@solara.component
def LoadsTable() -> solara.Element:
    """Render full surface foundation loads editable table card."""
    state = project_state.value
    active_sc = state.get_active_scenario()
    loads = active_sc.loads

    return solara.Card(
        title="Surface & Foundation Loads Table",
        elevation=2,
        children=[
            solara.Column(
                children=[
                    solara.Row(
                        justify="space-between",
                        children=[
                            solara.Markdown(f"**Total Applied Loads:** {len(loads)}"),
                            solara.Button(
                                label="➕ Add Surface Load",
                                on_click=lambda: add_load(),
                                color="primary",
                            ),
                        ],
                    ),
                    solara.Markdown("---"),
                    *[LoadRow(load=ld) for ld in loads],
                ]
            )
        ],
    )
