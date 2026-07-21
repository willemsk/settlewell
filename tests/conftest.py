"""Shared pytest fixtures for bronbemaling test suite."""
import pytest
import numpy as np
from bronbemaling import (
    SoilLayer,
    SoilProfile,
    Well,
    ConstructionPit,
    DewateringConfig,
    Building,
    AquiferType,
    BuildingType,
)


@pytest.fixture
def single_sand_layer() -> SoilLayer:
    """A single sand layer for isolated tests."""
    return SoilLayer(
        name="Zand", thickness=5.0, gamma=17.5, gamma_sat=20.0,
        k_h=1e-4, e0=0.5, Cc=0.02, Cr=0.005, Eoed=30000, Cv=1e-2, OCR=1.0,
    )


@pytest.fixture
def single_clay_layer() -> SoilLayer:
    """A single clay layer for consolidation tests."""
    return SoilLayer(
        name="Klei", thickness=3.0, gamma=16.0, gamma_sat=18.5,
        k_h=1e-9, e0=1.0, Cc=0.30, Cr=0.06, Eoed=3000, Cv=1e-7, OCR=1.5,
    )


@pytest.fixture
def simple_profile(single_sand_layer) -> SoilProfile:
    """Single-layer sand profile for hydraulic tests."""
    return SoilProfile(
        layers=[single_sand_layer],
        gwl_mtaw=4.0,
        surface_level_mtaw=5.0,
    )


@pytest.fixture
def flemish_profile() -> SoilProfile:
    """Default 4-layer Flemish lowland scenario."""
    return SoilProfile(
        surface_level_mtaw=5.0,
        gwl_mtaw=4.0,
        layers=[
            SoilLayer("Aanvulling", 0.5, 17.0, 19.0, 1e-5, 0.6, 0.05, 0.01, 15000, 1e-4, 3.0),
            SoilLayer("Zand",       2.0, 17.5, 20.0, 1e-4, 0.5, 0.02, 0.005, 30000, 1e-2, 1.5),
            SoilLayer("Klei",       3.0, 16.0, 18.5, 1e-9, 1.0, 0.30, 0.06, 3000, 1e-7, 1.5),
            SoilLayer("Zand diep",  4.5, 18.0, 20.5, 5e-4, 0.45, 0.01, 0.003, 40000, 1e-2, 1.0),
        ],
    )


@pytest.fixture
def single_well() -> Well:
    """A single well at the origin."""
    return Well(x=0.0, y=0.0, Q=0.001, r_w=0.075,
                screen_top_mtaw=3.0, screen_bottom_mtaw=0.0)


@pytest.fixture
def pit() -> ConstructionPit:
    """Default rectangular pit."""
    return ConstructionPit(length=10.0, width=8.0, depth=3.0,
                           center_x=0.0, center_y=0.0, bottom_mtaw=2.0)


@pytest.fixture
def six_well_config() -> DewateringConfig:
    """Default 6-well dewatering configuration."""
    wells = [
        Well(x=-5.5, y=-4.5, Q=0.0005, screen_top_mtaw=3.0, screen_bottom_mtaw=0.0),
        Well(x=0.0,  y=-4.5, Q=0.0005, screen_top_mtaw=3.0, screen_bottom_mtaw=0.0),
        Well(x=5.5,  y=-4.5, Q=0.0005, screen_top_mtaw=3.0, screen_bottom_mtaw=0.0),
        Well(x=-5.5, y=4.5,  Q=0.0005, screen_top_mtaw=3.0, screen_bottom_mtaw=0.0),
        Well(x=0.0,  y=4.5,  Q=0.0005, screen_top_mtaw=3.0, screen_bottom_mtaw=0.0),
        Well(x=5.5,  y=4.5,  Q=0.0005, screen_top_mtaw=3.0, screen_bottom_mtaw=0.0),
    ]
    return DewateringConfig(
        wells=wells, target_drawdown_mtaw=1.5, original_gwl_mtaw=4.0,
        pumping_duration_days=90, aquifer_type=AquiferType.UNCONFINED,
    )


@pytest.fixture
def building() -> Building:
    """Default neighboring building."""
    return Building(x=12.0, y=0.0, length=10.0, width=6.0,
                    foundation_depth=0.6, building_type=BuildingType.MASONRY)
