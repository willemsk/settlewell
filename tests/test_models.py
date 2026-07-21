"""Unit tests for bronbemaling.models — dataclass properties and validation."""
import pytest
import math
from bronbemaling import SoilLayer, SoilProfile, Building, DewateringConfig, BuildingType


class TestSoilProfile:
    def test_gwl_depth_from_mtaw(self, flemish_profile):
        """gwl_depth = surface_level_mtaw - gwl_mtaw = 5.0 - 4.0 = 1.0 m."""
        assert flemish_profile.gwl_depth == pytest.approx(1.0)

    def test_total_depth(self, flemish_profile):
        """Total depth = 0.5 + 2.0 + 3.0 + 4.5 = 10.0 m."""
        assert flemish_profile.total_depth == pytest.approx(10.0)

    def test_rejects_gwl_above_surface(self):
        """gwl_mtaw > surface_level_mtaw should raise ValueError."""
        with pytest.raises(ValueError):
            SoilProfile(
                layers=[SoilLayer("X", 1.0, 17.0, 19.0, 1e-4, 0.5, 0.02, 0.005, 30000, 1e-2)],
                gwl_mtaw=6.0,  # Above surface
                surface_level_mtaw=5.0,
            )

    def test_rejects_empty_layers(self):
        """Empty layers list should raise ValueError."""
        with pytest.raises(ValueError):
            SoilProfile(layers=[], gwl_mtaw=4.0, surface_level_mtaw=5.0)


class TestSoilLayerValidation:
    @pytest.mark.parametrize("field,value", [
        ("thickness", -1.0),
        ("thickness", 0.0),
        ("gamma", -5.0),
        ("gamma_sat", -5.0),
        ("k_h", -1e-4),
        ("Eoed", 0.0),
        ("OCR", 0.5),
    ])
    def test_rejects_invalid_values(self, field, value):
        """Invalid field values should raise ValueError."""
        kwargs = dict(name="X", thickness=1.0, gamma=17.0, gamma_sat=19.0,
                      k_h=1e-4, e0=0.5, Cc=0.02, Cr=0.005, Eoed=30000, Cv=1e-2, OCR=1.0)
        kwargs[field] = value
        with pytest.raises(ValueError):
            SoilLayer(**kwargs)

    def test_rejects_gamma_sat_less_than_gamma(self):
        """gamma_sat < gamma should raise ValueError."""
        with pytest.raises(ValueError):
            SoilLayer(name="X", thickness=1.0, gamma=19.0, gamma_sat=17.0,
                      k_h=1e-4, e0=0.5, Cc=0.02, Cr=0.005, Eoed=30000, Cv=1e-2, OCR=1.0)


class TestDewateringConfig:
    def test_target_drawdown_from_mtaw(self, six_well_config):
        """target_drawdown = original_gwl_mtaw - target_drawdown_mtaw = 4.0 - 1.5 = 2.5 m."""
        assert six_well_config.target_drawdown == pytest.approx(2.5)


class TestBuilding:
    def test_corner_coordinates_no_rotation(self, building):
        """4 corners of a 10×6 building centered at (12, 0) with 0° rotation."""
        corners = building.corner_coordinates()
        assert len(corners) == 4
        # Corners should be at (7,−3), (17,−3), (17,3), (7,3)
        xs = sorted([c[0] for c in corners])
        ys = sorted([c[1] for c in corners])
        assert xs[0] == pytest.approx(7.0)
        assert xs[-1] == pytest.approx(17.0)
        assert ys[0] == pytest.approx(-3.0)
        assert ys[-1] == pytest.approx(3.0)

    def test_corner_coordinates_90deg_rotation(self):
        """90° rotation swaps length and width in coordinates."""
        b = Building(x=0, y=0, length=10, width=6, orientation_deg=90.0)
        corners = b.corner_coordinates()
        xs = sorted([c[0] for c in corners])
        ys = sorted([c[1] for c in corners])
        assert xs[0] == pytest.approx(-3.0, abs=1e-10)
        assert xs[-1] == pytest.approx(3.0, abs=1e-10)
        assert ys[0] == pytest.approx(-5.0, abs=1e-10)
        assert ys[-1] == pytest.approx(5.0, abs=1e-10)

    def test_evaluation_points_count(self, building):
        """evaluation_points returns 5 points (center + 4 corners)."""
        pts = building.evaluation_points()
        assert len(pts) == 5
        # First point should be center
        assert pts[0] == pytest.approx((12.0, 0.0))
