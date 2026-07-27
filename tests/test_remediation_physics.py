"""Rigorous unit tests for code review physics remediations in settlewell Solara application."""

from settlewell.solara_app.schemas import (
    BuildingSchema,
    DewateringConfigSchema,
    DrainageType,
    LoadGeometrySchema,
    LoadType,
    ScenarioSchema,
    SoilLayerSchema,
    SoilTypeUSCS,
    SolverSettingsSchema,
)
from settlewell.solara_app.state import (
    _compute_load_delta_sigma,
    run_building_damage_solve,
    run_full_consolidation_solve,
    run_hydraulics_solve,
)


def test_ocr_settlement_recompression() -> None:
    """Verify that OCR > 1.0 applies recompression index Cr below preconsolidation stress."""
    # Scenario 1: NC Clay (OCR = 1.0)
    sc_nc = ScenarioSchema(
        id="nc",
        stratigraphy=[
            SoilLayerSchema(
                id="l1",
                name="NC Clay",
                thickness=4.0,
                Cc=0.40,
                Cr=0.08,
                ocr=1.0,
                uscs_type=SoilTypeUSCS.CLAY,
            )
        ],
        loads=[
            LoadGeometrySchema(
                id="load1",
                type=LoadType.RECTANGULAR,
                width_B=4.0,
                length_L=6.0,
                stress_q=50.0,
            )
        ],
    )

    # Scenario 2: OC Clay (OCR = 3.0)
    sc_oc = ScenarioSchema(
        id="oc",
        stratigraphy=[
            SoilLayerSchema(
                id="l1",
                name="OC Clay",
                thickness=4.0,
                Cc=0.40,
                Cr=0.08,
                ocr=3.0,
                uscs_type=SoilTypeUSCS.CLAY,
            )
        ],
        loads=[
            LoadGeometrySchema(
                id="load1",
                type=LoadType.RECTANGULAR,
                width_B=4.0,
                length_L=6.0,
                stress_q=50.0,
            )
        ],
    )

    res_nc = run_full_consolidation_solve(sc_nc)
    res_oc = run_full_consolidation_solve(sc_oc)

    # Overconsolidated clay must yield significantly less primary settlement than Normally Consolidated clay
    assert res_oc["primary_settlement_mm"] < res_nc["primary_settlement_mm"]


def test_3d_fadum_rectangular_stress() -> None:
    """Verify 3D Fadum rectangular stress distribution vs 2D strip footing stress."""
    rect_load = LoadGeometrySchema(
        id="rect",
        type=LoadType.RECTANGULAR,
        width_B=4.0,
        length_L=4.0,
        stress_q=100.0,
    )
    strip_load = LoadGeometrySchema(
        id="strip",
        type=LoadType.STRIP,
        width_B=4.0,
        length_L=4.0,
        stress_q=100.0,
    )

    # At depth z = 4.0m under center
    ds_rect = _compute_load_delta_sigma(rect_load, x_rel=0.0, z=4.0)
    ds_strip = _compute_load_delta_sigma(strip_load, x_rel=0.0, z=4.0)

    # 3D finite square load must have less stress dispersion at depth than 2D infinite strip load
    assert 0.0 < ds_rect < ds_strip


def test_explicit_kh_hydraulics() -> None:
    """Verify that explicit k_h (m/s) controls Sichardt radius and hydraulics drawdown."""
    sc_sand = ScenarioSchema(
        id="sand",
        stratigraphy=[
            SoilLayerSchema(
                id="l1",
                name="Coarse Sand",
                thickness=10.0,
                k_h=1e-3,  # High permeability
                uscs_type=SoilTypeUSCS.SAND,
            )
        ],
        dewatering=DewateringConfigSchema(wells=[]),
    )

    sc_clay = ScenarioSchema(
        id="clay",
        stratigraphy=[
            SoilLayerSchema(
                id="l1",
                name="Silty Clay",
                thickness=10.0,
                k_h=1e-7,  # Low permeability
                uscs_type=SoilTypeUSCS.CLAY,
            )
        ],
        dewatering=DewateringConfigSchema(wells=[]),
    )

    res_sand = run_hydraulics_solve(sc_sand)
    res_clay = run_hydraulics_solve(sc_clay)

    # High permeability sand must have larger influence radius R than low permeability clay
    assert res_sand["R_influence_m"] > res_clay["R_influence_m"]


def test_coupled_building_damage_interpolation() -> None:
    """Verify that building damage differential settlement is interpolated from solver bowl."""
    sc = ScenarioSchema(
        id="bldg_test",
        stratigraphy=[SoilLayerSchema(id="l1", thickness=5.0, E_modulus=10.0)],
        loads=[
            LoadGeometrySchema(
                id="l1", width_B=4.0, length_L=6.0, stress_q=120.0, x_center=0.0
            )
        ],
        buildings=[
            BuildingSchema(id="b1", name="Building Near", x_center=3.0, length=6.0),
            BuildingSchema(id="b2", name="Building Far", x_center=20.0, length=6.0),
        ],
    )

    res = run_building_damage_solve(sc)
    b1_res = res["buildings"][0]
    b2_res = res["buildings"][1]

    # Building near footing experiences higher differential settlement & tilt than far building
    assert b1_res["differential_settlement_mm"] > b2_res["differential_settlement_mm"]
    assert b1_res["angular_distortion_beta"] > b2_res["angular_distortion_beta"]


def test_single_vs_double_drainage() -> None:
    """Verify single vs double drainage boundary condition affects consolidation progress."""
    sc_double = ScenarioSchema(
        id="double",
        solver_settings=SolverSettingsSchema(drainage=DrainageType.DOUBLE),
        stratigraphy=[SoilLayerSchema(id="l1", thickness=6.0, Cc=0.3, Cv=2.0)],
    )
    sc_single = ScenarioSchema(
        id="single",
        solver_settings=SolverSettingsSchema(drainage=DrainageType.SINGLE),
        stratigraphy=[SoilLayerSchema(id="l1", thickness=6.0, Cc=0.3, Cv=2.0)],
    )

    res_double = run_full_consolidation_solve(sc_double)
    res_single = run_full_consolidation_solve(sc_single)

    # Double drainage reaches 50% degree of consolidation faster than single drainage
    idx_mid = 15
    assert res_double["U_percent"][idx_mid] > res_single["U_percent"][idx_mid]
