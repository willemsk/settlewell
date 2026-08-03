"""Unit tests for Solara web application Pydantic schemas and reactive state store."""

from pathlib import Path

from settlewell.models import SoilTypeUSCS
from settlewell.solara_app.schemas import (
    ProjectState,
)
from settlewell.solara_app.state import (
    add_load,
    add_scenario,
    add_soil_layer,
    create_default_project_state,
    delete_load,
    delete_soil_layer,
    load_project_from_file,
    project_state,
    save_project_to_file,
    update_soil_layer,
)


def test_default_project_state_creation() -> None:
    """Verify default ProjectState initialization structure."""
    state = create_default_project_state()
    assert state.version == "3.0"
    assert state.metadata.title == "Main Bridge Abutment Settlement Study"
    assert len(state.scenarios) == 1
    active_sc = state.get_active_scenario()
    assert active_sc.id == "baseline"
    assert len(active_sc.stratigraphy) == 2
    assert len(active_sc.loads) == 1


def test_project_file_serialization(tmp_path: Path) -> None:
    """Test saving and loading a .settle project JSON file."""
    test_file = tmp_path / "test_project.settle"
    initial_state = create_default_project_state()
    project_state.set(initial_state)

    save_project_to_file(test_file)
    assert test_file.exists()

    # Reset state and re-load
    project_state.set(ProjectState(version="0.0"))
    load_project_from_file(test_file)

    loaded_state = project_state.value
    assert loaded_state.version == "3.0"
    assert loaded_state.metadata.title == initial_state.metadata.title
    assert len(loaded_state.scenarios) == len(initial_state.scenarios)


def test_state_modification_helpers() -> None:
    """Test helper functions for layer, load, and scenario modification."""
    project_state.set(create_default_project_state())

    # Add layer
    add_soil_layer()
    sc = project_state.value.get_active_scenario()
    assert len(sc.stratigraphy) == 3
    assert sc.stratigraphy[-1].name == "Soil Layer 3"

    # Update layer
    updated_layer = sc.stratigraphy[-1].model_copy(
        update={"name": "Updated Gravel", "uscs_type": SoilTypeUSCS.GRAVEL}
    )
    update_soil_layer(updated_layer.id, updated_layer)
    sc = project_state.value.get_active_scenario()
    assert sc.stratigraphy[-1].name == "Updated Gravel"
    assert sc.stratigraphy[-1].uscs_type == SoilTypeUSCS.GRAVEL

    # Delete layer
    delete_soil_layer(updated_layer.id)
    sc = project_state.value.get_active_scenario()
    assert len(sc.stratigraphy) == 2

    # Add & Delete load
    add_load()
    sc = project_state.value.get_active_scenario()
    assert len(sc.loads) == 2
    load_id = sc.loads[-1].id
    delete_load(load_id)
    sc = project_state.value.get_active_scenario()
    assert len(sc.loads) == 1

    # Add scenario
    new_sc_id = add_scenario("Alternative Load Scenario")
    assert project_state.value.active_scenario_id == new_sc_id
    assert len(project_state.value.scenarios) == 2
    assert project_state.value.get_active_scenario().name == "Alternative Load Scenario"
