"""Pydantic v2 schemas and re-exports for settlewell Solara web application."""

from typing import Any
from pydantic import BaseModel, Field, model_validator

from settlewell.models import (
    AquiferType,
    Building,
    BuildingType,
    ConstructionPit,
    DesignApproach,
    DewateringConfig,
    DrainageType,
    LoadGeometry,
    LoadType,
    SoilLayer,
    SoilProfile,
    SoilTypeUSCS,
    SolverSettings,
    StressMethod,
    Well,
)
from settlewell.project import Project
from settlewell.soils import FlemishSoilType

# Type aliases for backwards compatibility in GUI code
SoilLayerSchema = SoilLayer
LoadGeometrySchema = LoadGeometry
SolverSettingsSchema = SolverSettings
WellSchema = Well
ConstructionPitSchema = ConstructionPit
DewateringConfigSchema = DewateringConfig


class BuildingSchema(Building):
    @model_validator(mode="before")
    @classmethod
    def _remap_gui_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "x_center" in data and "x" not in data:
                data["x"] = data.pop("x_center")
            if "structural_type" in data and "building_type" not in data:
                data["building_type"] = data.pop("structural_type")
        return data

    @property
    def x_center(self) -> float:
        return self.x

    @property
    def structural_type(self) -> BuildingType:
        return self.building_type


class WaterTableSchema(BaseModel):
    """Pydantic schema for groundwater table depth."""

    depth_z: float = Field(
        ge=0, default=2.0, description="Groundwater depth below ground surface [m]"
    )


class ProjectMetadataSchema(BaseModel):
    """Pydantic schema for project metadata."""

    title: str = Field(default="Untitled Settlement Analysis")
    engineer: str = Field(default="Geotechnical Engineer")
    date: str = Field(default="2026-07-24")
    units: str = Field(default="metric")
    comments: str | None = Field(default=None)


def _default_stratigraphy() -> list[SoilLayer]:
    return [
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


class ScenarioSchema(BaseModel):
    """Pydantic schema for a calculation scenario wrapper around a core Project."""

    id: str = Field(default="baseline", description="Unique scenario ID")
    name: str = Field(default="Baseline Scenario")
    is_active: bool = Field(default=True)
    water_table: WaterTableSchema = Field(default_factory=WaterTableSchema)
    stratigraphy: list[SoilLayer] = Field(default_factory=_default_stratigraphy)
    loads: list[LoadGeometry] = Field(default_factory=list)
    construction_pit: ConstructionPit = Field(default_factory=ConstructionPit)
    dewatering: DewateringConfig = Field(default_factory=DewateringConfig)
    buildings: list[BuildingSchema] = Field(default_factory=list)
    solver_settings: SolverSettings = Field(default_factory=SolverSettings)

    def to_project(self) -> Project:
        """Construct or return the core Project instance representing this scenario."""
        gwl_mtaw = -self.water_table.depth_z
        surface_mtaw = 0.0
        dew = self.dewatering
        if dew.original_gwl_mtaw > surface_mtaw:
            dew = dew.model_copy(
                update={
                    "original_gwl_mtaw": gwl_mtaw,
                    "target_drawdown_mtaw": min(dew.target_drawdown_mtaw, gwl_mtaw),
                }
            )

        prof = SoilProfile(
            layers=self.stratigraphy,
            gwl_mtaw=gwl_mtaw,
            surface_level_mtaw=surface_mtaw,
        )
        return Project(
            soil=prof,
            pit=self.construction_pit,
            dewatering=dew,
            buildings=self.buildings,
            loads=self.loads,
            settings=self.solver_settings,
        )


class ProjectState(BaseModel):
    """Root Pydantic schema for full GUI state representation."""

    version: str = Field(default="3.0")
    metadata: ProjectMetadataSchema = Field(default_factory=ProjectMetadataSchema)
    scenarios: list[ScenarioSchema] = Field(default_factory=list)
    active_scenario_id: str = Field(default="baseline")
    edit_mode: bool = Field(
        default=True, description="Toggle canvas edit vs read-only mode"
    )
    dark_mode: bool = Field(default=False, description="UI dark mode toggle")

    def get_active_scenario(self) -> ScenarioSchema:
        """Return the currently active scenario, or default baseline if not found."""
        for s in self.scenarios:
            if s.id == self.active_scenario_id:
                return s
        if self.scenarios:
            return self.scenarios[0]
        default_sc = ScenarioSchema(id="baseline", name="Baseline Scenario")
        self.scenarios.append(default_sc)
        return default_sc


__all__ = [
    "AquiferType",
    "Building",
    "BuildingSchema",
    "BuildingType",
    "ConstructionPit",
    "ConstructionPitSchema",
    "DesignApproach",
    "DewateringConfig",
    "DewateringConfigSchema",
    "DrainageType",
    "FlemishSoilType",
    "LoadGeometry",
    "LoadGeometrySchema",
    "LoadType",
    "ProjectMetadataSchema",
    "ProjectState",
    "ScenarioSchema",
    "SoilLayer",
    "SoilLayerSchema",
    "SoilProfile",
    "SoilTypeUSCS",
    "SolverSettings",
    "SolverSettingsSchema",
    "StressMethod",
    "WaterTableSchema",
    "Well",
    "WellSchema",
]
