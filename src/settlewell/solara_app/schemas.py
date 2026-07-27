"""Pydantic v2 schemas and domain dataclass conversion routines for settlewell Solara web application."""

from enum import StrEnum
from pydantic import BaseModel, Field, ValidationInfo, field_validator

from settlewell.models import SoilLayer


class SoilTypeUSCS(StrEnum):
    """USCS Soil Classification types for visualization and hatching."""

    SAND = "SAND"
    CLAY = "CLAY"
    GRAVEL = "GRAVEL"
    PEAT = "PEAT"


class LoadType(StrEnum):
    """Surface load geometry types."""

    STRIP = "STRIP"
    RECTANGULAR = "RECTANGULAR"
    EMBANKMENT = "EMBANKMENT"
    POINT = "POINT"


class StressMethod(StrEnum):
    """Stress distribution calculation methods."""

    BOUSSINESQ = "BOUSSINESQ"
    WESTERGAARD = "WESTERGAARD"
    TWO_TO_ONE = "2:1"


class DrainageType(StrEnum):
    """Boundary drainage condition for primary consolidation."""

    DOUBLE = "DOUBLE"
    SINGLE = "SINGLE"


class AquiferType(StrEnum):
    """Aquifer hydrogeological classification."""

    UNCONFINED = "UNCONFINED"
    CONFINED = "CONFINED"


class BuildingType(StrEnum):
    """Neighboring building structural type."""

    MASONRY = "MASONRY"
    CONCRETE_FRAME = "CONCRETE_FRAME"


class SoilLayerSchema(BaseModel):
    """Pydantic schema for soil layer parameters in the GUI."""

    id: str = Field(description="Unique layer identifier")
    name: str = Field(default="New Layer", description="Descriptive layer name")
    thickness: float = Field(
        gt=0, default=3.0, description="Layer thickness in meters [m]"
    )
    gamma_dry: float = Field(gt=0, default=17.0, description="Dry unit weight [kN/m³]")
    gamma_sat: float = Field(
        gt=0, default=19.0, description="Saturated unit weight [kN/m³]"
    )
    e0: float = Field(ge=0, default=0.65, description="Initial void ratio [-]")
    E_modulus: float = Field(gt=0, default=15.0, description="Elastic modulus [MPa]")
    Cc: float = Field(ge=0, default=0.15, description="Compression index [-]")
    Cr: float = Field(ge=0, default=0.03, description="Recompression index [-]")
    Cv: float = Field(
        ge=0, default=5.0, description="Coefficient of consolidation [m²/yr]"
    )
    ocr: float = Field(ge=1.0, default=1.0, description="Overconsolidation ratio [-]")
    k_h: float = Field(gt=0, default=1e-4, description="Hydraulic conductivity [m/s]")
    uscs_type: SoilTypeUSCS = Field(
        default=SoilTypeUSCS.SAND, description="USCS soil classification"
    )
    color: str = Field(
        default="#f59e0b", description="Hex color code for visualization"
    )

    @field_validator("gamma_sat")
    def validate_gamma_sat(cls, v: float, info: ValidationInfo) -> float:
        """Ensure saturated unit weight is not less than dry unit weight."""
        gamma_dry = info.data.get("gamma_dry", 0.0)
        if v < gamma_dry:
            raise ValueError(
                f"Saturated unit weight ({v} kN/m³) cannot be less than dry unit weight ({gamma_dry} kN/m³)"
            )
        return v


class LoadGeometrySchema(BaseModel):
    """Pydantic schema for surface load geometry."""

    id: str = Field(description="Unique load identifier")
    name: str = Field(default="Footing Load", description="Load name")
    type: LoadType = Field(
        default=LoadType.RECTANGULAR, description="Load geometry type"
    )
    x_center: float = Field(default=0.0, description="X coordinate of load center [m]")
    z_surface_offset: float = Field(
        default=0.0, description="Depth offset from surface [m]"
    )
    width_B: float = Field(gt=0, default=4.0, description="Footing width B [m]")
    length_L: float = Field(gt=0, default=8.0, description="Footing length L [m]")
    stress_q: float = Field(
        gt=0, default=100.0, description="Applied uniform stress q [kPa]"
    )


class SolverSettingsSchema(BaseModel):
    """Pydantic schema for calculation mesh and solver parameters."""

    stress_method: StressMethod = Field(
        default=StressMethod.BOUSSINESQ, description="Stress distribution method"
    )
    drainage: DrainageType = Field(
        default=DrainageType.DOUBLE, description="Drainage boundary condition"
    )
    z_max: float = Field(
        gt=0, default=20.0, description="Maximum calculation depth [m]"
    )
    delta_z: float = Field(
        gt=0, default=0.25, description="Vertical mesh step size [m]"
    )
    x_min: float = Field(default=-15.0, description="Left grid boundary [m]")
    x_max: float = Field(default=15.0, description="Right grid boundary [m]")
    t_start_days: float = Field(
        ge=1.0, default=1.0, description="Start time for consolidation [days]"
    )
    t_end_years: float = Field(
        gt=0, default=50.0, description="End time for consolidation [years]"
    )
    calculate_creep: bool = Field(
        default=True, description="Enable secondary creep C_alpha calculation"
    )


class ProjectMetadataSchema(BaseModel):
    """Pydantic schema for project metadata."""

    title: str = Field(default="Untitled Settlement Analysis")
    engineer: str = Field(default="Geotechnical Engineer")
    date: str = Field(default="2026-07-24")
    units: str = Field(default="metric")
    comments: str | None = Field(default=None)


class WaterTableSchema(BaseModel):
    """Pydantic schema for groundwater table depth."""

    depth_z: float = Field(
        ge=0, default=2.0, description="Groundwater depth below ground surface [m]"
    )


class WellSchema(BaseModel):
    """Pydantic schema for a dewatering well."""

    id: str = Field(description="Unique well identifier")
    name: str = Field(default="Well 1", description="Well name")
    x: float = Field(default=-8.0, description="X coordinate of well [m]")
    y: float = Field(default=0.0, description="Y coordinate of well [m]")
    Q: float = Field(gt=0, default=25.0, description="Pumping rate Q [m³/h]")
    r_w: float = Field(gt=0, default=0.075, description="Casing radius r_w [m]")
    screen_top_mtaw: float = Field(
        default=-1.0, description="Screen top elevation [mTAW]"
    )
    screen_bottom_mtaw: float = Field(
        default=-6.0, description="Screen bottom elevation [mTAW]"
    )


class ConstructionPitSchema(BaseModel):
    """Pydantic schema for construction excavation pit geometry."""

    length: float = Field(gt=0, default=20.0, description="Pit length L [m]")
    width: float = Field(gt=0, default=15.0, description="Pit width W [m]")
    depth: float = Field(gt=0, default=4.0, description="Excavation depth d [m]")
    bottom_mtaw: float = Field(default=-1.5, description="Pit bottom level [mTAW]")


class DewateringConfigSchema(BaseModel):
    """Pydantic schema for dewatering hydraulics configuration."""

    aquifer_type: AquiferType = Field(
        default=AquiferType.UNCONFINED, description="Aquifer hydrogeological type"
    )
    target_drawdown_mtaw: float = Field(
        default=-2.0, description="Target lowered GWL [mTAW]"
    )
    pumping_duration_days: float = Field(
        gt=0, default=30.0, description="Pumping duration [days]"
    )
    wells: list[WellSchema] = Field(
        default_factory=list, description="Active dewatering well array"
    )


class BuildingSchema(BaseModel):
    """Pydantic schema for neighboring building assessment."""

    id: str = Field(description="Unique building identifier")
    name: str = Field(default="Adjacent Building", description="Building name")
    x_center: float = Field(
        default=18.0, description="X coordinate of building center [m]"
    )
    foundation_depth: float = Field(
        ge=0, default=1.5, description="Foundation depth [m]"
    )
    length: float = Field(gt=0, default=12.0, description="Building length L_bldg [m]")
    structural_type: BuildingType = Field(
        default=BuildingType.MASONRY, description="Structural classification type"
    )


class ScenarioSchema(BaseModel):
    """Pydantic schema for a calculation scenario."""

    id: str = Field(description="Unique scenario ID")
    name: str = Field(default="Baseline Scenario")
    is_active: bool = Field(default=True)
    water_table: WaterTableSchema = Field(default_factory=WaterTableSchema)
    stratigraphy: list[SoilLayerSchema] = Field(default_factory=list)
    loads: list[LoadGeometrySchema] = Field(default_factory=list)
    construction_pit: ConstructionPitSchema = Field(
        default_factory=ConstructionPitSchema
    )
    dewatering: DewateringConfigSchema = Field(default_factory=DewateringConfigSchema)
    buildings: list[BuildingSchema] = Field(default_factory=list)
    solver_settings: SolverSettingsSchema = Field(default_factory=SolverSettingsSchema)


class ProjectState(BaseModel):
    """Root Pydantic schema for full GUI state representation."""

    version: str = Field(default="2.0")
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


SECONDS_PER_YEAR = 365.25 * 86400.0


def to_domain_soil_layer(
    schema: SoilLayerSchema,
    k_h: float | None = None,
    ocr: float | None = None,
) -> SoilLayer:
    """Convert a SoilLayerSchema GUI model into a settlewell.models.SoilLayer domain object.

    Parameters
    ----------
    schema : SoilLayerSchema
        GUI soil layer schema instance.
    k_h : float | None, default None
        Horizontal hydraulic conductivity [m/s]. If None, schema.k_h is used.
    ocr : float | None, default None
        Overconsolidation ratio [-]. If None, schema.ocr is used.

    Returns
    -------
    SoilLayer
        Domain dataclass instance.
    """
    actual_k_h = schema.k_h if k_h is None else k_h
    actual_ocr = schema.ocr if ocr is None else ocr

    return SoilLayer(
        name=schema.name,
        thickness=schema.thickness,
        gamma=schema.gamma_dry,
        gamma_sat=schema.gamma_sat,
        k_h=actual_k_h,
        e0=schema.e0,
        Cc=schema.Cc,
        Cr=schema.Cr,
        Eoed=schema.E_modulus * 1000.0,  # Convert MPa to kPa
        Cv=schema.Cv / SECONDS_PER_YEAR,  # Convert m²/yr to m²/s
        OCR=actual_ocr,
    )


def from_domain_soil_layer(
    layer: SoilLayer,
    layer_id: str = "layer_1",
    uscs_type: SoilTypeUSCS = SoilTypeUSCS.SAND,
    color: str = "#f59e0b",
) -> SoilLayerSchema:
    """Convert a settlewell.models.SoilLayer domain object into a SoilLayerSchema GUI model.

    Parameters
    ----------
    layer : SoilLayer
        Domain dataclass instance.
    layer_id : str, default "layer_1"
        Unique identifier for the GUI schema.
    uscs_type : SoilTypeUSCS, default SoilTypeUSCS.SAND
        USCS soil type classification.
    color : str, default "#f59e0b"
        Hex color code.

    Returns
    -------
    SoilLayerSchema
        GUI soil layer schema instance.
    """
    return SoilLayerSchema(
        id=layer_id,
        name=layer.name,
        thickness=layer.thickness,
        gamma_dry=layer.gamma,
        gamma_sat=layer.gamma_sat,
        e0=layer.e0,
        E_modulus=layer.Eoed / 1000.0,  # Convert kPa to MPa
        Cc=layer.Cc,
        Cr=layer.Cr,
        Cv=layer.Cv * SECONDS_PER_YEAR,  # Convert m²/s to m²/yr
        ocr=layer.OCR,
        k_h=layer.k_h,
        uscs_type=uscs_type,
        color=color,
    )
