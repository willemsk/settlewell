"""Subsoil Stratigraphy layer cards component."""

import solara

from settlewell.solara_app.schemas import SoilLayerSchema, SoilTypeUSCS
from settlewell.solara_app.state import (
    add_soil_layer,
    delete_soil_layer,
    duplicate_soil_layer,
    load_flemish_profile_template,
    project_state,
    update_soil_layer,
)
from settlewell.soils import (
    FLEMISH_PROFILE_TEMPLATES,
    FLEMISH_SOIL_PRESETS,
    FlemishSoilType,
)


@solara.component
def StratigraphyLayerCard(index: int, layer: SoilLayerSchema) -> solara.Element:
    """Render a structured, clean input card for a single soil layer."""

    def on_field_update(**kwargs) -> None:
        updated = layer.model_copy(update=kwargs)
        update_soil_layer(layer.id, updated)

    def on_uscs_change(uscs_val: str) -> None:
        uscs_enum = SoilTypeUSCS(uscs_val)
        default_kh_map = {
            SoilTypeUSCS.SAND: 1e-4,
            SoilTypeUSCS.CLAY: 1e-8,
            SoilTypeUSCS.GRAVEL: 1e-2,
            SoilTypeUSCS.PEAT: 1e-5,
        }
        new_kh = default_kh_map.get(uscs_enum, layer.k_h)
        on_field_update(uscs_type=uscs_enum, k_h=new_kh)

    def on_flemish_change(flemish_val: str) -> None:
        flemish_enum = FlemishSoilType(flemish_val)
        preset = FLEMISH_SOIL_PRESETS.get(flemish_enum)
        if preset:
            on_field_update(
                flemish_type=flemish_enum,
                name=preset["name"],
                gamma_dry=preset["gamma_dry"],
                gamma_sat=preset["gamma_sat"],
                e0=preset["e0"],
                E_modulus=preset["E_modulus"],
                Cc=preset["Cc"],
                Cr=preset["Cr"],
                Cv=preset["Cv"],
                ocr=preset["ocr"],
                k_h=preset["k_h"],
                uscs_type=preset["uscs_type"],
                color=preset["color"],
            )
        else:
            on_field_update(flemish_type=flemish_enum)

    return solara.Column(
        style={
            "padding": "12px",
            "margin-bottom": "12px",
            "border": "1px solid rgba(128, 128, 128, 0.2)",
            "border-radius": "8px",
            "background-color": "rgba(128, 128, 128, 0.03)",
        },
        children=[
            # Top Bar: Name, Flemish Classification, USCS & Actions
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
                                style={"flex": "2"},
                                children=[
                                    solara.Select(
                                        label="Flemish Soil (EC7)",
                                        value=layer.flemish_type.value,
                                        values=[t.value for t in FlemishSoilType],
                                        on_value=on_flemish_change,
                                    )
                                ],
                            ),
                            solara.Column(
                                style={"flex": "1"},
                                children=[
                                    solara.Select(
                                        label="USCS",
                                        value=layer.uscs_type.value,
                                        values=[t.value for t in SoilTypeUSCS],
                                        on_value=on_uscs_change,
                                    )
                                ],
                            ),
                        ],
                    ),
                    solara.Row(
                        gap="4px",
                        children=[
                            solara.Button(
                                icon_name="mdi-content-copy",
                                color="secondary",
                                text=True,
                                outlined=True,
                                on_click=lambda: duplicate_soil_layer(layer.id),
                            ),
                            solara.Button(
                                icon_name="mdi-delete",
                                color="error",
                                text=True,
                                outlined=True,
                                on_click=lambda: delete_soil_layer(layer.id),
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
            # Row 3: OCR and Hydraulic Conductivity k_h
            solara.Row(
                gap="8px",
                children=[
                    solara.Column(
                        style={"flex": "1"},
                        children=[
                            solara.InputFloat(
                                label="OCR [-]",
                                value=layer.ocr,
                                on_value=lambda v: on_field_update(
                                    ocr=max(1.0, float(v))
                                ),
                            )
                        ],
                    ),
                    solara.Column(
                        style={"flex": "1"},
                        children=[
                            solara.InputFloat(
                                label="k_h [m/s]",
                                value=layer.k_h,
                                on_value=lambda v: on_field_update(
                                    k_h=max(1e-12, float(v))
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
                    solara.Row(
                        gap="8px",
                        children=[
                            solara.Select(
                                label="🇧🇪 Flemish Profile Template",
                                value=None,
                                values=list(FLEMISH_PROFILE_TEMPLATES.keys()),
                                on_value=lambda t: (
                                    load_flemish_profile_template(t) if t else None
                                ),
                            ),
                            solara.Button(
                                label="➕ Add Soil Layer",
                                on_click=lambda: add_soil_layer(),
                                color="primary",
                            ),
                        ],
                    ),
                ],
            ),
            *[
                StratigraphyLayerCard(index=idx + 1, layer=layer)
                for idx, layer in enumerate(layers)
            ],
        ]
    )
