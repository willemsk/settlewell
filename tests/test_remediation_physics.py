"""Rigorous unit tests for code review physics remediations in settlewell Solara application."""

import numpy as np

from settlewell.models import (
    Building,
    BuildingType,
    ConstructionPit,
    DewateringConfig,
    DrainageType,
    LoadGeometry,
    LoadType,
    SoilLayer,
    SoilProfile,
    AquiferType,
)
from settlewell.project import Project
from settlewell.stress import compute_stress_profile_under_loads

# Dummy components for project initialization
dummy_pit = ConstructionPit(length=10.0, width=10.0, depth=1.0)
dummy_config = DewateringConfig(
    wells=[],
    target_drawdown_mtaw=0.0,
    original_gwl_mtaw=0.0,
    pumping_duration_days=1,
    aquifer_type=AquiferType.UNCONFINED,
)


def test_ocr_settlement_recompression() -> None:
    """Verify that OCR > 1.0 applies recompression index Cr below preconsolidation stress."""
    l_nc = SoilLayer(
        name="NC Clay",
        thickness=4.0,
        gamma=18.0,
        gamma_sat=20.0,
        k_h=1e-9,
        e0=1.0,
        Cc=0.40,
        Cr=0.08,
        Eoed=3000.0,
        Cv=1e-7,
        OCR=1.0,
    )
    l_oc = SoilLayer(
        name="OC Clay",
        thickness=4.0,
        gamma=18.0,
        gamma_sat=20.0,
        k_h=1e-9,
        e0=1.0,
        Cc=0.40,
        Cr=0.08,
        Eoed=3000.0,
        Cv=1e-7,
        OCR=3.0,
    )

    prof_nc = SoilProfile(layers=[l_nc], gwl_mtaw=4.0, surface_level_mtaw=4.0)
    prof_oc = SoilProfile(layers=[l_oc], gwl_mtaw=4.0, surface_level_mtaw=4.0)

    load = LoadGeometry(
        type=LoadType.RECTANGULAR, width_B=4.0, length_L=6.0, stress_q=50.0
    )

    p_nc = Project(soil=prof_nc, pit=dummy_pit, dewatering=dummy_config, loads=[load])
    p_nc.settings = p_nc.settings.model_copy(update={"settlement_method": "cc_cr"})
    res_nc = p_nc.solve().settlement

    p_oc = Project(soil=prof_oc, pit=dummy_pit, dewatering=dummy_config, loads=[load])
    p_oc.settings = p_oc.settings.model_copy(update={"settlement_method": "cc_cr"})
    res_oc = p_oc.solve().settlement

    assert res_oc.total_settlement < res_nc.total_settlement


def test_3d_fadum_rectangular_stress() -> None:
    """Verify 3D Fadum rectangular stress distribution vs 2D strip footing stress."""
    rect_load = LoadGeometry(
        type=LoadType.RECTANGULAR, width_B=4.0, length_L=4.0, stress_q=100.0
    )
    strip_load = LoadGeometry(
        type=LoadType.STRIP, width_B=4.0, length_L=4.0, stress_q=100.0
    )

    ds_rect = compute_stress_profile_under_loads(
        [rect_load], np.array([4.0]), x_eval=0.0
    )[0]
    ds_strip = compute_stress_profile_under_loads(
        [strip_load], np.array([4.0]), x_eval=0.0
    )[0]

    assert 0.0 < ds_rect < ds_strip


def test_explicit_kh_hydraulics() -> None:
    """Verify that explicit k_h (m/s) controls Sichardt radius and hydraulics drawdown."""
    l_sand = SoilLayer(
        name="Coarse Sand",
        thickness=10.0,
        gamma=18.0,
        gamma_sat=20.0,
        k_h=1e-3,
        e0=0.5,
        Cc=0.0,
        Cr=0.0,
        Eoed=10000.0,
        Cv=1e-2,
        OCR=1.0,
    )
    l_clay = SoilLayer(
        name="Silty Clay",
        thickness=10.0,
        gamma=16.0,
        gamma_sat=18.5,
        k_h=1e-7,
        e0=1.0,
        Cc=0.3,
        Cr=0.06,
        Eoed=3000.0,
        Cv=1e-7,
        OCR=1.0,
    )

    prof_sand = SoilProfile(layers=[l_sand], gwl_mtaw=4.0, surface_level_mtaw=5.0)
    prof_clay = SoilProfile(layers=[l_clay], gwl_mtaw=4.0, surface_level_mtaw=5.0)

    config = DewateringConfig(
        wells=[],
        target_drawdown_mtaw=1.5,
        original_gwl_mtaw=4.0,
        pumping_duration_days=10,
        aquifer_type=AquiferType.UNCONFINED,
    )

    p_sand = Project(soil=prof_sand, dewatering=config, pit=dummy_pit)
    p_clay = Project(soil=prof_clay, dewatering=config, pit=dummy_pit)

    res_sand = p_sand.solve_hydraulics()
    res_clay = p_clay.solve_hydraulics()

    assert res_sand.R > res_clay.R


def test_coupled_building_damage_interpolation() -> None:
    """Verify that building damage differential settlement is interpolated from solver bowl."""
    l1 = SoilLayer(
        name="L1",
        thickness=5.0,
        gamma=18.0,
        gamma_sat=20.0,
        k_h=1e-3,
        e0=1.0,
        Cc=0.3,
        Cr=0.06,
        Eoed=10000.0,
        Cv=1e-7,
        OCR=1.0,
    )
    prof = SoilProfile(layers=[l1], gwl_mtaw=0.0, surface_level_mtaw=0.0)
    load = LoadGeometry(width_B=4.0, length_L=6.0, stress_q=120.0, x_center=0.0)

    b1 = Building(
        id="b1",
        name="Building Near",
        x=3.0,
        y=0.0,
        length=6.0,
        width=6.0,
        foundation_depth=0.5,
        building_type=BuildingType.MASONRY,
    )
    b2 = Building(
        id="b2",
        name="Building Far",
        x=20.0,
        y=0.0,
        length=6.0,
        width=6.0,
        foundation_depth=0.5,
        building_type=BuildingType.MASONRY,
    )

    from settlewell.models import Well

    p = Project(
        soil=prof,
        pit=dummy_pit,
        dewatering=dummy_config.model_copy(
            update={"wells": [Well(x=0.0, y=0.0, Q=0.01)], "target_drawdown_mtaw": -1.0}
        ),
        loads=[load],
        buildings=[b1, b2],
    )
    res = p.solve().damage

    b1_res = res.assessments["b1"]
    b2_res = res.assessments["b2"]

    assert b1_res.differential_settlement > b2_res.differential_settlement
    assert b1_res.angular_distortion > b2_res.angular_distortion


def test_single_vs_double_drainage() -> None:
    """Verify single vs double drainage boundary condition affects consolidation progress."""
    l1 = SoilLayer(
        name="L1",
        thickness=6.0,
        gamma=18.0,
        gamma_sat=20.0,
        k_h=1e-9,
        e0=1.0,
        Cc=0.3,
        Cr=0.06,
        Eoed=3000.0,
        Cv=1e-7,
        OCR=1.0,
    )
    prof = SoilProfile(layers=[l1], gwl_mtaw=4.0, surface_level_mtaw=5.0)
    load = LoadGeometry(width_B=10.0, length_L=10.0, stress_q=100.0)

    p_double = Project(soil=prof, pit=dummy_pit, dewatering=dummy_config, loads=[load])
    p_double.settings = p_double.settings.model_copy(
        update={
            "drainage": DrainageType.DOUBLE,
            "calculate_creep": True,
            "t_end_years": 1.0,
        }
    )

    p_single = Project(soil=prof, pit=dummy_pit, dewatering=dummy_config, loads=[load])
    p_single.settings = p_single.settings.model_copy(
        update={
            "drainage": DrainageType.SINGLE,
            "calculate_creep": True,
            "t_end_years": 1.0,
        }
    )

    res_double = p_double.solve().settlement
    res_single = p_single.solve().settlement

    idx_mid = 15
    # The time curve includes total settlement. Since it reaches full settlement faster,
    # the settlement value at idx_mid should be higher for DOUBLE drainage.
    assert (
        res_double.time_settlement_curve[idx_mid]
        > res_single.time_settlement_curve[idx_mid]
    )
