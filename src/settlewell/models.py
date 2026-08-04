"""Domain data models and input validation for ground settlement calculations.

This module provides Pydantic V2 data models for soil layers,
soil profiles, wells, construction pit geometries, dewatering configurations,
neighboring buildings, load geometries, and solver settings.
"""

import math
from enum import StrEnum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class AquiferType(StrEnum):
    """Type of aquifer for hydraulic calculations."""

    CONFINED = "confined"
    UNCONFINED = "unconfined"


class BuildingType(StrEnum):
    """Building construction type for damage classification."""

    MASONRY = "masonry"
    CONCRETE_FRAME = "concrete_frame"


class SoilTypeUSCS(StrEnum):
    """USCS Soil Classification types for visualization and hatching."""

    SAND = "SAND"
    CLAY = "CLAY"
    GRAVEL = "GRAVEL"
    PEAT = "PEAT"


class FlemishSoilType(StrEnum):
    """NBN EN 1997-1 ANB Flemish standard soil classification types."""

    BOOMSE_KLEI = "BOOMSE_KLEI"
    IEPERSE_KLEI = "IEPERSE_KLEI"
    ALLUVIALE_KLEI = "ALLUVIALE_KLEI"
    BRABANTSE_LEEM = "BRABANTSE_LEEM"
    PLEISTOCEEN_ZAND = "PLEISTOCEEN_ZAND"
    DIESTIAAN_ZAND = "DIESTIAAN_ZAND"
    BRUSSELIAAN_ZAND = "BRUSSELIAAN_ZAND"
    MAASGRIND = "MAASGRIND"
    HOLOCEEN_VEEN = "HOLOCEEN_VEEN"
    ANTROPOGEEN = "ANTROPOGEEN"


class LoadType(StrEnum):
    """Geometry type for surface load distribution."""

    STRIP = "STRIP"
    RECTANGULAR = "RECTANGULAR"
    EMBANKMENT = "EMBANKMENT"
    POINT = "POINT"


class StressMethod(StrEnum):
    """Method for vertical stress distribution calculations."""

    BOUSSINESQ = "BOUSSINESQ"
    WESTERGAARD = "WESTERGAARD"
    TWO_TO_ONE = "2:1"


class DrainageType(StrEnum):
    """Consolidation drainage condition."""

    DOUBLE = "DOUBLE"
    SINGLE = "SINGLE"


class DesignApproach(StrEnum):
    """Eurocode 7 design approach or SLS verification mode."""

    SLS_CHARACTERISTIC = "SLS_CHARACTERISTIC"
    EC7_DA1_M1 = "EC7_DA1_M1"
    EC7_DA1_M2 = "EC7_DA1_M2"


class BaseDomainModel(BaseModel):
    """Base Pydantic V2 model supporting positional arguments for backwards compatibility."""

    model_config = ConfigDict(frozen=True)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if args:
            fields = list(self.__class__.model_fields.keys())
            for name, arg in zip(fields, args):
                kwargs[name] = arg
        super().__init__(**kwargs)


class SoilLayer(BaseDomainModel):
    """Geotechnical properties of a single horizontal soil layer."""

    name: str
    """Name or descriptive label for this soil layer."""
    thickness: float = Field(gt=0.0)
    """Thickness of the layer [m]."""
    gamma: float = Field(gt=0.0)
    """Dry unit weight [kN/m³]."""
    gamma_sat: float = Field(gt=0.0)
    """Saturated unit weight [kN/m³]."""
    k_h: float = Field(gt=0.0, default=1e-4)
    """Horizontal hydraulic conductivity [m/s]."""
    e0: float = Field(gt=0.0)
    """Initial void ratio [-]."""
    Cc: float = Field(ge=0.0)
    """Virgin compression index [-]."""
    Cr: float = Field(ge=0.0)
    """Recompression (swelling) index [-]."""
    Eoed: float = Field(gt=0.0)
    """Oedometric constrained modulus [kPa]."""
    Cv: float = Field(ge=0.0)
    """Coefficient of consolidation [m²/s]."""
    OCR: float = Field(ge=1.0, default=1.0)
    """Overconsolidation ratio [-]."""
    id: str | None = Field(default=None)
    """Optional unique identifier."""
    color: str = Field(default="#f59e0b")
    """Hex color code for plotting (e.g. '#f59e0b')."""
    uscs_type: SoilTypeUSCS = Field(default=SoilTypeUSCS.SAND)
    """USCS classification type for hatching."""
    flemish_type: FlemishSoilType = Field(default=FlemishSoilType.PLEISTOCEEN_ZAND)
    """Flemish standard soil classification type."""

    @property
    def gamma_dry(self) -> float:
        """Alias for gamma (dry unit weight) for GUI backward compatibility."""
        return self.gamma

    @property
    def E_modulus(self) -> float:
        """Alias for Eoed in MPa for GUI backward compatibility."""
        return self.Eoed / 1000.0

    @property
    def ocr(self) -> float:
        """Alias for OCR for GUI backward compatibility."""
        return self.OCR

    @classmethod
    def _v_thickness(cls, v: Any) -> Any:
        if isinstance(v, (int, float)) and v <= 0:
            raise ValueError(f"Soil layer thickness must be > 0, got {v}")
        return v

    @field_validator("gamma", mode="before")
    @classmethod
    def _v_gamma(cls, v: Any) -> Any:
        if isinstance(v, (int, float)) and v <= 0:
            raise ValueError(f"Dry unit weight gamma must be > 0, got {v}")
        return v

    @field_validator("gamma_sat", mode="before")
    @classmethod
    def _v_gamma_sat(cls, v: Any) -> Any:
        if isinstance(v, (int, float)) and v <= 0:
            raise ValueError(f"Saturated unit weight gamma_sat must be > 0, got {v}")
        return v

    @field_validator("k_h", mode="before")
    @classmethod
    def _v_k_h(cls, v: Any) -> Any:
        if isinstance(v, (int, float)) and v <= 0:
            raise ValueError(f"Hydraulic conductivity k_h must be > 0, got {v}")
        return v

    @field_validator("e0", mode="before")
    @classmethod
    def _v_e0(cls, v: Any) -> Any:
        if isinstance(v, (int, float)) and v <= 0:
            raise ValueError(f"Initial void ratio e0 must be > 0, got {v}")
        return v

    @field_validator("Cc", mode="before")
    @classmethod
    def _v_Cc(cls, v: Any) -> Any:
        if isinstance(v, (int, float)) and v < 0:
            raise ValueError(f"Compression index Cc must be >= 0, got {v}")
        return v

    @field_validator("Cr", mode="before")
    @classmethod
    def _v_Cr(cls, v: Any) -> Any:
        if isinstance(v, (int, float)) and v < 0:
            raise ValueError(f"Recompression index Cr must be >= 0, got {v}")
        return v

    @field_validator("Eoed", mode="before")
    @classmethod
    def _v_Eoed(cls, v: Any) -> Any:
        if isinstance(v, (int, float)) and v <= 0:
            raise ValueError(f"Oedometric modulus Eoed must be > 0, got {v}")
        return v

    @field_validator("Cv", mode="before")
    @classmethod
    def _v_Cv(cls, v: Any) -> Any:
        if isinstance(v, (int, float)) and v < 0:
            raise ValueError(f"Coefficient of consolidation Cv must be >= 0, got {v}")
        return v

    @field_validator("OCR", mode="before")
    @classmethod
    def _v_OCR(cls, v: Any) -> Any:
        if isinstance(v, (int, float)) and v < 1.0:
            raise ValueError(f"Overconsolidation ratio OCR must be >= 1.0, got {v}")
        return v

    @model_validator(mode="after")
    def validate_soil_layer_physics(self) -> "SoilLayer":
        if self.gamma_sat < self.gamma:
            raise ValueError(
                f"Saturated unit weight ({self.gamma_sat}) cannot be less than dry unit weight ({self.gamma})"
            )
        if self.Cr > self.Cc:
            raise ValueError(
                f"Recompression index Cr ({self.Cr}) cannot exceed virgin compression index Cc ({self.Cc})"
            )
        return self


class SoilProfile(BaseDomainModel):
    """Multi-layer soil profile with groundwater level."""

    layers: list[SoilLayer] = Field(min_length=1)
    """List of soil layers ordered from top to bottom."""
    gwl_mtaw: float
    """Groundwater level elevation [mTAW]."""
    surface_level_mtaw: float
    """Ground surface elevation [mTAW]."""

    @field_validator("layers", mode="before")
    @classmethod
    def _v_layers(cls, v: Any) -> Any:
        if isinstance(v, list) and not v:
            raise ValueError("SoilProfile must contain at least one SoilLayer.")
        return v

    @model_validator(mode="after")
    def validate_gwl(self) -> "SoilProfile":
        if not self.layers:
            raise ValueError("SoilProfile must contain at least one SoilLayer.")
        if self.gwl_mtaw > self.surface_level_mtaw:
            raise ValueError(
                f"Groundwater level ({self.gwl_mtaw} mTAW) cannot be above surface level ({self.surface_level_mtaw} mTAW)."
            )
        return self

    @property
    def gwl_depth(self) -> float:
        """Depth of groundwater table below surface."""
        return self.surface_level_mtaw - self.gwl_mtaw

    @property
    def total_depth(self) -> float:
        """Total depth of soil profile across all layers."""
        return sum(layer.thickness for layer in self.layers)

    def mtaw_to_depth(self, elevation_mtaw: float) -> float:
        """Convert Belgian datum elevation (mTAW) to depth below ground surface [m]."""
        return self.surface_level_mtaw - elevation_mtaw

    def depth_to_mtaw(self, depth: float) -> float:
        """Convert depth below ground surface [m] to Belgian datum elevation (mTAW)."""
        return self.surface_level_mtaw - depth


class Well(BaseDomainModel):
    """Specification of a single dewatering well."""

    x: float
    """X-coordinate of the well [m]."""
    y: float
    """Y-coordinate of the well [m]."""
    Q: float
    """Pumping rate (discharge) [m³/s]. Use positive values for extraction."""
    id: str | None = Field(default=None)
    """Optional unique identifier."""
    name: str = Field(default="Well")
    """Descriptive name for the well."""
    r_w: float = Field(gt=0.0, default=0.075)
    """Well radius [m]."""
    screen_top_mtaw: float = 0.0
    """Top elevation of the well screen [mTAW]."""
    screen_bottom_mtaw: float = 0.0
    """Bottom elevation of the well screen [mTAW]."""

    @field_validator("r_w", mode="before")
    @classmethod
    def _v_r_w(cls, v: Any) -> Any:
        if isinstance(v, (int, float)) and v <= 0:
            raise ValueError(f"Well radius r_w must be > 0, got {v}")
        return v

    @model_validator(mode="after")
    def validate_screen(self) -> "Well":
        if self.screen_top_mtaw < self.screen_bottom_mtaw:
            raise ValueError(
                f"Well screen_top_mtaw ({self.screen_top_mtaw}) cannot be below screen_bottom_mtaw ({self.screen_bottom_mtaw})"
            )
        return self


class ConstructionPit(BaseDomainModel):
    """Rectangular excavation geometry for a construction pit."""

    length: float = Field(gt=0.0, default=20.0)
    """Length of the excavation pit [m]."""
    width: float = Field(gt=0.0, default=15.0)
    """Width of the excavation pit [m]."""
    depth: float = Field(gt=0.0, default=4.0)
    """Depth of the excavation below surface level [m]."""
    center_x: float = 0.0
    """X-coordinate of the pit's center [m]."""
    center_y: float = 0.0
    """Y-coordinate of the pit's center [m]."""
    bottom_mtaw: float = 0.0
    """Elevation of the pit bottom [mTAW]."""

    @field_validator("length", mode="before")
    @classmethod
    def _v_length(cls, v: Any) -> Any:
        if isinstance(v, (int, float)) and v <= 0:
            raise ValueError(f"ConstructionPit length must be > 0, got {v}")
        return v

    @field_validator("width", mode="before")
    @classmethod
    def _v_width(cls, v: Any) -> Any:
        if isinstance(v, (int, float)) and v <= 0:
            raise ValueError(f"ConstructionPit width must be > 0, got {v}")
        return v

    @field_validator("depth", mode="before")
    @classmethod
    def _v_depth(cls, v: Any) -> Any:
        if isinstance(v, (int, float)) and v <= 0:
            raise ValueError(f"ConstructionPit depth must be > 0, got {v}")
        return v


class DewateringConfig(BaseDomainModel):
    """Dewatering system layout and hydraulic target parameters."""

    wells: list[Well] = Field(default_factory=list)
    """List of dewatering wells."""
    target_drawdown_mtaw: float = -2.0
    """Required groundwater level inside the pit [mTAW]."""
    original_gwl_mtaw: float = 4.0
    """Original undisturbed groundwater level [mTAW]."""
    pumping_duration_days: float = Field(gt=0.0, default=30.0)
    """Duration of the dewatering phase [days]."""
    aquifer_type: AquiferType = AquiferType.UNCONFINED
    """Type of aquifer (confined or unconfined)."""
    R: float | None = Field(gt=0.0, default=None)
    """Radius of influence (Sichardt/Weber) [m]. Computed automatically if None."""
    T: float | None = Field(gt=0.0, default=None)
    """Aquifer transmissivity [m²/s]. Computed automatically if None."""
    S: float | None = Field(gt=0.0, default=None)
    """Aquifer storativity or specific yield [-]."""

    @field_validator("pumping_duration_days", mode="before")
    @classmethod
    def _v_duration(cls, v: Any) -> Any:
        if isinstance(v, (int, float)) and v <= 0:
            raise ValueError(f"pumping_duration_days must be > 0, got {v}")
        return v

    @field_validator("R", mode="before")
    @classmethod
    def _v_R(cls, v: Any) -> Any:
        if isinstance(v, (int, float)) and v <= 0:
            raise ValueError(f"Radius of influence R must be > 0 if specified, got {v}")
        return v

    @field_validator("T", mode="before")
    @classmethod
    def _v_T(cls, v: Any) -> Any:
        if isinstance(v, (int, float)) and v <= 0:
            raise ValueError(f"Transmissivity T must be > 0 if specified, got {v}")
        return v

    @field_validator("S", mode="before")
    @classmethod
    def _v_S(cls, v: Any) -> Any:
        if isinstance(v, (int, float)) and v <= 0:
            raise ValueError(f"Storativity S must be > 0 if specified, got {v}")
        return v

    @model_validator(mode="after")
    def validate_dewatering(self) -> "DewateringConfig":
        if self.target_drawdown_mtaw > self.original_gwl_mtaw:
            raise ValueError(
                f"target_drawdown_mtaw ({self.target_drawdown_mtaw}) cannot be above original_gwl_mtaw ({self.original_gwl_mtaw})"
            )
        return self

    @property
    def target_drawdown(self) -> float:
        """Total target drawdown magnitude."""
        return self.original_gwl_mtaw - self.target_drawdown_mtaw


class Building(BaseDomainModel):
    """Neighboring building structure for settlement damage assessment."""

    x: float = 0.0
    """X-coordinate of the building center [m]."""
    y: float = 0.0
    """Y-coordinate of the building center [m]."""
    length: float = Field(gt=0.0, default=10.0)
    """Length of the building footprint [m]."""
    width: float = Field(gt=0.0, default=8.0)
    """Width of the building footprint [m]."""
    id: str | None = Field(default=None)
    """Optional unique identifier."""
    name: str = Field(default="Building")
    """Descriptive name for the building."""
    orientation_deg: float = 0.0
    """Orientation of the building relative to the x-axis [degrees]."""
    foundation_depth: float = Field(ge=0.0, default=0.6)
    """Depth of the foundation below ground surface [m]."""
    building_type: BuildingType = BuildingType.MASONRY
    """Construction type of the building."""

    @field_validator("length", mode="before")
    @classmethod
    def _v_length(cls, v: Any) -> Any:
        if isinstance(v, (int, float)) and v <= 0:
            raise ValueError(f"Building length must be > 0, got {v}")
        return v

    @field_validator("width", mode="before")
    @classmethod
    def _v_width(cls, v: Any) -> Any:
        if isinstance(v, (int, float)) and v <= 0:
            raise ValueError(f"Building width must be > 0, got {v}")
        return v

    @field_validator("foundation_depth", mode="before")
    @classmethod
    def _v_foundation_depth(cls, v: Any) -> Any:
        if isinstance(v, (int, float)) and v < 0:
            raise ValueError(f"Building foundation_depth must be >= 0, got {v}")
        return v

    def corner_coordinates(self) -> list[tuple[float, float]]:
        """Compute (x, y) coordinates of the 4 building corners."""
        dx = self.length / 2.0
        dy = self.width / 2.0
        rel_corners = [(-dx, -dy), (dx, -dy), (dx, dy), (-dx, dy)]
        rad = math.radians(self.orientation_deg)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)

        abs_corners = []
        for rx, ry in rel_corners:
            x_rot = rx * cos_a - ry * sin_a
            y_rot = rx * sin_a + ry * cos_a
            abs_corners.append((self.x + x_rot, self.y + y_rot))
        return abs_corners

    def evaluation_points(self) -> list[tuple[float, float]]:
        """Get key evaluation points for building damage assessment."""
        return [(self.x, self.y)] + self.corner_coordinates()


class LoadGeometry(BaseDomainModel):
    """Geometry and magnitude of surface loading."""

    id: str | None = Field(default=None)
    """Optional unique identifier."""
    name: str = Field(default="Footing Load")
    """Descriptive name for the load."""
    type: LoadType = Field(default=LoadType.RECTANGULAR)
    """Geometric shape of the load."""
    x_center: float = 0.0
    """X-coordinate of the load center [m]."""
    z_surface_offset: float = 0.0
    """Depth of the load application below ground surface [m]."""
    width_B: float = Field(gt=0.0, default=4.0)
    """Width of the load footprint [m]."""
    length_L: float = Field(gt=0.0, default=8.0)
    """Length of the load footprint [m]."""
    stress_q: float = Field(gt=0.0, default=100.0)
    """Magnitude of the applied surface stress [kPa]."""


class SolverSettings(BaseDomainModel):
    """Calculation settings for numerical and analytical solvers."""

    stress_method: StressMethod = Field(default=StressMethod.BOUSSINESQ)
    """Method used for vertical stress distribution calculations."""
    drainage: DrainageType = Field(default=DrainageType.DOUBLE)
    """Consolidation drainage condition (single or double drainage)."""
    design_approach: DesignApproach = Field(default=DesignApproach.SLS_CHARACTERISTIC)
    """Eurocode 7 design approach for partial safety factors."""
    hydraulics_solver: str = Field(default="analytical")
    """Solver used for hydraulic calculations."""
    settlement_method: str = Field(default="cc_cr")
    """Method used for consolidation settlement calculations."""
    z_max: float = Field(gt=0.0, default=20.0)
    """Maximum depth for vertical stress integration [m]."""
    delta_z: float = Field(gt=0.0, default=0.25)
    """Vertical spatial step size for numerical integration [m]."""
    grid_dx: float = Field(gt=0.0, default=1.0)
    """Horizontal grid spacing for contour plotting and spatial analysis [m]."""
    grid_padding: float = Field(gt=0.0, default=50.0)
    """Extra padding added around defined geometries for the calculation grid [m]."""
    x_min: float = -15.0
    """Minimum X-coordinate for 1D/2D profile generation [m]."""
    x_max: float = 15.0
    """Maximum X-coordinate for 1D/2D profile generation [m]."""
    t_start_days: float = Field(ge=1.0, default=1.0)
    """Starting time for time-dependent settlement analysis [days]."""
    t_end_years: float = Field(gt=0.0, default=50.0)
    """Ending time for time-dependent settlement analysis [years]."""
    calculate_creep: bool = True
    """Flag to enable or disable secondary compression (creep) calculation."""
