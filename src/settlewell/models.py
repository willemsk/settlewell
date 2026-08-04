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
    thickness: float = Field(gt=0.0)
    gamma: float = Field(gt=0.0)
    gamma_sat: float = Field(gt=0.0)
    k_h: float = Field(gt=0.0, default=1e-4)
    e0: float = Field(gt=0.0)
    Cc: float = Field(ge=0.0)
    Cr: float = Field(ge=0.0)
    Eoed: float = Field(gt=0.0)
    Cv: float = Field(ge=0.0)
    OCR: float = Field(ge=1.0, default=1.0)
    id: str | None = Field(default=None)
    color: str = Field(default="#f59e0b")
    uscs_type: SoilTypeUSCS = Field(default=SoilTypeUSCS.SAND)
    flemish_type: FlemishSoilType = Field(default=FlemishSoilType.PLEISTOCEEN_ZAND)

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
    gwl_mtaw: float
    surface_level_mtaw: float

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
    y: float
    Q: float
    id: str | None = Field(default=None)
    name: str = Field(default="Well")
    r_w: float = Field(gt=0.0, default=0.075)
    screen_top_mtaw: float = 0.0
    screen_bottom_mtaw: float = 0.0

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
    width: float = Field(gt=0.0, default=15.0)
    depth: float = Field(gt=0.0, default=4.0)
    center_x: float = 0.0
    center_y: float = 0.0
    bottom_mtaw: float = 0.0

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
    target_drawdown_mtaw: float = -2.0
    original_gwl_mtaw: float = 4.0
    pumping_duration_days: float = Field(gt=0.0, default=30.0)
    aquifer_type: AquiferType = AquiferType.UNCONFINED
    R: float | None = Field(gt=0.0, default=None)
    T: float | None = Field(gt=0.0, default=None)
    S: float | None = Field(gt=0.0, default=None)

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
    y: float = 0.0
    length: float = Field(gt=0.0, default=10.0)
    width: float = Field(gt=0.0, default=8.0)
    id: str | None = Field(default=None)
    name: str = Field(default="Building")
    orientation_deg: float = 0.0
    foundation_depth: float = Field(ge=0.0, default=0.6)
    building_type: BuildingType = BuildingType.MASONRY


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
    name: str = Field(default="Footing Load")
    type: LoadType = Field(default=LoadType.RECTANGULAR)
    x_center: float = 0.0
    z_surface_offset: float = 0.0
    width_B: float = Field(gt=0.0, default=4.0)
    length_L: float = Field(gt=0.0, default=8.0)
    stress_q: float = Field(gt=0.0, default=100.0)


class SolverSettings(BaseDomainModel):
    """Calculation settings for numerical and analytical solvers."""

    stress_method: StressMethod = Field(default=StressMethod.BOUSSINESQ)
    drainage: DrainageType = Field(default=DrainageType.DOUBLE)
    design_approach: DesignApproach = Field(default=DesignApproach.SLS_CHARACTERISTIC)
    hydraulics_solver: str = Field(default="analytical")
    settlement_method: str = Field(default="cc_cr")
    z_max: float = Field(gt=0.0, default=20.0)
    delta_z: float = Field(gt=0.0, default=0.25)
    grid_dx: float = Field(gt=0.0, default=1.0)
    grid_padding: float = Field(gt=0.0, default=50.0)
    x_min: float = -15.0
    x_max: float = 15.0
    t_start_days: float = Field(ge=1.0, default=1.0)
    t_end_years: float = Field(gt=0.0, default=50.0)
    calculate_creep: bool = True
