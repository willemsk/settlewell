"""Unit tests for settlewell.models — dataclass properties and validation."""
import pytest
import math
from settlewell.models import SoilLayer, SoilProfile, Building, DewateringConfig, BuildingType, Well, ConstructionPit


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

class TestModelsEdgeCases:
    def test_soillayer_validation_edges(self):
        kwargs = dict(name="X", thickness=1.0, gamma=17.0, gamma_sat=19.0,
                      k_h=1e-4, e0=0.5, Cc=0.02, Cr=0.005, Eoed=30000, Cv=1e-2, OCR=1.0)

        # e0 < 0
        kwargs["e0"] = -0.1
        with pytest.raises(ValueError, match="Initial void ratio e0"):
            SoilLayer(**kwargs)

        # Cc < 0
        kwargs["e0"] = 0.5
        kwargs["Cc"] = -0.1
        with pytest.raises(ValueError, match="Compression index Cc"):
            SoilLayer(**kwargs)

        # Cr < 0
        kwargs["Cc"] = 0.02
        kwargs["Cr"] = -0.1
        with pytest.raises(ValueError, match="Recompression index Cr must be >= 0"):
            SoilLayer(**kwargs)

        # Cr > Cc
        kwargs["Cr"] = 0.05
        with pytest.raises(ValueError, match="cannot exceed virgin compression index"):
            SoilLayer(**kwargs)

    def test_soilprofile_mtaw_conversions(self, flemish_profile):
        # surface is 5.0 mTAW
        assert flemish_profile.mtaw_to_depth(3.0) == pytest.approx(2.0)
        assert flemish_profile.depth_to_mtaw(2.0) == pytest.approx(3.0)

    def test_well_validation_edges(self):
        # r_w <= 0
        with pytest.raises(ValueError, match="Well radius"):
            Well(x=0, y=0, Q=0.001, r_w=0.0)

        # screen_top < screen_bottom
        with pytest.raises(ValueError, match="cannot be below screen_bottom_mtaw"):
            Well(x=0, y=0, Q=0.001, screen_top_mtaw=-10.0, screen_bottom_mtaw=-5.0)

    def test_constructionpit_validation_edges(self):
        # length <= 0
        with pytest.raises(ValueError, match="length must be"):
            ConstructionPit(length=0.0, width=10.0, depth=5.0)
        # width <= 0
        with pytest.raises(ValueError, match="width must be"):
            ConstructionPit(length=10.0, width=0.0, depth=5.0)
        # depth <= 0
        with pytest.raises(ValueError, match="depth must be"):
            ConstructionPit(length=10.0, width=10.0, depth=0.0)

    def test_dewateringconfig_validation_edges(self):
        well = Well(x=0, y=0, Q=0.001)
        # target_drawdown_mtaw > original_gwl_mtaw
        with pytest.raises(ValueError, match="cannot be above"):
            DewateringConfig(wells=[well], target_drawdown_mtaw=5.0, original_gwl_mtaw=4.0, pumping_duration_days=1)

        # pumping_duration_days <= 0
        with pytest.raises(ValueError, match="pumping_duration_days must be"):
            DewateringConfig(wells=[well], target_drawdown_mtaw=2.0, original_gwl_mtaw=4.0, pumping_duration_days=0.0)

        # R <= 0
        with pytest.raises(ValueError, match="Radius of influence R"):
            DewateringConfig(wells=[well], target_drawdown_mtaw=2.0, original_gwl_mtaw=4.0, pumping_duration_days=1, R=-1.0)

        # T <= 0
        with pytest.raises(ValueError, match="Transmissivity T"):
            DewateringConfig(wells=[well], target_drawdown_mtaw=2.0, original_gwl_mtaw=4.0, pumping_duration_days=1, T=-1e-4)

        # S <= 0
        with pytest.raises(ValueError, match="Storativity S"):
            DewateringConfig(wells=[well], target_drawdown_mtaw=2.0, original_gwl_mtaw=4.0, pumping_duration_days=1, S=-0.1)

    def test_building_validation_edges(self):
        # length <= 0
        with pytest.raises(ValueError, match="Building length"):
            Building(x=0, y=0, length=0.0, width=10.0)
        # width <= 0
        with pytest.raises(ValueError, match="Building width"):
            Building(x=0, y=0, length=10.0, width=0.0)
        # foundation_depth < 0
        with pytest.raises(ValueError, match="Building foundation_depth"):
            Building(x=0, y=0, length=10.0, width=10.0, foundation_depth=-1.0)

    def test_soillayer_cv_edge(self):
        kwargs = dict(name="X", thickness=1.0, gamma=17.0, gamma_sat=19.0,
                      k_h=1e-4, e0=0.5, Cc=0.02, Cr=0.005, Eoed=30000, Cv=-1.0, OCR=1.0)
        with pytest.raises(ValueError, match="Coefficient of consolidation Cv must be"):
            SoilLayer(**kwargs)
