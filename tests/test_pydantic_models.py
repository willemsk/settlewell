"""Unit tests for Pydantic V2 domain model features (immutability, JSON roundtrip, dumping)."""

import pytest
from pydantic import ValidationError

from settlewell.models import (
    Building,
    ConstructionPit,
    DewateringConfig,
    DesignApproach,
    DrainageType,
    FlemishSoilType,
    LoadGeometry,
    LoadType,
    SoilLayer,
    SoilProfile,
    SoilTypeUSCS,
    SolverSettings,
    StressMethod,
    Well,
)


def test_frozen_mutation(single_sand_layer, flemish_profile):
    """Verify mutating fields on frozen Pydantic models raises ValidationError."""
    layer = single_sand_layer
    with pytest.raises(ValidationError):
        layer.thickness = 10.0

    profile = flemish_profile
    with pytest.raises(ValidationError):
        profile.gwl_mtaw = 2.0

    load = LoadGeometry(width_B=5.0, stress_q=150.0)
    with pytest.raises(ValidationError):
        load.stress_q = 200.0

    solver = SolverSettings()
    with pytest.raises(ValidationError):
        solver.z_max = 50.0

    well = Well(x=0.0, y=0.0, Q=0.001)
    with pytest.raises(ValidationError):
        well.Q = 0.005

    pit = ConstructionPit(length=10.0, width=8.0, depth=3.0)
    with pytest.raises(ValidationError):
        pit.length = 15.0

    building = Building(x=10.0, y=5.0, length=12.0, width=8.0)
    with pytest.raises(ValidationError):
        building.name = "Modified Building"

    dewatering = DewateringConfig(
        wells=[well],
        target_drawdown_mtaw=2.0,
        original_gwl_mtaw=4.0,
        pumping_duration_days=30.0,
    )
    with pytest.raises(ValidationError):
        dewatering.pumping_duration_days = 60.0


def test_json_roundtrip(flemish_profile):
    """Verify model_dump_json() and model_validate_json() serialization for domain models."""
    # LoadGeometry roundtrip
    load_orig = LoadGeometry(
        id="load_1",
        name="Custom Footing Load",
        type=LoadType.RECTANGULAR,
        x_center=5.0,
        z_surface_offset=0.5,
        width_B=4.5,
        length_L=10.0,
        stress_q=120.0,
    )
    load_json = load_orig.model_dump_json()
    assert isinstance(load_json, str)
    load_restored = LoadGeometry.model_validate_json(load_json)
    assert load_restored == load_orig

    # SoilProfile roundtrip
    profile_orig = flemish_profile
    profile_json = profile_orig.model_dump_json()
    assert isinstance(profile_json, str)
    profile_restored = SoilProfile.model_validate_json(profile_json)
    assert profile_restored == profile_orig
    assert len(profile_restored.layers) == len(profile_orig.layers)

    # SolverSettings roundtrip
    solver_orig = SolverSettings(
        stress_method=StressMethod.WESTERGAARD,
        drainage=DrainageType.SINGLE,
        design_approach=DesignApproach.EC7_DA1_M1,
        z_max=25.0,
        delta_z=0.5,
        x_min=-20.0,
        x_max=20.0,
        t_start_days=2.0,
        t_end_years=100.0,
        calculate_creep=False,
    )
    solver_json = solver_orig.model_dump_json()
    assert isinstance(solver_json, str)
    solver_restored = SolverSettings.model_validate_json(solver_json)
    assert solver_restored == solver_orig


def test_model_dump():
    """Verify model_dump() returns dictionary with expected keys and merged GUI fields."""
    layer = SoilLayer(
        name="Merged Sand",
        thickness=4.0,
        gamma=18.0,
        gamma_sat=20.0,
        k_h=1e-4,
        e0=0.55,
        Cc=0.02,
        Cr=0.005,
        Eoed=25000,
        Cv=1e-2,
        OCR=1.2,
        id="layer_gui_1",
        color="#3b82f6",
        uscs_type=SoilTypeUSCS.SAND,
        flemish_type=FlemishSoilType.PLEISTOCEEN_ZAND,
    )
    dumped = layer.model_dump()
    assert isinstance(dumped, dict)
    # Check core physical fields
    assert dumped["name"] == "Merged Sand"
    assert dumped["thickness"] == 4.0
    assert dumped["gamma"] == 18.0
    assert dumped["gamma_sat"] == 20.0
    assert dumped["k_h"] == 1e-4
    assert dumped["e0"] == 0.55
    assert dumped["Cc"] == 0.02
    assert dumped["Cr"] == 0.005
    assert dumped["Eoed"] == 25000
    assert dumped["Cv"] == 1e-2
    assert dumped["OCR"] == 1.2
    # Check merged GUI fields
    assert dumped["id"] == "layer_gui_1"
    assert dumped["color"] == "#3b82f6"
    assert dumped["uscs_type"] == SoilTypeUSCS.SAND
    assert dumped["flemish_type"] == FlemishSoilType.PLEISTOCEEN_ZAND

    # Verify model_dump for SoilProfile containing SoilLayer
    profile = SoilProfile(
        surface_level_mtaw=5.0,
        gwl_mtaw=4.0,
        layers=[layer],
    )
    profile_dump = profile.model_dump()
    assert isinstance(profile_dump, dict)
    assert profile_dump["surface_level_mtaw"] == 5.0
    assert profile_dump["gwl_mtaw"] == 4.0
    assert len(profile_dump["layers"]) == 1
    layer_in_profile = profile_dump["layers"][0]
    assert layer_in_profile["id"] == "layer_gui_1"
    assert layer_in_profile["color"] == "#3b82f6"
    assert layer_in_profile["uscs_type"] == SoilTypeUSCS.SAND
    assert layer_in_profile["flemish_type"] == FlemishSoilType.PLEISTOCEEN_ZAND

    # Verify model_dump for LoadGeometry
    load = LoadGeometry(id="load_2", name="Test Load")
    load_dump = load.model_dump()
    assert load_dump["id"] == "load_2"
    assert load_dump["name"] == "Test Load"
    assert load_dump["type"] == LoadType.RECTANGULAR

    # Verify model_dump for SolverSettings
    solver = SolverSettings()
    solver_dump = solver.model_dump()
    assert solver_dump["stress_method"] == StressMethod.BOUSSINESQ
    assert solver_dump["calculate_creep"] is True
