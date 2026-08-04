"""Reactive state management and serialization for settlewell Solara web application."""

from pathlib import Path

import solara

from settlewell.models import (
    BuildingType,
    ConstructionPit,
    DewateringConfig,
    LoadGeometry,
    LoadType,
    SoilLayer,
    SoilTypeUSCS,
    SolverSettings,
    Well,
)
from settlewell.solara_app.schemas import (
    BuildingSchema,
    ProjectMetadataSchema,
    ProjectState,
    ScenarioSchema,
    WaterTableSchema,
)


def create_default_project_state() -> ProjectState:
    """Create a default initial ProjectState instance with sample geotechnical data."""
    default_layers = [
        SoilLayer(
            id="layer_1",
            name="Medium Dense Sand",
            thickness=3.0,
            gamma=17.5,
            gamma_sat=19.5,
            k_h=1e-4,
            e0=0.65,
            Eoed=25000.0,
            Cc=0.05,
            Cr=0.01,
            Cv=3.8e-7,
            uscs_type=SoilTypeUSCS.SAND,
            color="#f59e0b",
        ),
        SoilLayer(
            id="layer_2",
            name="Soft Overconsolidated Clay",
            thickness=6.5,
            gamma=15.0,
            gamma_sat=17.0,
            k_h=1e-8,
            e0=1.10,
            Eoed=8000.0,
            Cc=0.35,
            Cr=0.06,
            Cv=4.7e-8,
            uscs_type=SoilTypeUSCS.CLAY,
            color="#854d0e",
        ),
    ]

    default_loads = [
        LoadGeometry(
            id="load_1",
            name="Strip Footing Load",
            type=LoadType.RECTANGULAR,
            x_center=0.0,
            z_surface_offset=0.0,
            width_B=4.0,
            length_L=8.0,
            stress_q=120.0,
        )
    ]

    default_wells = [
        Well(
            id="well_1",
            name="Dewatering Well 1",
            x=-8.0,
            y=0.0,
            Q=25.0,
            r_w=0.075,
            screen_top_mtaw=-1.0,
            screen_bottom_mtaw=-6.0,
        )
    ]

    default_buildings = [
        BuildingSchema(
            id="bldg_1",
            name="Adjacent Residence",
            x_center=18.0,
            foundation_depth=1.5,
            length=12.0,
            structural_type=BuildingType.MASONRY,
        )
    ]

    baseline_scenario = ScenarioSchema(
        id="baseline",
        name="Baseline Model",
        is_active=True,
        water_table=WaterTableSchema(depth_z=2.5),
        stratigraphy=default_layers,
        loads=default_loads,
        construction_pit=ConstructionPit(),
        dewatering=DewateringConfig(wells=default_wells),
        buildings=default_buildings,
        solver_settings=SolverSettings(),
    )

    return ProjectState(
        version="3.0",
        metadata=ProjectMetadataSchema(
            title="Main Bridge Abutment Settlement Study",
            engineer="J. Doe, PE",
            date="2026-07-24",
            units="metric",
        ),
        scenarios=[baseline_scenario],
        active_scenario_id="baseline",
        edit_mode=True,
        dark_mode=False,
    )


# Global reactive state store
project_state = solara.reactive(create_default_project_state())
display_elevation_mtaw = solara.reactive(False)


def set_elevation_display_mode(mtaw_enabled: bool) -> None:
    """Set global elevation display mode (Depth m vs Elevation mTAW)."""
    display_elevation_mtaw.set(mtaw_enabled)


def create_new_scenario(name: str = "New Scenario") -> None:
    """Create and activate a new scenario."""
    current_state = project_state.value.model_copy(deep=True)
    idx = len(current_state.scenarios) + 1
    new_sc = ScenarioSchema(
        id=f"scenario_{idx}",
        name=name,
        is_active=True,
    )
    for sc in current_state.scenarios:
        sc.is_active = False

    current_state.scenarios.append(new_sc)
    current_state.active_scenario_id = new_sc.id
    project_state.set(current_state)


def duplicate_scenario(scenario_id: str) -> None:
    """Duplicate an existing scenario by ID and activate the copy."""
    current_state = project_state.value.model_copy(deep=True)
    target_sc = None
    for sc in current_state.scenarios:
        if sc.id == scenario_id:
            target_sc = sc
            break

    if target_sc is not None:
        idx = len(current_state.scenarios) + 1
        dup_sc = target_sc.model_copy(deep=True)
        dup_sc.id = f"scenario_{idx}"
        dup_sc.name = f"{target_sc.name} (Copy)"

        for sc in current_state.scenarios:
            sc.is_active = False

        dup_sc.is_active = True
        current_state.scenarios.append(dup_sc)
        current_state.active_scenario_id = dup_sc.id
        project_state.set(current_state)


def switch_active_scenario(scenario_id: str) -> None:
    """Switch active scenario by ID."""
    current_state = project_state.value.model_copy(deep=True)
    found = False
    for sc in current_state.scenarios:
        if sc.id == scenario_id:
            sc.is_active = True
            found = True
        else:
            sc.is_active = False

    if found:
        current_state.active_scenario_id = scenario_id
        project_state.set(current_state)


def save_project_json() -> str:
    """Serialize active scenario to .settle JSON format string."""
    active_sc = project_state.value.get_active_scenario()
    project = active_sc.to_project()
    from settlewell.project import ProjectDataModel
    project_data = ProjectDataModel(
        soil=project.soil,
        pit=project.pit,
        dewatering=project.dewatering,
        buildings=project.buildings,
        loads=project.loads,
        settings=project.settings,
    )
    return project_data.model_dump_json(indent=2)


def load_project_json(json_content: str) -> bool:
    """Load core Project from .settle JSON string and wrap in ProjectState.

    Parameters
    ----------
    json_content : str
        JSON formatted string.

    Returns
    -------
    bool
        True if loaded successfully, False otherwise.
    """
    try:
        from settlewell.project import ProjectDataModel
        project_data = ProjectDataModel.model_validate_json(json_content)
        
        # Reconstruct ScenarioSchema from ProjectDataModel
        scenario = ScenarioSchema(
            id="baseline",
            name="Loaded Project",
            is_active=True,
            water_table=WaterTableSchema(depth_z=-project_data.dewatering.original_gwl_mtaw if project_data.dewatering else 0.0),
            stratigraphy=project_data.soil.layers if project_data.soil else [],
            loads=project_data.loads,
            construction_pit=project_data.pit if project_data.pit else ConstructionPit(),
            dewatering=project_data.dewatering if project_data.dewatering else DewateringConfig(),
            buildings=[BuildingSchema(**b.model_dump()) for b in project_data.buildings],
            solver_settings=project_data.settings,
        )
        
        new_state = ProjectState(
            version="3.0",
            scenarios=[scenario],
            active_scenario_id="baseline"
        )
        project_state.set(new_state)
        return True
    except Exception:
        import logging

        logging.exception("Failed to parse .settle project JSON content")
        return False


def load_project_from_file(file_path: Path | str) -> None:
    """Read .settle JSON file, parse into ProjectState, and update reactive store."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Project file not found: {path}")

    with open(path, encoding="utf-8") as f:
        content = f.read()

    if not load_project_json(content):
        raise ValueError("Failed to parse project file.")


def save_project_to_file(file_path: Path | str) -> None:
    """Serialize current active scenario to a .settle JSON file."""
    path = Path(file_path)
    if not path.suffix:
        path = path.with_suffix(".settle")

    path.parent.mkdir(parents=True, exist_ok=True)
    json_data = save_project_json()
    with open(path, "w", encoding="utf-8") as f:
        f.write(json_data)


def add_soil_layer(layer: SoilLayer | None = None) -> None:
    """Add a soil layer to the active scenario in project_state."""
    current_state = project_state.value.model_copy(deep=True)
    active_sc = current_state.get_active_scenario()

    if layer is None:
        new_idx = len(active_sc.stratigraphy) + 1
        layer = SoilLayer(
            id=f"layer_{new_idx}",
            name=f"Soil Layer {new_idx}",
            thickness=3.0,
            gamma=17.0,
            gamma_sat=19.0,
            k_h=1e-4,
            e0=0.65,
            Eoed=15000.0,
            Cc=0.15,
            Cr=0.03,
            Cv=1.5e-7,
            uscs_type=SoilTypeUSCS.SAND,
            color="#f59e0b",
        )

    active_sc.stratigraphy.append(layer)
    project_state.set(current_state)


def update_soil_layer(layer_id: str, updated_layer: SoilLayer) -> None:
    """Update an existing soil layer by ID in the active scenario."""
    current_state = project_state.value.model_copy(deep=True)
    active_sc = current_state.get_active_scenario()

    for idx, layer in enumerate(active_sc.stratigraphy):
        if layer.id == layer_id:
            active_sc.stratigraphy[idx] = updated_layer
            break

    project_state.set(current_state)


def delete_soil_layer(layer_id: str) -> None:
    """Delete a soil layer by ID from the active scenario."""
    current_state = project_state.value.model_copy(deep=True)
    active_sc = current_state.get_active_scenario()

    active_sc.stratigraphy = [
        layer for layer in active_sc.stratigraphy if layer.id != layer_id
    ]
    project_state.set(current_state)


def duplicate_soil_layer(layer_id: str) -> None:
    """Duplicate an existing soil layer by ID."""
    current_state = project_state.value.model_copy(deep=True)
    active_sc = current_state.get_active_scenario()

    for idx, layer in enumerate(active_sc.stratigraphy):
        if layer.id == layer_id:
            dup_id = f"layer_{len(active_sc.stratigraphy) + 1}"
            dup_layer = layer.model_copy(
                deep=True, update={"id": dup_id, "name": f"{layer.name} (Copy)"}
            )
            active_sc.stratigraphy.insert(idx + 1, dup_layer)
            break

    project_state.set(current_state)


def add_load(load: LoadGeometry | None = None) -> None:
    """Add a load definition to the active scenario."""
    current_state = project_state.value.model_copy(deep=True)
    active_sc = current_state.get_active_scenario()

    if load is None:
        new_idx = len(active_sc.loads) + 1
        load = LoadGeometry(
            id=f"load_{new_idx}",
            name=f"Load {new_idx}",
            type=LoadType.RECTANGULAR,
            x_center=0.0,
            z_surface_offset=0.0,
            width_B=4.0,
            length_L=8.0,
            stress_q=100.0,
        )

    active_sc.loads.append(load)
    project_state.set(current_state)


def update_load(load_id: str, updated_load: LoadGeometry) -> None:
    """Update an existing surface load definition by ID."""
    current_state = project_state.value.model_copy(deep=True)
    active_sc = current_state.get_active_scenario()

    for idx, load in enumerate(active_sc.loads):
        if load.id == load_id:
            active_sc.loads[idx] = updated_load
            break

    project_state.set(current_state)


def duplicate_load(load_id: str) -> None:
    """Duplicate an existing load definition by ID."""
    current_state = project_state.value.model_copy(deep=True)
    active_sc = current_state.get_active_scenario()

    for idx, load in enumerate(active_sc.loads):
        if load.id == load_id:
            dup_id = f"load_{len(active_sc.loads) + 1}"
            dup_load = load.model_copy(
                deep=True, update={"id": dup_id, "name": f"{load.name} (Copy)"}
            )
            active_sc.loads.insert(idx + 1, dup_load)
            break

    project_state.set(current_state)


def delete_load(load_id: str) -> None:
    """Delete a load definition by ID from the active scenario."""
    current_state = project_state.value.model_copy(deep=True)
    active_sc = current_state.get_active_scenario()

    active_sc.loads = [item for item in active_sc.loads if item.id != load_id]
    project_state.set(current_state)


def add_scenario(name: str) -> str:
    """Duplicate current active scenario as a new scenario and set it as active."""
    current_state = project_state.value.model_copy(deep=True)
    active_sc = current_state.get_active_scenario()

    new_id = f"scenario_{len(current_state.scenarios) + 1}"
    new_scenario = active_sc.model_copy(deep=True)
    new_scenario.id = new_id
    new_scenario.name = name
    new_scenario.is_active = True

    current_state.scenarios.append(new_scenario)
    current_state.active_scenario_id = new_id
    project_state.set(current_state)
    return new_id


def update_metadata(
    title: str | None = None,
    engineer: str | None = None,
    date: str | None = None,
    comments: str | None = None,
) -> None:
    """Update project metadata attributes."""
    current_state = project_state.value.model_copy(deep=True)
    if title is not None:
        current_state.metadata.title = title
    if engineer is not None:
        current_state.metadata.engineer = engineer
    if date is not None:
        current_state.metadata.date = date
    if comments is not None:
        current_state.metadata.comments = comments
    project_state.set(current_state)


def update_water_table(depth_z: float) -> None:
    """Update groundwater depth z_gw in active scenario."""
    current_state = project_state.value.model_copy(deep=True)
    active_sc = current_state.get_active_scenario()
    active_sc.water_table.depth_z = max(0.0, float(depth_z))
    project_state.set(current_state)


def update_solver_settings(
    stress_method: str | None = None,
    drainage: str | None = None,
    design_approach: str | None = None,
    z_max: float | None = None,
    delta_z: float | None = None,
    x_min: float | None = None,
    x_max: float | None = None,
    t_start_days: float | None = None,
    t_end_years: float | None = None,
    calculate_creep: bool | None = None,
) -> None:
    """Update calculation mesh and solver settings in active scenario."""
    current_state = project_state.value.model_copy(deep=True)
    active_sc = current_state.get_active_scenario()
    settings_dict = active_sc.solver_settings.model_dump()

    if stress_method is not None:
        settings_dict["stress_method"] = stress_method
    if drainage is not None:
        settings_dict["drainage"] = drainage
    if design_approach is not None:
        settings_dict["design_approach"] = design_approach
    if z_max is not None:
        settings_dict["z_max"] = max(0.1, float(z_max))
    if delta_z is not None:
        settings_dict["delta_z"] = max(0.01, float(delta_z))
    if x_min is not None:
        settings_dict["x_min"] = float(x_min)
    if x_max is not None:
        settings_dict["x_max"] = float(x_max)
    if t_start_days is not None:
        settings_dict["t_start_days"] = max(1.0, float(t_start_days))
    if t_end_years is not None:
        settings_dict["t_end_years"] = max(0.1, float(t_end_years))
    if calculate_creep is not None:
        settings_dict["calculate_creep"] = bool(calculate_creep)

    active_sc.solver_settings = SolverSettings(**settings_dict)
    project_state.set(current_state)


def load_flemish_profile_template(template_name: str) -> None:
    """Load a predefined Flemish stratigraphy profile template into the active scenario."""
    from settlewell.soils import FLEMISH_PROFILE_TEMPLATES, FLEMISH_SOIL_PRESETS

    if template_name not in FLEMISH_PROFILE_TEMPLATES:
        return

    current_state = project_state.value.model_copy(deep=True)
    active_sc = current_state.get_active_scenario()

    template_layers = FLEMISH_PROFILE_TEMPLATES[template_name]
    new_stratigraphy = []
    for idx, (layer_name, flemish_type, thickness) in enumerate(
        template_layers, start=1
    ):
        preset = FLEMISH_SOIL_PRESETS[flemish_type]
        new_stratigraphy.append(
            SoilLayer(
                id=f"layer_{idx}",
                name=layer_name,
                thickness=thickness,
                gamma=preset["gamma_dry"],
                gamma_sat=preset["gamma_sat"],
                e0=preset["e0"],
                Eoed=preset["E_modulus"] * 1000.0,
                Cc=preset["Cc"],
                Cr=preset["Cr"],
                Cv=preset["Cv"],
                OCR=preset["ocr"],
                k_h=preset["k_h"],
                flemish_type=flemish_type,
                uscs_type=preset["uscs_type"],
                color=preset["color"],
            )
        )

    active_sc.stratigraphy = new_stratigraphy
    project_state.set(current_state)


def add_well(well: Well | None = None) -> None:
    """Add a dewatering well to the active scenario."""
    current_state = project_state.value.model_copy(deep=True)
    active_sc = current_state.get_active_scenario()

    if well is None:
        idx = len(active_sc.dewatering.wells) + 1
        well = Well(
            id=f"well_{idx}",
            name=f"Well {idx}",
            x=-8.0 + (idx - 1) * 4.0,
            y=0.0,
            Q=20.0,
            r_w=0.075,
            screen_top_mtaw=-1.0,
            screen_bottom_mtaw=-6.0,
        )

    active_sc.dewatering.wells.append(well)
    project_state.set(current_state)


def update_well(well_id: str, updated_well: Well) -> None:
    """Update a dewatering well by ID in active scenario."""
    current_state = project_state.value.model_copy(deep=True)
    active_sc = current_state.get_active_scenario()

    for idx, item in enumerate(active_sc.dewatering.wells):
        if item.id == well_id:
            active_sc.dewatering.wells[idx] = updated_well
            break

    project_state.set(current_state)


def delete_well(well_id: str) -> None:
    """Delete a dewatering well by ID from active scenario."""
    current_state = project_state.value.model_copy(deep=True)
    active_sc = current_state.get_active_scenario()

    active_sc.dewatering.wells = [
        item for item in active_sc.dewatering.wells if item.id != well_id
    ]
    project_state.set(current_state)


def duplicate_well(well_id: str) -> None:
    """Duplicate a dewatering well by ID."""
    current_state = project_state.value.model_copy(deep=True)
    active_sc = current_state.get_active_scenario()

    for idx, item in enumerate(active_sc.dewatering.wells):
        if item.id == well_id:
            dup_id = f"well_{len(active_sc.dewatering.wells) + 1}"
            dup_well = item.model_copy(
                deep=True,
                update={"id": dup_id, "name": f"{item.name} (Copy)", "x": item.x + 2.0},
            )
            active_sc.dewatering.wells.insert(idx + 1, dup_well)
            break

    project_state.set(current_state)


def update_construction_pit(
    length: float | None = None,
    width: float | None = None,
    depth: float | None = None,
    bottom_mtaw: float | None = None,
) -> None:
    """Update construction pit geometry parameters."""
    current_state = project_state.value.model_copy(deep=True)
    active_sc = current_state.get_active_scenario()
    pit = active_sc.construction_pit.model_dump()

    if length is not None:
        pit["length"] = max(0.1, float(length))
    if width is not None:
        pit["width"] = max(0.1, float(width))
    if depth is not None:
        pit["depth"] = max(0.1, float(depth))
    if bottom_mtaw is not None:
        pit["bottom_mtaw"] = float(bottom_mtaw)

    active_sc.construction_pit = ConstructionPit(**pit)
    project_state.set(current_state)


def add_building(building: BuildingSchema | None = None) -> None:
    """Add a neighboring building to the active scenario."""
    current_state = project_state.value.model_copy(deep=True)
    active_sc = current_state.get_active_scenario()

    if building is None:
        idx = len(active_sc.buildings) + 1
        building = BuildingSchema(
            id=f"bldg_{idx}",
            name=f"Building {idx}",
            x_center=15.0 + (idx - 1) * 10.0,
            foundation_depth=1.5,
            length=10.0,
            structural_type=BuildingType.MASONRY,
        )

    active_sc.buildings.append(building)
    project_state.set(current_state)


def update_building(building_id: str, updated_bldg: BuildingSchema) -> None:
    """Update a neighboring building by ID in active scenario."""
    current_state = project_state.value.model_copy(deep=True)
    active_sc = current_state.get_active_scenario()

    for idx, item in enumerate(active_sc.buildings):
        if item.id == building_id:
            active_sc.buildings[idx] = updated_bldg
            break

    project_state.set(current_state)


def delete_building(building_id: str) -> None:
    """Delete a neighboring building by ID from active scenario."""
    current_state = project_state.value.model_copy(deep=True)
    active_sc = current_state.get_active_scenario()

    active_sc.buildings = [
        item for item in active_sc.buildings if item.id != building_id
    ]
    project_state.set(current_state)
