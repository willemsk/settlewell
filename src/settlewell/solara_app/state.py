"""Reactive state management and serialization for settlewell Solara web application."""

from pathlib import Path

import solara

from .schemas import (
    LoadGeometrySchema,
    LoadType,
    ProjectMetadataSchema,
    ProjectState,
    ScenarioSchema,
    SoilLayerSchema,
    SoilTypeUSCS,
    SolverSettingsSchema,
    WaterTableSchema,
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

    baseline_scenario = ScenarioSchema(
        id="baseline",
        name="Baseline Model",
        is_active=True,
        water_table=WaterTableSchema(depth_z=2.5),
        stratigraphy=default_layers,
        loads=default_loads,
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


# Global Reactive State Instance
project_state: solara.Reactive[ProjectState] = solara.reactive(
    create_default_project_state()
)


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
