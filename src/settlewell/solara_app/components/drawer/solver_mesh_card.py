"""Calculation Mesh & Solver Parameters accordion card component."""

import solara

from settlewell.solara_app.schemas import StressMethod
from settlewell.solara_app.state import project_state, update_solver_settings


@solara.component
def SolverMeshCard() -> solara.Element:
    """Render calculation mesh parameters, stress distribution method, and consolidation time range controls."""
    state = project_state.value
    active_sc = state.get_active_scenario()
    settings = active_sc.solver_settings

    return solara.Card(
        title="Calculation Mesh & Solver Settings",
        elevation=2,
        children=[
            solara.Column(
                gap="12px",
                children=[
                    solara.Select(
                        label="Stress Distribution Method",
                        value=settings.stress_method.value,
                        values=[m.value for m in StressMethod],
                        on_value=lambda v: update_solver_settings(stress_method=v),
                    ),
                    solara.Markdown("#### Vertical Depth Mesh Parameters"),
                    solara.Row(
                        children=[
                            solara.InputFloat(
                                label="Max Depth z_max [m]",
                                value=settings.z_max,
                                on_value=lambda v: update_solver_settings(z_max=v),
                            ),
                            solara.InputFloat(
                                label="Step Size delta_z [m]",
                                value=settings.delta_z,
                                on_value=lambda v: update_solver_settings(delta_z=v),
                            ),
                        ]
                    ),
                    solara.Markdown("#### Horizontal Grid Boundaries"),
                    solara.Row(
                        children=[
                            solara.InputFloat(
                                label="Left Bound x_min [m]",
                                value=settings.x_min,
                                on_value=lambda v: update_solver_settings(x_min=v),
                            ),
                            solara.InputFloat(
                                label="Right Bound x_max [m]",
                                value=settings.x_max,
                                on_value=lambda v: update_solver_settings(x_max=v),
                            ),
                        ]
                    ),
                    solara.Markdown("#### Time-Consolidation Range"),
                    solara.Row(
                        children=[
                            solara.InputFloat(
                                label="Start Time t_start [days]",
                                value=settings.t_start_days,
                                on_value=lambda v: update_solver_settings(
                                    t_start_days=v
                                ),
                            ),
                            solara.InputFloat(
                                label="End Time t_end [years]",
                                value=settings.t_end_years,
                                on_value=lambda v: update_solver_settings(
                                    t_end_years=v
                                ),
                            ),
                        ]
                    ),
                    solara.Checkbox(
                        label="Calculate Secondary Creep (C_alpha)",
                        value=settings.calculate_creep,
                        on_value=lambda v: update_solver_settings(calculate_creep=v),
                    ),
                ],
            )
        ],
    )
