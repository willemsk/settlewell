"""Unit tests for Solara web application Pydantic schemas and reactive state store."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from settlewell.models import SoilLayer
from settlewell.solara_app.schemas import (
    ProjectState,
    SoilLayerSchema,
    SoilTypeUSCS,
    from_domain_soil_layer,
    to_domain_soil_layer,
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
    assert state.version == "2.0"
    assert state.metadata.title == "Main Bridge Abutment Settlement Study"
    assert len(state.scenarios) == 1
    active_sc = state.get_active_scenario()
    assert active_sc.id == "baseline"
    assert len(active_sc.stratigraphy) == 2
    assert len(active_sc.loads) == 1


def test_soil_layer_schema_validation() -> None:
    """Verify Pydantic validation rules for soil layer schema."""
    # Valid layer
    valid_layer = SoilLayerSchema(
        id="valid_1",
        name="Sand",
        thickness=5.0,
        gamma_dry=17.0,
        gamma_sat=19.0,
        e0=0.6,
        E_modulus=20.0,
        Cc=0.1,
        Cr=0.02,
        Cv=10.0,
    )
    assert valid_layer.thickness == 5.0

    # Invalid: gamma_sat < gamma_dry
    with pytest.raises(ValidationError) as exc_info:
        SoilLayerSchema(
            id="invalid_1",
            gamma_dry=18.0,
            gamma_sat=16.0,  # Invalid: sat < dry
        )
    assert (
        "Saturated unit weight (16.0 kN/m³) cannot be less than dry unit weight (18.0 kN/m³)"
        in str(exc_info.value)
    )


def test_domain_soil_layer_conversion() -> None:
    """Test bi-directional conversion between SoilLayerSchema and domain SoilLayer."""
    schema = SoilLayerSchema(
        id="l1",
        name="Test Clay",
        thickness=4.0,
        gamma_dry=16.0,
        gamma_sat=18.0,
        e0=0.8,
        E_modulus=10.0,  # MPa
        Cc=0.25,
        Cr=0.04,
        Cv=2.0,  # m²/yr
        uscs_type=SoilTypeUSCS.CLAY,
        color="#854d0e",
    )

    domain_layer = to_domain_soil_layer(schema)
    assert isinstance(domain_layer, SoilLayer)
    assert domain_layer.name == "Test Clay"
    assert domain_layer.thickness == 4.0
    assert domain_layer.gamma == 16.0
    assert domain_layer.gamma_sat == 18.0
    assert domain_layer.Eoed == 10000.0  # 10 MPa -> 10000 kPa
    assert pytest.approx(domain_layer.Cv * (365.25 * 86400.0)) == 2.0

    converted_schema = from_domain_soil_layer(
        domain_layer, layer_id="l1", uscs_type=SoilTypeUSCS.CLAY, color="#854d0e"
    )
    assert converted_schema.name == schema.name
    assert converted_schema.thickness == schema.thickness
    assert converted_schema.gamma_dry == schema.gamma_dry
    assert converted_schema.gamma_sat == schema.gamma_sat
    assert pytest.approx(converted_schema.E_modulus) == schema.E_modulus
    assert pytest.approx(converted_schema.Cv) == schema.Cv


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
    assert loaded_state.version == "2.0"
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
