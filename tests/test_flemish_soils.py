"""Unit tests for NBN EN 1997-1 ANB Eurocode 7 Flemish soil library and design approaches."""

from settlewell import SoilLayer
from settlewell.solara_app.schemas import (
    DesignApproach,
    ScenarioSchema,
    SolverSettingsSchema,
)
from settlewell.soils import FLEMISH_SOIL_PRESETS, FlemishSoilType
from settlewell.solara_app.state import (
    load_flemish_profile_template,
    project_state,
)


def test_flemish_soil_presets_completeness() -> None:
    """Verify all Flemish soil types exist in preset dictionary with valid parameters."""
    for soil_type in FlemishSoilType:
        assert soil_type in FLEMISH_SOIL_PRESETS
        preset = FLEMISH_SOIL_PRESETS[soil_type]
        assert preset["gamma_sat"] >= preset["gamma_dry"] > 0
        assert preset["E_modulus"] > 0
        assert preset["k_h"] > 0
        assert preset["ocr"] >= 1.0


def test_flemish_profile_template_loading() -> None:
    """Verify loading Flemish profile templates into global reactive state."""
    load_flemish_profile_template("Antwerp Boom Clay Formation")

    active_sc = project_state.value.get_active_scenario()
    assert len(active_sc.stratigraphy) == 3
    assert active_sc.stratigraphy[2].flemish_type == FlemishSoilType.BOOMSE_KLEI
    assert active_sc.stratigraphy[2].OCR == 3.0


def test_eurocode_7_design_approach_safety_factors() -> None:
    """Verify Eurocode 7 partial safety factor scaling under ULS DA1-2 / GEO Set M2."""
    sc_sls = ScenarioSchema(
        id="sls",
        solver_settings=SolverSettingsSchema(
            design_approach=DesignApproach.SLS_CHARACTERISTIC
        ),
        stratigraphy=[
            SoilLayer(
                name="Boomse Klei",
                flemish_type=FlemishSoilType.BOOMSE_KLEI,
                thickness=5.0,
                gamma=16.0,
                gamma_sat=18.0,
                k_h=1e-9,
                e0=0.8,
                Eoed=10000.0,
                Cc=0.35,
                Cr=0.06,
                Cv=1.5e-8,
                OCR=1.0,
            )
        ],
    )

    sc_uls = ScenarioSchema(
        id="uls",
        solver_settings=SolverSettingsSchema(design_approach=DesignApproach.EC7_DA1_M2),
        stratigraphy=[
            SoilLayer(
                name="Boomse Klei",
                flemish_type=FlemishSoilType.BOOMSE_KLEI,
                thickness=5.0,
                gamma=16.0,
                gamma_sat=18.0,
                k_h=1e-9,
                e0=0.8,
                Eoed=10000.0,
                Cc=0.35,
                Cr=0.06,
                Cv=1.5e-8,
                OCR=1.0,
            )
        ],
    )

    res_sls = sc_sls.to_project().solve()
    res_uls = sc_uls.to_project().solve()

    assert res_uls.settlement is not None and res_sls.settlement is not None
    assert res_uls.settlement.total_settlement >= res_sls.settlement.total_settlement


def test_project_from_template() -> None:
    """Verify loading Flemish profile templates into a Project instance."""
    from settlewell import Project

    project = Project.from_template(
        "Antwerp Boom Clay Formation", gwl_mtaw=4.0, surface_level_mtaw=5.0
    )

    assert project.soil is not None
    assert len(project.soil.layers) == 3
    assert "Klei" in project.soil.layers[2].name
    assert project.soil.layers[2].OCR >= 1.0
