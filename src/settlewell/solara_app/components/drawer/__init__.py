"""Persistent left drawer container assembling all 4 input accordion cards."""

import solara

from settlewell.solara_app.components.drawer.loads_table import LoadsTable
from settlewell.solara_app.components.drawer.metadata_card import MetadataCard
from settlewell.solara_app.components.drawer.solver_mesh_card import SolverMeshCard
from settlewell.solara_app.components.drawer.stratigraphy_table import StratigraphyTable


@solara.component
def DrawerContainer() -> solara.Element:
    """Render persistent left drawer containing collapsible expansion panel cards."""
    return solara.Column(
        gap="16px",
        style={"padding": "8px", "max-width": "650px", "overflow-y": "auto"},
        children=[
            solara.v.ExpansionPanels(
                multiple=True,
                v_model=[0, 1, 2, 3],  # All cards expanded by default
                children=[
                    solara.v.ExpansionPanel(
                        children=[
                            solara.v.ExpansionPanelHeader(
                                children=["Project Metadata & Groundwater"]
                            ),
                            solara.v.ExpansionPanelContent(children=[MetadataCard()]),
                        ]
                    ),
                    solara.v.ExpansionPanel(
                        children=[
                            solara.v.ExpansionPanelHeader(
                                children=["Subsoil Stratigraphy Table"]
                            ),
                            solara.v.ExpansionPanelContent(
                                children=[StratigraphyTable()]
                            ),
                        ]
                    ),
                    solara.v.ExpansionPanel(
                        children=[
                            solara.v.ExpansionPanelHeader(
                                children=["Surface & Foundation Loads Table"]
                            ),
                            solara.v.ExpansionPanelContent(children=[LoadsTable()]),
                        ]
                    ),
                    solara.v.ExpansionPanel(
                        children=[
                            solara.v.ExpansionPanelHeader(
                                children=["Calculation Mesh & Solver Settings"]
                            ),
                            solara.v.ExpansionPanelContent(children=[SolverMeshCard()]),
                        ]
                    ),
                ],
            )
        ],
    )


__all__ = [
    "DrawerContainer",
    "MetadataCard",
    "StratigraphyTable",
    "LoadsTable",
    "SolverMeshCard",
]
