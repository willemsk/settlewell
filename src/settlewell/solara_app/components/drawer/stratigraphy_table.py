"""Subsoil Stratigraphy layer cards component."""

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
def StratigraphyLayerCard(index: int, layer: SoilLayerSchema) -> solara.Element:
    """Render a structured, clean input card for a single soil layer."""

    def on_field_update(**kwargs) -> None:
        updated = layer.model_copy(update=kwargs)
        update_soil_layer(layer.id, updated)

    return solara.Column(
        style={
            "padding": "12px",
            "margin-bottom": "12px",
            "border": "1px solid rgba(128, 128, 128, 0.2)",
            "border-radius": "8px",
            "background-color": "rgba(128, 128, 128, 0.03)",
        },
        children=[
            # Top Bar: Name, USCS Classification & Actions
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
                                style={"flex": "2"},
                                children=[
                                    solara.InputText(
                                        label="Layer Name",
                                        value=layer.name,
                                        on_value=lambda v: on_field_update(name=v),
                                    )
                                ],
                            ),
                            solara.Column(
                                style={"flex": "0 0 120px"},
                                children=[
                                    solara.Select(
                                        label="USCS",
                                        value=layer.uscs_type.value,
                                        values=[t.value for t in SoilTypeUSCS],
                                        on_value=lambda v: on_field_update(
                                            uscs_type=SoilTypeUSCS(v)
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
                                on_click=lambda: duplicate_soil_layer(layer.id),
                                outlined=True,
                                icon_name="mdi-content-copy",
                            ),
                            solara.Button(
                                label="🗑️",
                                on_click=lambda: delete_soil_layer(layer.id),
                                color="error",
                                outlined=True,
                                icon_name="mdi-delete",
                            ),
                        ],
                    ),
                ],
            ),
            # Row 1: Thickness h, Unit weights, Initial void ratio
            solara.Row(
                gap="8px",
                children=[
                    solara.Column(
                        style={"flex": "1"},
                        children=[
                            solara.InputFloat(
                                label="Thickness h [m]",
                                value=layer.thickness,
                                on_value=lambda v: on_field_update(
                                    thickness=max(0.1, float(v))
                                ),
                            )
                        ],
                    ),
                    solara.Column(
                        style={"flex": "1"},
                        children=[
                            solara.InputFloat(
                                label="γ dry [kN/m³]",
                                value=layer.gamma_dry,
                                on_value=lambda v: on_field_update(
                                    gamma_dry=max(0.1, float(v))
                                ),
                            )
                        ],
                    ),
                    solara.Column(
                        style={"flex": "1"},
                        children=[
                            solara.InputFloat(
                                label="γ sat [kN/m³]",
                                value=layer.gamma_sat,
                                on_value=lambda v: on_field_update(
                                    gamma_sat=max(layer.gamma_dry, float(v))
                                ),
                            )
                        ],
                    ),
                    solara.Column(
                        style={"flex": "1"},
                        children=[
                            solara.InputFloat(
                                label="e0 [-]",
                                value=layer.e0,
                                on_value=lambda v: on_field_update(
                                    e0=max(0.0, float(v))
                                ),
                            )
                        ],
                    ),
                ],
            ),
            # Row 2: Elastic modulus E, Cc, Cr, Cv
            solara.Row(
                gap="8px",
                children=[
                    solara.Column(
                        style={"flex": "1"},
                        children=[
                            solara.InputFloat(
                                label="E [MPa]",
                                value=layer.E_modulus,
                                on_value=lambda v: on_field_update(
                                    E_modulus=max(0.1, float(v))
                                ),
                            )
                        ],
                    ),
                    solara.Column(
                        style={"flex": "1"},
                        children=[
                            solara.InputFloat(
                                label="Cc [-]",
                                value=layer.Cc,
                                on_value=lambda v: on_field_update(
                                    Cc=max(0.0, float(v))
                                ),
                            )
                        ],
                    ),
                    solara.Column(
                        style={"flex": "1"},
                        children=[
                            solara.InputFloat(
                                label="Cr [-]",
                                value=layer.Cr,
                                on_value=lambda v: on_field_update(
                                    Cr=max(0.0, float(v))
                                ),
                            )
                        ],
                    ),
                    solara.Column(
                        style={"flex": "1"},
                        children=[
                            solara.InputFloat(
                                label="Cv [m²/yr]",
                                value=layer.Cv,
                                on_value=lambda v: on_field_update(
                                    Cv=max(0.0, float(v))
                                ),
                            )
                        ],
                    ),
                ],
            ),
        ],
    )


@solara.component
def StratigraphyTable() -> solara.Element:
    """Render full subsoil stratigraphy cards component."""
    state = project_state.value
    active_sc = state.get_active_scenario()
    layers = active_sc.stratigraphy

    return solara.Column(
        children=[
            solara.Row(
                justify="space-between",
                style={"align-items": "center", "margin-bottom": "12px"},
                children=[
                    solara.Markdown(
                        f"**Layers:** {len(layers)} | **Total Depth:** {sum(layer.thickness for layer in layers):.1f} m"
                    ),
                    solara.Button(
                        label="➕ Add Soil Layer",
                        on_click=lambda: add_soil_layer(),
                        color="primary",
                    ),
                ],
            ),
            *[
                StratigraphyLayerCard(index=idx + 1, layer=layer)
                for idx, layer in enumerate(layers)
            ],
        ]
    )
