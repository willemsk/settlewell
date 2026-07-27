"""End-to-End automated test suite for settlewell Solara Web Application."""

import reacton
from settlewell.solara_app import Page
from settlewell.solara_app.export import (
    generate_csv_data,
    generate_dxf_drawing,
    generate_excel_workbook,
    generate_pdf_report,
)
from settlewell.solara_app.schemas import (
    BuildingSchema,
    BuildingType,
    LoadGeometrySchema,
    LoadType,
    SoilLayerSchema,
    SoilTypeUSCS,
    WellSchema,
)
from settlewell.solara_app.state import (
    add_building,
    add_load,
    add_soil_layer,
    add_well,
    create_new_scenario,
    display_elevation_mtaw,
    duplicate_scenario,
    load_project_json,
    project_state,
    run_building_damage_solve,
    run_fast_elastic_solve,
    run_full_consolidation_solve,
    run_hydraulics_solve,
    save_project_json,
    set_elevation_display_mode,
    switch_active_scenario,
)


def test_e2e_full_workflow() -> None:
    """Execute complete end-to-end user workflow integration test."""
    # 1. Verify default project state initialization
    state = project_state.value
    assert state.version == "2.0"
    active_sc = state.get_active_scenario()
    assert active_sc.id == "baseline"
    assert len(active_sc.stratigraphy) >= 1
    assert len(active_sc.loads) >= 1

    # 2. Scenario creation and duplication
    create_new_scenario("Proposed Dewatering Scenario")
    assert len(project_state.value.scenarios) == 2
    sc2 = project_state.value.get_active_scenario()
    assert sc2.name == "Proposed Dewatering Scenario"

    duplicate_scenario(sc2.id)
    assert len(project_state.value.scenarios) == 3
    switch_active_scenario("baseline")
    assert project_state.value.active_scenario_id == "baseline"

    # 3. Add soil layer, surface load, dewatering well, and neighboring building
    new_layer = SoilLayerSchema(
        id="layer_deep_clay",
        name="Deep Stiff Clay",
        thickness=5.0,
        gamma_dry=16.0,
        gamma_sat=18.0,
        e0=0.9,
        E_modulus=12.0,
        Cc=0.25,
        Cr=0.04,
        Cv=2.0,
        uscs_type=SoilTypeUSCS.CLAY,
    )
    add_soil_layer(new_layer)

    new_load = LoadGeometrySchema(
        id="load_storage_tank",
        name="Storage Tank Load",
        type=LoadType.RECTANGULAR,
        x_center=5.0,
        z_surface_offset=0.0,
        width_B=6.0,
        length_L=10.0,
        stress_q=85.0,
    )
    add_load(new_load)

    new_well = WellSchema(
        id="well_east_2",
        name="East Well 2",
        x=10.0,
        y=0.0,
        Q=30.0,
        r_w=0.075,
    )
    add_well(new_well)

    new_bldg = BuildingSchema(
        id="bldg_church",
        name="Historic Church",
        x_center=25.0,
        foundation_depth=2.0,
        length=15.0,
        structural_type=BuildingType.MASONRY,
    )
    add_building(new_bldg)

    # 4. Elevation Datum Unit Toggle
    set_elevation_display_mode(True)
    assert display_elevation_mtaw.value is True
    set_elevation_display_mode(False)
    assert display_elevation_mtaw.value is False

    # 5. Solver Engine Runs
    curr_sc = project_state.value.get_active_scenario()
    elastic_res = run_fast_elastic_solve(curr_sc)
    assert elastic_res["elastic_settlement_mm"] > 0.0

    consolidation_res = run_full_consolidation_solve(curr_sc)
    assert len(consolidation_res["time_years"]) == 50

    hydraulics_res = run_hydraulics_solve(curr_sc)
    assert hydraulics_res["R_influence_m"] > 0.0

    damage_res = run_building_damage_solve(curr_sc)
    assert len(damage_res["buildings"]) >= 1

    # 6. Deliverable File Exports
    pdf_b = generate_pdf_report(curr_sc)
    assert len(pdf_b) > 500

    dxf_b = generate_dxf_drawing(curr_sc)
    assert len(dxf_b) > 200

    excel_b = generate_excel_workbook(curr_sc)
    assert len(excel_b) > 500

    csv_b = generate_csv_data(curr_sc)
    assert len(csv_b) > 50

    # 7. Project JSON Serialization / Deserialization (.settle file format)
    json_str = save_project_json()
    assert len(json_str) > 200
    assert "baseline" in json_str

    success = load_project_json(json_str)
    assert success is True

    # 8. Full Application Shell UI Rendering
    page_box = reacton.render(Page())
    assert page_box is not None
