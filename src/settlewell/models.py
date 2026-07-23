"""Domain data models and input validation for ground settlement calculations.

This module provides frozen/dataclass input structures for soil layers,
soil profiles, wells, construction pit geometries, dewatering configurations,
and neighboring buildings.
"""

import math
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple


class AquiferType(Enum):
    """Type of aquifer for hydraulic calculations.

    Attributes
    ----------
    CONFINED : str
        Confined aquifer (Afgesloten watervoerend pakket).
    UNCONFINED : str
        Unconfined/phreatic aquifer (Freatisch watervoerend pakket).
    """

    CONFINED = "confined"
    UNCONFINED = "unconfined"


class BuildingType(Enum):
    """Building construction type for damage classification.

    Attributes
    ----------
    MASONRY : str
        Masonry structure (Metselwerk).
    CONCRETE_FRAME : str
        Concrete frame structure (Betonskelet).
    """

    MASONRY = "masonry"
    CONCRETE_FRAME = "concrete_frame"


@dataclass
class SoilLayer:
    """Geotechnical properties of a single horizontal soil layer.

    All properties are specified in SI units. Each layer is assumed
    homogeneous and horizontally uniform.

    Parameters
    ----------
    name : str
        Name or description of soil layer (e.g. "Klei" or "Zand").
    thickness : float
        Thickness of the layer [m]. Must be > 0.
    gamma : float
        Dry unit weight of soil [kN/m³]. Must be > 0.
    gamma_sat : float
        Saturated unit weight of soil [kN/m³]. Must be >= gamma.
    k_h : float
        Horizontal hydraulic conductivity [m/s]. Must be > 0.
    e0 : float
        Initial void ratio [-]. Must be >= 0.
    Cc : float
        Compression index for virgin compression [-]. Must be >= 0.
    Cr : float
        Recompression/swelling index [-]. Must be >= 0.
    Eoed : float
        Oedometric (constrained) modulus [kPa]. Must be > 0.
    Cv : float
        Coefficient of consolidation [m²/s]. Must be >= 0.
    OCR : float, default 1.0
        Overconsolidation ratio [-]. Must be >= 1.0.

    Raises
    ------
    ValueError
        If any input parameters violate physical constraints.
    """

    name: str
    thickness: float
    gamma: float
    gamma_sat: float
    k_h: float
    e0: float
    Cc: float
    Cr: float
    Eoed: float
    Cv: float
    OCR: float = 1.0

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
        if self.e0 <= 0:
            raise ValueError(f"Initial void ratio e0 must be > 0, got {self.e0}")
        if self.Cc < 0:
            raise ValueError(f"Compression index Cc must be >= 0, got {self.Cc}")
        if self.Cr < 0:
            raise ValueError(f"Recompression index Cr must be >= 0, got {self.Cr}")
        if self.Cr > self.Cc:
            raise ValueError(
                f"Recompression index Cr ({self.Cr}) cannot exceed virgin compression index Cc ({self.Cc})"
            )
        if self.Eoed <= 0:
            raise ValueError(f"Oedometric modulus Eoed must be > 0, got {self.Eoed}")
        if self.Cv < 0:
            raise ValueError(f"Coefficient of consolidation Cv must be >= 0, got {self.Cv}")
        if self.OCR < 1.0:
            raise ValueError(f"Overconsolidation ratio OCR must be >= 1.0, got {self.OCR}")


@dataclass
class SoilProfile:
    """Multi-layer soil profile with groundwater level.

    Layers are ordered top-to-bottom starting at the ground surface (z = 0).

    Parameters
    ----------
    layers : List[SoilLayer]
        List of soil layers ordered from top to bottom. Must not be empty.
    gwl_mtaw : float
        Groundwater level in Belgian datum mTAW [m].
    surface_level_mtaw : float
        Ground surface level in Belgian datum mTAW [m].

    Raises
    ------
    ValueError
        If `layers` is empty or `gwl_mtaw > surface_level_mtaw`.
    """

    layers: List[SoilLayer]
    gwl_mtaw: float
    surface_level_mtaw: float

    def __post_init__(self) -> None:
        if not self.layers:
            raise ValueError("SoilProfile must contain at least one SoilLayer.")
        if self.gwl_mtaw > self.surface_level_mtaw:
            raise ValueError(
                f"Groundwater level ({self.gwl_mtaw} mTAW) cannot be above surface level ({self.surface_level_mtaw} mTAW)."
            )

    @property
    def gwl_depth(self) -> float:
        """Depth of groundwater table below surface.

        Returns
        -------
        float
            Groundwater table depth [m] (positive downward).
        """
        return self.surface_level_mtaw - self.gwl_mtaw

    @property
    def total_depth(self) -> float:
        """Total depth of soil profile across all layers.

        Returns
        -------
        float
            Sum of thickness of all soil layers [m].
        """
        return sum(layer.thickness for layer in self.layers)

    def mtaw_to_depth(self, elevation_mtaw: float) -> float:
        """Convert Belgian datum elevation (mTAW) to depth below ground surface [m].

        Parameters
        ----------
        elevation_mtaw : float
            Elevation in mTAW [m].

        Returns
        -------
        float
            Depth below ground surface [m] (positive downward).
        """
        return self.surface_level_mtaw - elevation_mtaw

    def depth_to_mtaw(self, depth: float) -> float:
        """Convert depth below ground surface [m] to Belgian datum elevation (mTAW).

        Parameters
        ----------
        depth : float
            Depth below ground surface [m] (positive downward).

        Returns
        -------
        float
            Elevation in mTAW [m].
        """
        return self.surface_level_mtaw - depth


@dataclass
class Well:
    """Specification of a single dewatering well.

    Parameters
    ----------
    x : float
        X-coordinate of well location [m].
    y : float
        Y-coordinate of well location [m].
    Q : float
        Pumping rate [m³/s] (positive value denotes extraction).
    r_w : float, default 0.075
        Radius of well casing [m].
    screen_top_mtaw : float, default 0.0
        Top elevation of well screen [mTAW].
    screen_bottom_mtaw : float, default 0.0
        Bottom elevation of well screen [mTAW].
    """

    x: float
    y: float
    Q: float
    r_w: float = 0.075
    screen_top_mtaw: float = 0.0
    screen_bottom_mtaw: float = 0.0

    def __post_init__(self) -> None:
        if self.r_w <= 0:
            raise ValueError(f"Well radius r_w must be > 0, got {self.r_w}")
        if self.screen_top_mtaw < self.screen_bottom_mtaw:
            raise ValueError(
                f"Well screen_top_mtaw ({self.screen_top_mtaw}) cannot be below screen_bottom_mtaw ({self.screen_bottom_mtaw})"
            )


@dataclass
class ConstructionPit:
    """Rectangular excavation geometry for a construction pit.

    Parameters
    ----------
    length : float
        Length of pit along x-axis [m].
    width : float
        Width of pit along y-axis [m].
    depth : float
        Depth of excavation below surface [m].
    center_x : float, default 0.0
        X-coordinate of pit center [m].
    center_y : float, default 0.0
        Y-coordinate of pit center [m].
    bottom_mtaw : float, default 0.0
        Bottom level of pit in Belgian datum mTAW [m].
    """

    length: float
    width: float
    depth: float
    center_x: float = 0.0
    center_y: float = 0.0
    bottom_mtaw: float = 0.0

    def __post_init__(self) -> None:
        if self.length <= 0:
            raise ValueError(f"ConstructionPit length must be > 0, got {self.length}")
        if self.width <= 0:
            raise ValueError(f"ConstructionPit width must be > 0, got {self.width}")
        if self.depth <= 0:
            raise ValueError(f"ConstructionPit depth must be > 0, got {self.depth}")


@dataclass
class DewateringConfig:
    """Dewatering system layout and hydraulic target parameters.

    Parameters
    ----------
    wells : List[Well]
        List of active dewatering wells.
    target_drawdown_mtaw : float
        Target lowered water level inside excavation pit [mTAW].
    original_gwl_mtaw : float
        Original undisturbed groundwater level [mTAW].
    pumping_duration_days : float
        Total duration of dewatering operation [days].
    aquifer_type : AquiferType, default AquiferType.UNCONFINED
        Aquifer classification (`CONFINED` or `UNCONFINED`).
    R : float, optional
        Radius of influence [m]. Computed via Sichardt formula if None.
    T : float, optional
        Transmissivity [m²/s]. Computed from soil layers if None.
    S : float, optional
        Storativity / specific yield [-]. Computed from soil layers if None.
    """

    wells: List[Well]
    target_drawdown_mtaw: float
    original_gwl_mtaw: float
    pumping_duration_days: float
    aquifer_type: AquiferType = AquiferType.UNCONFINED
    R: Optional[float] = None
    T: Optional[float] = None
    S: Optional[float] = None

    def __post_init__(self) -> None:
        if self.target_drawdown_mtaw > self.original_gwl_mtaw:
            raise ValueError(
                f"target_drawdown_mtaw ({self.target_drawdown_mtaw}) cannot be above original_gwl_mtaw ({self.original_gwl_mtaw})"
            )
        if self.pumping_duration_days <= 0:
            raise ValueError(
                f"pumping_duration_days must be > 0, got {self.pumping_duration_days}"
            )
        if self.R is not None and self.R <= 0:
            raise ValueError(f"Radius of influence R must be > 0 if specified, got {self.R}")
        if self.T is not None and self.T <= 0:
            raise ValueError(f"Transmissivity T must be > 0 if specified, got {self.T}")
        if self.S is not None and self.S <= 0:
            raise ValueError(f"Storativity S must be > 0 if specified, got {self.S}")

    @property
    def target_drawdown(self) -> float:
        """Total target drawdown magnitude.

        Returns
        -------
        float
            Target drawdown [m] from original groundwater level.
        """
        return self.original_gwl_mtaw - self.target_drawdown_mtaw


@dataclass
class Building:
    """Neighboring building structure for settlement damage assessment.

    Parameters
    ----------
    x : float
        X-coordinate of building center [m].
    y : float
        Y-coordinate of building center [m].
    length : float
        Building footprint length [m].
    width : float
        Building footprint width [m].
    orientation_deg : float, default 0.0
        Rotation angle from x-axis in degrees [°].
    foundation_depth : float, default 0.6
        Foundation depth below ground surface [m].
    building_type : BuildingType, default BuildingType.MASONRY
        Building structural type (`MASONRY` or `CONCRETE_FRAME`).
    """

    x: float
    y: float
    length: float
    width: float
    orientation_deg: float = 0.0
    foundation_depth: float = 0.6
    building_type: BuildingType = BuildingType.MASONRY

    def __post_init__(self) -> None:
        if self.length <= 0:
            raise ValueError(f"Building length must be > 0, got {self.length}")
        if self.width <= 0:
            raise ValueError(f"Building width must be > 0, got {self.width}")
        if self.foundation_depth < 0:
            raise ValueError(
                f"Building foundation_depth must be >= 0, got {self.foundation_depth}"
            )

    def corner_coordinates(self) -> List[Tuple[float, float]]:
        """Compute (x, y) coordinates of the 4 building corners.

        Accounts for building center translation and orientation angle.

        Returns
        -------
        List[Tuple[float, float]]
            List of 4 corner coordinate pairs:
            [bottom-left, bottom-right, top-right, top-left].
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

    def evaluation_points(self) -> List[Tuple[float, float]]:
        """Get key evaluation points for building damage assessment.

        Returns
        -------
        List[Tuple[float, float]]
            List of 5 evaluation points: [center, corner1, corner2, corner3, corner4].
        """
        return [(self.x, self.y)] + self.corner_coordinates()
