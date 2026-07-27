"""Reactive state management and serialization for settlewell Solara web application."""

from pathlib import Path

import numpy as np
import solara

from settlewell.models import SoilProfile
from settlewell.settlement import compute_initial_stress_profile
from settlewell.solara_app.schemas import (
    BuildingSchema,
    BuildingType,
    ConstructionPitSchema,
    DewateringConfigSchema,
    LoadGeometrySchema,
    LoadType,
    ProjectMetadataSchema,
    ProjectState,
    ScenarioSchema,
    SoilLayerSchema,
    SoilTypeUSCS,
    SolverSettingsSchema,
    WaterTableSchema,
    WellSchema,
    to_domain_soil_layer,
)


def create_default_project_state() -> ProjectState:
    """Create a default initial ProjectState instance with sample geotechnical data."""
    default_layers = [
        SoilLayerSchema(
            id="layer_1",
            name="Medium Dense Sand",
            thickness=3.0,
            gamma_dry=17.5,
            gamma_sat=19.5,
            e0=0.65,
            E_modulus=25.0,
            Cc=0.05,
            Cr=0.01,
            Cv=12.0,
            uscs_type=SoilTypeUSCS.SAND,
            color="#f59e0b",
        ),
        SoilLayerSchema(
            id="layer_2",
            name="Soft Overconsolidated Clay",
            thickness=6.5,
            gamma_dry=15.0,
            gamma_sat=17.0,
            e0=1.10,
            E_modulus=8.0,
            Cc=0.35,
            Cr=0.06,
            Cv=1.5,
            uscs_type=SoilTypeUSCS.CLAY,
            color="#854d0e",
        ),
    ]

    default_loads = [
        LoadGeometrySchema(
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
        WellSchema(
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
        construction_pit=ConstructionPitSchema(),
        dewatering=DewateringConfigSchema(wells=default_wells),
        buildings=default_buildings,
        solver_settings=SolverSettingsSchema(),
    )

    return ProjectState(
        version="2.0",
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
    """Serialize project state to .settle JSON format string."""
    return project_state.value.model_dump_json(indent=2)


def load_project_json(json_content: str) -> bool:
    """Load project state from .settle JSON string.

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
        new_state = ProjectState.model_validate_json(json_content)
        project_state.set(new_state)
        return True
    except Exception:
        import logging

        logging.exception("Failed to parse .settle project JSON content")
        return False


def load_project_from_file(file_path: Path | str) -> None:
    """Read .settle JSON file, parse into ProjectState, and update reactive store.

    Parameters
    ----------
    file_path : Path or str
        Path to .settle project JSON file.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Project file not found: {path}")

    with open(path, encoding="utf-8") as f:
        content = f.read()

    new_state = ProjectState.model_validate_json(content)
    project_state.set(new_state)


def save_project_to_file(file_path: Path | str) -> None:
    """Serialize current reactive project_state to a .settle JSON file.

    Parameters
    ----------
    file_path : Path or str
        Destination path for .settle project JSON file.
    """
    path = Path(file_path)
    if not path.suffix:
        path = path.with_suffix(".settle")

    path.parent.mkdir(parents=True, exist_ok=True)
    json_data = project_state.value.model_dump_json(indent=2)
    with open(path, "w", encoding="utf-8") as f:
        f.write(json_data)


def add_soil_layer(layer: SoilLayerSchema | None = None) -> None:
    """Add a soil layer to the active scenario in project_state."""
    current_state = project_state.value.model_copy(deep=True)
    active_sc = current_state.get_active_scenario()

    if layer is None:
        new_idx = len(active_sc.stratigraphy) + 1
        layer = SoilLayerSchema(
            id=f"layer_{new_idx}",
            name=f"Soil Layer {new_idx}",
            thickness=3.0,
            gamma_dry=17.0,
            gamma_sat=19.0,
            e0=0.65,
            E_modulus=15.0,
            Cc=0.15,
            Cr=0.03,
            Cv=5.0,
            uscs_type=SoilTypeUSCS.SAND,
            color="#f59e0b",
        )

    active_sc.stratigraphy.append(layer)
    project_state.set(current_state)


def update_soil_layer(layer_id: str, updated_layer: SoilLayerSchema) -> None:
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


def add_load(load: LoadGeometrySchema | None = None) -> None:
    """Add a load definition to the active scenario."""
    current_state = project_state.value.model_copy(deep=True)
    active_sc = current_state.get_active_scenario()

    if load is None:
        new_idx = len(active_sc.loads) + 1
        load = LoadGeometrySchema(
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


def delete_load(load_id: str) -> None:
    """Delete a load definition by ID from the active scenario."""
    current_state = project_state.value.model_copy(deep=True)
    active_sc = current_state.get_active_scenario()

    active_sc.loads = [item for item in active_sc.loads if item.id != load_id]
    project_state.set(current_state)


def add_scenario(name: str) -> str:
    """Duplicate current active scenario as a new scenario and set it as active.

    Parameters
    ----------
    name : str
        Name for the new scenario.

    Returns
    -------
    str
        New scenario ID.
    """
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
    settings = active_sc.solver_settings

    if stress_method is not None:
        settings.stress_method = stress_method
    if drainage is not None:
        from settlewell.solara_app.schemas import DrainageType

        settings.drainage = DrainageType(drainage)
    if design_approach is not None:
        from settlewell.solara_app.schemas import DesignApproach

        settings.design_approach = DesignApproach(design_approach)
    if z_max is not None:
        settings.z_max = max(0.1, float(z_max))
    if delta_z is not None:
        settings.delta_z = max(0.01, float(delta_z))
    if x_min is not None:
        settings.x_min = float(x_min)
    if x_max is not None:
        settings.x_max = float(x_max)
    if t_start_days is not None:
        settings.t_start_days = max(1.0, float(t_start_days))
    if t_end_years is not None:
        settings.t_end_years = max(0.1, float(t_end_years))
    if calculate_creep is not None:
        settings.calculate_creep = bool(calculate_creep)

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
            SoilLayerSchema(
                id=f"layer_{idx}",
                name=layer_name,
                thickness=thickness,
                gamma_dry=preset["gamma_dry"],
                gamma_sat=preset["gamma_sat"],
                e0=preset["e0"],
                E_modulus=preset["E_modulus"],
                Cc=preset["Cc"],
                Cr=preset["Cr"],
                Cv=preset["Cv"],
                ocr=preset["ocr"],
                k_h=preset["k_h"],
                flemish_type=flemish_type,
                uscs_type=preset["uscs_type"],
                color=preset["color"],
            )
        )

    active_sc.stratigraphy = new_stratigraphy
    project_state.set(current_state)


def duplicate_soil_layer(layer_id: str) -> None:
    """Duplicate an existing soil layer by ID."""
    current_state = project_state.value.model_copy(deep=True)
    active_sc = current_state.get_active_scenario()

    for idx, layer in enumerate(active_sc.stratigraphy):
        if layer.id == layer_id:
            dup_id = f"layer_{len(active_sc.stratigraphy) + 1}"
            dup_layer = layer.model_copy(deep=True)
            dup_layer.id = dup_id
            dup_layer.name = f"{layer.name} (Copy)"
            active_sc.stratigraphy.insert(idx + 1, dup_layer)
            break

    project_state.set(current_state)


def update_load(load_id: str, updated_load: LoadGeometrySchema) -> None:
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
            dup_load = load.model_copy(deep=True)
            dup_load.id = dup_id
            dup_load.name = f"{load.name} (Copy)"
            active_sc.loads.insert(idx + 1, dup_load)
            break


def _fadum_corner(b: float, l_dim: float, z: float) -> float:
    """Calculate Fadum corner stress influence value Iz for rectangle b x l_dim at depth z."""
    if z <= 1e-6 or b <= 1e-6 or l_dim <= 1e-6:
        return 0.25
    m = b / z
    n = l_dim / z
    m2 = m**2
    n2 = n**2
    v = m2 + n2 + 1.0
    v_mn = m2 * n2
    term1 = (2.0 * m * n * np.sqrt(v) / (v + v_mn)) * ((v + 1.0) / v)
    arg2 = (2.0 * m * n * np.sqrt(v)) / (v - v_mn)
    if v - v_mn < 0:
        arg2_val = np.arctan(arg2) + np.pi
    else:
        arg2_val = np.arctan(arg2)
    return float((1.0 / (4.0 * np.pi)) * (term1 + arg2_val))


def _compute_load_delta_sigma(
    load: LoadGeometrySchema, x_rel: float, z: float
) -> float:
    """Compute vertical stress increment delta_sigma_z under a surface load geometry."""
    q = max(0.0, load.stress_q)
    B = max(0.1, load.width_B)
    depth = max(0.01, z + load.z_surface_offset)

    if load.type == LoadType.STRIP:
        x_l = x_rel - B / 2.0
        x_r = x_rel + B / 2.0
        alpha = np.arctan2(x_r, depth) - np.arctan2(x_l, depth)
        return max(0.0, (q / np.pi) * (alpha + np.sin(alpha) * np.cos(alpha)))
    else:  # RECTANGULAR, EMBANKMENT, POINT
        L = max(0.1, load.length_L)
        y_half = L / 2.0
        if abs(x_rel) <= B / 2.0:
            b1 = B / 2.0 - x_rel
            b2 = B / 2.0 + x_rel
            iz = 2.0 * (
                _fadum_corner(b1, y_half, depth) + _fadum_corner(b2, y_half, depth)
            )
        else:
            b_far = abs(x_rel) + B / 2.0
            b_near = abs(x_rel) - B / 2.0
            iz = 2.0 * (
                _fadum_corner(b_far, y_half, depth)
                - _fadum_corner(b_near, y_half, depth)
            )
        return max(0.0, q * iz)


def run_fast_elastic_solve(scenario: ScenarioSchema) -> dict:
    """Execute fast 1D stress distribution and elastic settlement calculation.

    Parameters
    ----------
    scenario : ScenarioSchema
        Active scenario configuration.

    Returns
    -------
    dict
        Dictionary containing z_grid, sigma_v0_eff, delta_sigma_z, x_grid,
        stress_heatmap, and elastic_settlement_mm.
    """
    domain_layers = [
        to_domain_soil_layer(
            layer,
            k_h=layer.k_h,
            ocr=layer.ocr,
        )
        for layer in scenario.stratigraphy
    ]
    profile = SoilProfile(
        layers=domain_layers,
        gwl_mtaw=-max(0.0, scenario.water_table.depth_z),
        surface_level_mtaw=0.0,
    )
    settings = scenario.solver_settings
    z_max = max(1.0, settings.z_max)
    dz = max(0.1, settings.delta_z)

    z_grid = np.arange(0, z_max + dz, dz)
    z_eval, sigma_v0_eff, sigma_v_total = compute_initial_stress_profile(
        profile, z_grid
    )

    # 1D Delta Stress Profile under main load center (x = 0)
    delta_sigma_z = np.zeros_like(z_eval)
    for load in scenario.loads:
        x_rel = 0.0 - load.x_center
        for idx, z in enumerate(z_eval):
            delta_sigma_z[idx] += _compute_load_delta_sigma(load, x_rel, z)

    # 2D Stress Ratio Heatmap Grid
    x_grid = np.linspace(settings.x_min, settings.x_max, 60)
    stress_heatmap = np.zeros((len(z_eval), len(x_grid)))

    for i, z in enumerate(z_eval):
        for j, x in enumerate(x_grid):
            ds_sum = 0.0
            for load in scenario.loads:
                x_rel = x - load.x_center
                ds_sum += _compute_load_delta_sigma(load, x_rel, z)
            primary_q = scenario.loads[0].stress_q if scenario.loads else 100.0
            stress_heatmap[i, j] = ds_sum / max(1.0, primary_q)

    # Instant Elastic Settlement calculation s_e = sum(delta_sigma * dz / E)
    elastic_settlement_m = 0.0
    curr_depth = 0.0
    for layer in scenario.stratigraphy:
        z_mid = curr_depth + layer.thickness / 2.0
        ds_mid = 0.0
        for load in scenario.loads:
            x_rel = 0.0 - load.x_center
            ds_mid += _compute_load_delta_sigma(load, x_rel, z_mid)
        E_kpa = layer.E_modulus * 1000.0
        elastic_settlement_m += (ds_mid * layer.thickness) / max(100.0, E_kpa)
        curr_depth += layer.thickness

    return {
        "z_grid": z_eval,
        "sigma_v0_eff": sigma_v0_eff,
        "sigma_v_total": sigma_v_total,
        "delta_sigma_z": delta_sigma_z,
        "x_grid": x_grid,
        "stress_heatmap": stress_heatmap,
        "elastic_settlement_mm": elastic_settlement_m * 1000.0,
    }


def run_full_consolidation_solve(scenario: ScenarioSchema) -> dict:
    """Execute deep numerical time-consolidation integration over time intervals.

    Parameters
    ----------
    scenario : ScenarioSchema
        Active scenario configuration.

    Returns
    -------
    dict
        Dictionary containing time_years, settlement_mm, U_percent,
        layer_settlements, primary_settlement_mm, and creep_settlement_mm.
    """
    settings = scenario.solver_settings
    t_start = max(1.0, settings.t_start_days) / 365.25
    t_end = max(0.1, settings.t_end_years)

    time_years = np.logspace(np.log10(t_start), np.log10(t_end), 50)
    elastic_res = run_fast_elastic_solve(scenario)
    s_e_mm = elastic_res["elastic_settlement_mm"]

    # Calculate ultimate primary consolidation settlement per layer
    layer_ult_settlements_mm = []
    curr_depth = 0.0

    for idx, layer in enumerate(scenario.stratigraphy):
        z_mid = curr_depth + layer.thickness / 2.0
        ds_mid = 0.0
        for load in scenario.loads:
            x_rel = 0.0 - load.x_center
            ds_mid += _compute_load_delta_sigma(load, x_rel, z_mid)

        # Initial effective stress at midpoint & preconsolidation stress
        sigma_v0 = max(1.0, 10.0 + curr_depth * 8.0)
        sigma_p = sigma_v0 * max(1.0, layer.ocr)
        sigma_f = sigma_v0 + ds_mid
        H = layer.thickness
        e0 = max(0.01, layer.e0)

        if sigma_f <= sigma_p:
            # Recompression range only
            s_c_ult_m = (layer.Cr / (1.0 + e0)) * H * np.log10(sigma_f / sigma_v0)
        else:
            # Recompression up to sigma_p + virgin compression above sigma_p
            s_recomp = (layer.Cr / (1.0 + e0)) * H * np.log10(sigma_p / sigma_v0)
            s_virgin = (layer.Cc / (1.0 + e0)) * H * np.log10(sigma_f / sigma_p)
            s_c_ult_m = s_recomp + s_virgin

        layer_ult_settlements_mm.append(max(0.0, s_c_ult_m * 1000.0))
        curr_depth += layer.thickness

    total_s_c_ult = sum(layer_ult_settlements_mm)

    # Time-consolidation curve s(t)
    total_settlement_mm = []
    U_percent = []

    # Equivalent Cv for layered strata: Cv_eq = H_total^2 / (sum(h_i / sqrt(Cv_i)))^2
    total_H = sum(layer.thickness for layer in scenario.stratigraphy) or 10.0
    denom = sum(
        layer.thickness / np.sqrt(max(1e-4, layer.Cv))
        for layer in scenario.stratigraphy
    )
    eq_Cv = (total_H**2) / max(1e-4, denom**2)

    # Drainage path length
    from settlewell.solara_app.schemas import DrainageType

    if settings.drainage == DrainageType.SINGLE:
        H_dr = total_H
    else:
        H_dr = total_H / 2.0

    for t in time_years:
        Tv = (eq_Cv * t) / max(1e-4, H_dr**2)
        if Tv <= 0.2:
            U = 2.0 * np.sqrt(Tv / np.pi)
        else:
            U = 1.0 - (8.0 / (np.pi**2)) * np.exp(-((np.pi**2) / 4.0) * Tv)
        U = float(np.clip(U, 0.0, 1.0))

        s_t = s_e_mm + total_s_c_ult * U
        if settings.calculate_creep and t > 1.0:
            s_t += total_s_c_ult * 0.05 * np.log10(t)

        total_settlement_mm.append(s_t)
        U_percent.append(U * 100.0)

    return {
        "time_years": time_years,
        "settlement_mm": np.array(total_settlement_mm),
        "U_percent": np.array(U_percent),
        "layer_settlements": [
            {
                "name": layer.name,
                "elastic_mm": s_e_mm / max(1, len(scenario.stratigraphy)),
                "consolidation_mm": layer_ult_settlements_mm[i],
                "creep_mm": (
                    layer_ult_settlements_mm[i] * 0.05
                    if settings.calculate_creep
                    else 0.0
                ),
            }
            for i, layer in enumerate(scenario.stratigraphy)
        ],
        "elastic_settlement_mm": s_e_mm,
        "primary_settlement_mm": total_s_c_ult,
        "creep_settlement_mm": (
            total_s_c_ult * 0.05 if settings.calculate_creep else 0.0
        ),
    }


def add_well(well: WellSchema | None = None) -> None:
    """Add a dewatering well to the active scenario."""
    current_state = project_state.value.model_copy(deep=True)
    active_sc = current_state.get_active_scenario()

    if well is None:
        idx = len(active_sc.dewatering.wells) + 1
        well = WellSchema(
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


def update_well(well_id: str, updated_well: WellSchema) -> None:
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
            dup_well = item.model_copy(deep=True)
            dup_well.id = dup_id
            dup_well.name = f"{item.name} (Copy)"
            dup_well.x += 2.0
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
    pit = active_sc.construction_pit

    if length is not None:
        pit.length = max(0.1, float(length))
    if width is not None:
        pit.width = max(0.1, float(width))
    if depth is not None:
        pit.depth = max(0.1, float(depth))
    if bottom_mtaw is not None:
        pit.bottom_mtaw = float(bottom_mtaw)

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


def run_hydraulics_solve(scenario: ScenarioSchema) -> dict:
    """Execute steady-state Dupuit-Thiem drawdown calculations for well array.

    Parameters
    ----------
    scenario : ScenarioSchema
        Active scenario configuration.

    Returns
    -------
    dict
        Dictionary containing x_grid, y_grid, drawdown_matrix, r_grid,
        drawdown_radial, and R_influence_m.
    """
    settings = scenario.solver_settings
    x_grid = np.linspace(settings.x_min, settings.x_max, 50)
    y_grid = np.linspace(-15.0, 15.0, 50)
    X, Y = np.meshgrid(x_grid, y_grid)

    wells = scenario.dewatering.wells
    drawdown_matrix = np.zeros_like(X)

    # Sichardt radius of influence R = 3000 * s * sqrt(k_h)
    k_h = (
        np.mean([layer.k_h for layer in scenario.stratigraphy])
        if scenario.stratigraphy
        else 1e-4
    )
    target_s = max(0.5, scenario.water_table.depth_z)
    R_influence = max(50.0, 3000.0 * target_s * np.sqrt(k_h))

    # Saturated aquifer thickness & transmissivity T = k_h * D_sat
    total_H = (
        sum(layer.thickness for layer in scenario.stratigraphy)
        if scenario.stratigraphy
        else 10.0
    )
    D_sat = max(1.0, total_H - scenario.water_table.depth_z)
    T_transmissivity = max(1e-6, k_h * D_sat)

    for well in wells:
        Q_m3s = max(0.1, well.Q) / 3600.0
        r_w = max(0.01, well.r_w)
        dist = np.sqrt((X - well.x) ** 2 + (Y - well.y) ** 2)
        dist = np.maximum(r_w, dist)

        # Dupuit-Thiem steady state drawdown s(r) = (Q / 2pi T) * ln(R / r)
        s_well = (Q_m3s / (2.0 * np.pi * T_transmissivity)) * np.log(
            np.maximum(1.1, R_influence / dist)
        )
        drawdown_matrix += np.maximum(0.0, s_well)

    # Radial profile r vs drawdown
    r_grid = np.linspace(0.1, max(30.0, R_influence), 50)
    if wells:
        main_Q = max(0.1, wells[0].Q) / 3600.0
        s_radial = (main_Q / (2.0 * np.pi * T_transmissivity)) * np.log(
            np.maximum(1.1, R_influence / np.maximum(wells[0].r_w, r_grid))
        )
    else:
        s_radial = np.zeros_like(r_grid)

    return {
        "x_grid": x_grid,
        "y_grid": y_grid,
        "drawdown_matrix": drawdown_matrix,
        "r_grid": r_grid,
        "drawdown_radial": np.maximum(0.0, s_radial),
        "R_influence_m": R_influence,
    }


def run_building_damage_solve(scenario: ScenarioSchema) -> dict:
    """Execute building differential settlement, angular distortion, and damage classification.

    Parameters
    ----------
    scenario : ScenarioSchema
        Active scenario configuration.

    Returns
    -------
    dict
        Dictionary containing list of building risk result dictionaries.
    """
    elastic_res = run_fast_elastic_solve(scenario)
    s_max_mm = elastic_res["elastic_settlement_mm"]
    primary_B = scenario.loads[0].width_B if scenario.loads else 4.0
    primary_x0 = scenario.loads[0].x_center if scenario.loads else 0.0

    # Grid for surface settlement bowl s(x)
    x_eval = np.linspace(
        scenario.solver_settings.x_min, scenario.solver_settings.x_max, 120
    )
    s_eval_mm = s_max_mm / (
        1.0 + ((x_eval - primary_x0) / max(0.5, primary_B / 2.0)) ** 2
    )

    bldg_results = []
    for bldg in scenario.buildings:
        L_bldg = max(1.0, bldg.length)
        x_left = bldg.x_center - L_bldg / 2.0
        x_right = bldg.x_center + L_bldg / 2.0

        s_left = float(np.interp(x_left, x_eval, s_eval_mm))
        s_right = float(np.interp(x_right, x_eval, s_eval_mm))

        diff_s_mm = abs(s_left - s_right)
        beta_tilt = diff_s_mm / (L_bldg * 1000.0)
        deflection_ratio = (diff_s_mm / 2.0) / (L_bldg * 1000.0)

        # Burland & Wroth damage severity category
        if beta_tilt < 1 / 500:
            cat = 0
            desc = "Category 0: Negligible"
            crack = "< 0.1 mm"
            color = "#16a34a"
        elif beta_tilt < 1 / 300:
            cat = 1
            desc = "Category 1: Very Slight"
            crack = "0.1 – 1.0 mm"
            color = "#84cc16"
        elif beta_tilt < 1 / 150:
            cat = 2
            desc = "Category 2: Slight"
            crack = "1 – 5 mm"
            color = "#eab308"
        elif beta_tilt < 1 / 100:
            cat = 3
            desc = "Category 3: Moderate"
            crack = "5 – 15 mm"
            color = "#ea580c"
        else:
            cat = 4
            desc = "Category 4/5: Severe / Very Severe"
            crack = "> 15 mm"
            color = "#dc2626"

        bldg_results.append(
            {
                "id": bldg.id,
                "name": bldg.name,
                "differential_settlement_mm": diff_s_mm,
                "angular_distortion_beta": beta_tilt,
                "deflection_ratio": deflection_ratio,
                "damage_category": cat,
                "risk_category_name": desc,
                "expected_crack_width": crack,
                "risk_color": color,
                "s_left_mm": s_left,
                "s_right_mm": s_right,
            }
        )

    return {"buildings": bldg_results}
