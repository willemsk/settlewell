"""Calculation Mesh & Solver Parameters component."""

import solara

from settlewell.solara_app.schemas import DesignApproach, DrainageType, StressMethod
from settlewell.solara_app.state import project_state, update_solver_settings


@solara.component
def SolverMeshCard() -> solara.Element:
    """Render calculation mesh parameters, stress distribution method, and consolidation time range controls."""
    state = project_state.value
    active_sc = state.get_active_scenario()
    settings = active_sc.solver_settings

    return solara.Column(
        gap="16px",
        style={"padding": "8px 4px"},
        children=[
            solara.Select(
                label="Stress Distribution Method",
                value=settings.stress_method.value,
                values=[m.value for m in StressMethod],
                on_value=lambda v: update_solver_settings(stress_method=v),
            ),
            solara.Select(
                label="Drainage Boundary Condition",
                value=settings.drainage.value,
                values=[d.value for d in DrainageType],
                on_value=lambda v: update_solver_settings(drainage=v),
            ),
            solara.Select(
                label="Eurocode 7 Design Limit State",
                value=settings.design_approach.value,
                values=[da.value for da in DesignApproach],
                on_value=lambda v: update_solver_settings(design_approach=v),
            ),
            solara.Markdown("##### Vertical Depth Mesh Parameters"),
            solara.Row(
                gap="12px",
                children=[
                    solara.Column(
                        style={"flex": "1"},
                        children=[
                            solara.InputFloat(
                                label="Max Depth z_max [m]",
                                value=settings.z_max,
                                on_value=lambda v: update_solver_settings(z_max=v),
                            )
                        ],
                    ),
                    solara.Column(
                        style={"flex": "1"},
                        children=[
                            solara.InputFloat(
                                label="Step Size delta_z [m]",
                                value=settings.delta_z,
                                on_value=lambda v: update_solver_settings(delta_z=v),
                            )
                        ],
                    ),
                ],
            ),
            solara.Markdown("##### Horizontal Grid Boundaries"),
            solara.Row(
                gap="12px",
                children=[
                    solara.Column(
                        style={"flex": "1"},
                        children=[
                            solara.InputFloat(
                                label="Left Bound x_min [m]",
                                value=settings.x_min,
                                on_value=lambda v: update_solver_settings(x_min=v),
                            )
                        ],
                    ),
                    solara.Column(
                        style={"flex": "1"},
                        children=[
                            solara.InputFloat(
                                label="Right Bound x_max [m]",
                                value=settings.x_max,
                                on_value=lambda v: update_solver_settings(x_max=v),
                            )
                        ],
                    ),
                ],
            ),
            solara.Markdown("##### Time-Consolidation Range"),
            solara.Row(
                gap="12px",
                children=[
                    solara.Column(
                        style={"flex": "1"},
                        children=[
                            solara.InputFloat(
                                label="Start Time t_start [days]",
                                value=settings.t_start_days,
                                on_value=lambda v: update_solver_settings(
                                    t_start_days=v
                                ),
                            )
                        ],
                    ),
                    solara.Column(
                        style={"flex": "1"},
                        children=[
                            solara.InputFloat(
                                label="End Time t_end [years]",
                                value=settings.t_end_years,
                                on_value=lambda v: update_solver_settings(
                                    t_end_years=v
                                ),
                            )
                        ],
                    ),
                ],
            ),
            solara.Checkbox(
                label="Calculate Secondary Creep (C_alpha)",
                value=settings.calculate_creep,
                on_value=lambda v: update_solver_settings(calculate_creep=v),
            ),
        ],
    )
