"""Subsoil Stratigraphy editable table accordion card component."""

import solara

from settlewell.solara_app.schemas import SoilLayerSchema, SoilTypeUSCS
from settlewell.solara_app.state import (
    add_soil_layer,
    delete_soil_layer,
    duplicate_soil_layer,
    project_state,
    update_soil_layer,
)


@solara.component
def StratigraphyRow(layer: SoilLayerSchema) -> solara.Element:
    """Render a single editable soil layer row."""

    def on_field_update(**kwargs) -> None:
        updated = layer.model_copy(update=kwargs)
        update_soil_layer(layer.id, updated)

    return solara.Row(
        gap="8px",
        style={
            "align-items": "center",
            "padding": "4px 0",
            "border-bottom": "1px solid rgba(128,128,128,0.2)",
        },
        children=[
            solara.InputText(
                label="Name",
                value=layer.name,
                on_value=lambda v: on_field_update(name=v),
            ),
            solara.InputFloat(
                label="h [m]",
                value=layer.thickness,
                on_value=lambda v: on_field_update(thickness=max(0.1, float(v))),
            ),
            solara.InputFloat(
                label="γ dry [kN/m³]",
                value=layer.gamma_dry,
                on_value=lambda v: on_field_update(gamma_dry=max(0.1, float(v))),
            ),
            solara.InputFloat(
                label="γ sat [kN/m³]",
                value=layer.gamma_sat,
                on_value=lambda v: on_field_update(
                    gamma_sat=max(layer.gamma_dry, float(v))
                ),
            ),
            solara.InputFloat(
                label="e0 [-]",
                value=layer.e0,
                on_value=lambda v: on_field_update(e0=max(0.0, float(v))),
            ),
            solara.InputFloat(
                label="E [MPa]",
                value=layer.E_modulus,
                on_value=lambda v: on_field_update(E_modulus=max(0.1, float(v))),
            ),
            solara.InputFloat(
                label="Cc [-]",
                value=layer.Cc,
                on_value=lambda v: on_field_update(Cc=max(0.0, float(v))),
            ),
            solara.InputFloat(
                label="Cr [-]",
                value=layer.Cr,
                on_value=lambda v: on_field_update(Cr=max(0.0, float(v))),
            ),
            solara.InputFloat(
                label="Cv [m²/yr]",
                value=layer.Cv,
                on_value=lambda v: on_field_update(Cv=max(0.0, float(v))),
            ),
            solara.Select(
                label="USCS",
                value=layer.uscs_type.value,
                values=[t.value for t in SoilTypeUSCS],
                on_value=lambda v: on_field_update(uscs_type=SoilTypeUSCS(v)),
            ),
            solara.Button(
                label="📋 Copy",
                on_click=lambda: duplicate_soil_layer(layer.id),
                outlined=True,
            ),
            solara.Button(
                label="🗑️ Delete",
                on_click=lambda: delete_soil_layer(layer.id),
                color="error",
                outlined=True,
            ),
        ],
    )


@solara.component
def StratigraphyTable() -> solara.Element:
    """Render full subsoil stratigraphy editable table card."""
    state = project_state.value
    active_sc = state.get_active_scenario()
    layers = active_sc.stratigraphy

    return solara.Card(
        title="Subsoil Stratigraphy Table",
        elevation=2,
        children=[
            solara.Column(
                children=[
                    solara.Row(
                        justify="space-between",
                        children=[
                            solara.Markdown(
                                f"**Total Layers:** {len(layers)} | **Total Depth:** {sum(layer.thickness for layer in layers):.1f} m"
                            ),
                            solara.Button(
                                label="➕ Add Soil Layer",
                                on_click=lambda: add_soil_layer(),
                                color="primary",
                            ),
                        ],
                    ),
                    solara.Markdown("---"),
                    *[StratigraphyRow(layer=layer) for layer in layers],
                ]
            )
        ],
    )
