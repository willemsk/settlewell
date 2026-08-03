"""Unit tests for Solara web application drawer components."""

from settlewell.solara_app.components.drawer import (
    DrawerContainer,
    LoadsTable,
    MetadataCard,
    SolverMeshCard,
    StratigraphyTable,
)
from settlewell.solara_app.schemas import StressMethod
from settlewell.solara_app.state import (
    create_default_project_state,
    project_state,
    update_metadata,
    update_solver_settings,
    update_water_table,
)


def test_drawer_components_instantiation() -> None:
    """Verify that all drawer components instantiate without errors."""
    project_state.set(create_default_project_state())

    card1 = MetadataCard()
    assert card1 is not None

    card2 = StratigraphyTable()
    assert card2 is not None

    card3 = LoadsTable()
    assert card3 is not None

    card4 = SolverMeshCard()
    assert card4 is not None

    container = DrawerContainer()
    assert container is not None


def test_page_component_rendering() -> None:
    """Verify that full Page component renders via reacton without component errors."""
    import reacton
    from settlewell.solara_app import Page

    project_state.set(create_default_project_state())
    box, _ = reacton.render(Page())
    assert box is not None


def test_metadata_card_state_updates() -> None:
    """Test reactive state updates for MetadataCard inputs."""
    project_state.set(create_default_project_state())

    update_metadata(
        title="New Bridge Study", engineer="A. Smith, PE", date="2026-08-01"
    )
    update_water_table(4.5)

    state = project_state.value
    assert state.metadata.title == "New Bridge Study"
    assert state.metadata.engineer == "A. Smith, PE"
    assert state.metadata.date == "2026-08-01"
    assert state.get_active_scenario().water_table.depth_z == 4.5


def test_solver_mesh_card_state_updates() -> None:
    """Test reactive state updates for SolverMeshCard settings."""
    project_state.set(create_default_project_state())

    update_solver_settings(
        stress_method=StressMethod.WESTERGAARD,
        z_max=30.0,
        delta_z=0.5,
        x_min=-20.0,
        x_max=20.0,
        t_start_days=2.0,
        t_end_years=100.0,
        calculate_creep=False,
    )

    settings = project_state.value.get_active_scenario().solver_settings
    assert settings.stress_method == StressMethod.WESTERGAARD
    assert settings.z_max == 30.0
    assert settings.delta_z == 0.5
    assert settings.x_min == -20.0
    assert settings.x_max == 20.0
    assert settings.t_start_days == 2.0
    assert settings.t_end_years == 100.0
    assert settings.calculate_creep is False

    # Reset state and solver settings to default
    update_solver_settings(stress_method=StressMethod.BOUSSINESQ)
    project_state.set(create_default_project_state())
