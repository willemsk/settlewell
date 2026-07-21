"""Data models and input validation for bronbemaling dewatering calculation."""
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class AquiferType(Enum):
    """Type of aquifer for hydraulic calculations."""
    CONFINED = "confined"       # Afgesloten watervoerend pakket
    UNCONFINED = "unconfined"   # Freatisch watervoerend pakket


class BuildingType(Enum):
    """Building construction type for damage classification."""
    MASONRY = "masonry"              # Metselwerk
    CONCRETE_FRAME = "concrete_frame" # Betonskelet


@dataclass
class SoilLayer:
    """A single soil layer with geotechnical properties.
    
    All properties in SI units. Each layer is horizontal and uniform.
    """
    name: str                    # e.g., "Klei" or "Zand"
    thickness: float             # [m] Layer thickness
    gamma: float                 # [kN/m³] Dry unit weight
    gamma_sat: float             # [kN/m³] Saturated unit weight
    k_h: float                   # [m/s] Horizontal hydraulic conductivity
    e0: float                    # [-] Initial void ratio
    Cc: float                    # [-] Compression index (virgin compression)
    Cr: float                    # [-] Recompression index (swelling/recompression)
    Eoed: float                  # [kPa] Oedometric (constrained) modulus
    Cv: float                    # [m²/s] Coefficient of consolidation
    OCR: float = 1.0            # [-] Overconsolidation ratio

    def __post_init__(self) -> None:
        if self.thickness <= 0:
            raise ValueError(f"Soil layer thickness must be > 0, got {self.thickness}")
        if self.gamma <= 0:
            raise ValueError(f"Dry unit weight gamma must be > 0, got {self.gamma}")
        if self.gamma_sat <= 0:
            raise ValueError(f"Saturated unit weight gamma_sat must be > 0, got {self.gamma_sat}")
        if self.gamma_sat < self.gamma:
            raise ValueError(
                f"Saturated unit weight ({self.gamma_sat}) cannot be less than dry unit weight ({self.gamma})"
            )
        if self.k_h <= 0:
            raise ValueError(f"Hydraulic conductivity k_h must be > 0, got {self.k_h}")
        if self.e0 < 0:
            raise ValueError(f"Initial void ratio e0 must be >= 0, got {self.e0}")
        if self.Cc < 0:
            raise ValueError(f"Compression index Cc must be >= 0, got {self.Cc}")
        if self.Cr < 0:
            raise ValueError(f"Recompression index Cr must be >= 0, got {self.Cr}")
        if self.Eoed <= 0:
            raise ValueError(f"Oedometric modulus Eoed must be > 0, got {self.Eoed}")
        if self.Cv < 0:
            raise ValueError(f"Coefficient of consolidation Cv must be >= 0, got {self.Cv}")
        if self.OCR < 1.0:
            raise ValueError(f"Overconsolidation ratio OCR must be >= 1.0, got {self.OCR}")


@dataclass
class SoilProfile:
    """Multi-layer soil profile with groundwater level.
    
    Layers are ordered top-to-bottom. The first layer starts at ground surface (z=0).
    """
    layers: list[SoilLayer]
    gwl_mtaw: float              # [mTAW] Groundwater level in Belgian datum (Tweede Algemene Waterpassing)
    surface_level_mtaw: float    # [mTAW] Ground surface level in Belgian datum

    def __post_init__(self) -> None:
        if not self.layers:
            raise ValueError("SoilProfile must contain at least one SoilLayer.")
        if self.gwl_mtaw > self.surface_level_mtaw:
            raise ValueError(
                f"Groundwater level ({self.gwl_mtaw} mTAW) cannot be above surface level ({self.surface_level_mtaw} mTAW)."
            )

    @property
    def gwl_depth(self) -> float:
        """[m] Depth of groundwater below surface (positive downward)."""
        return self.surface_level_mtaw - self.gwl_mtaw

    @property
    def total_depth(self) -> float:
        """[m] Total depth of all layers combined."""
        return sum(layer.thickness for layer in self.layers)


@dataclass
class Well:
    """A single dewatering well."""
    x: float                     # [m] X-coordinate in local system
    y: float                     # [m] Y-coordinate in local system
    Q: float                     # [m³/s] Pumping rate (positive = extraction)
    r_w: float = 0.075           # [m] Well radius (default 150mm diameter)
    screen_top_mtaw: float = 0.0 # [mTAW] Top of well screen
    screen_bottom_mtaw: float = 0.0  # [mTAW] Bottom of well screen


@dataclass
class ConstructionPit:
    """Rectangular construction pit geometry."""
    length: float                # [m] Pit length (x-direction)
    width: float                 # [m] Pit width (y-direction)
    depth: float                 # [m] Pit depth below surface
    center_x: float = 0.0       # [m] X-coordinate of pit center
    center_y: float = 0.0       # [m] Y-coordinate of pit center
    bottom_mtaw: float = 0.0    # [mTAW] Pit bottom level


@dataclass
class DewateringConfig:
    """Dewatering well configuration and hydraulic parameters."""
    wells: list[Well]
    target_drawdown_mtaw: float  # [mTAW] Target water level inside the pit
    original_gwl_mtaw: float     # [mTAW] Original (undisturbed) groundwater level
    pumping_duration_days: float # [days] Duration of pumping
    aquifer_type: AquiferType = AquiferType.UNCONFINED
    R: Optional[float] = None   # [m] Radius of influence (computed via Sichardt if None)
    T: Optional[float] = None   # [m²/s] Transmissivity (computed from layers if None)
    S: Optional[float] = None   # [-] Storativity (computed from layers if None)

    @property
    def target_drawdown(self) -> float:
        """[m] Total drawdown from original GWL to target level."""
        return self.original_gwl_mtaw - self.target_drawdown_mtaw


@dataclass
class Building:
    """Neighboring building to assess for settlement damage."""
    x: float                     # [m] X-coordinate of building center
    y: float                     # [m] Y-coordinate of building center
    length: float                # [m] Building length
    width: float                 # [m] Building width
    orientation_deg: float = 0.0 # [°] Rotation angle from x-axis
    foundation_depth: float = 0.6  # [m] Foundation depth below surface
    building_type: BuildingType = BuildingType.MASONRY

    def corner_coordinates(self) -> list[tuple[float, float]]:
        """Return (x, y) coordinates of the 4 building corners, accounting for orientation.
        
        Implementation:
        1. Define corners relative to center: (±length/2, ±width/2)
        2. Apply 2D rotation matrix using orientation_deg
        3. Translate to (self.x, self.y)
        
        Returns list of 4 tuples: [bottom-left, bottom-right, top-right, top-left]
        """
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
        """Return 5 evaluation points: center + 4 corners.
        
        Returns list of 5 tuples: [center, corner1, corner2, corner3, corner4]
        """
        return [(self.x, self.y)] + self.corner_coordinates()
