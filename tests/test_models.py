"""Unit tests for settlewell.models — dataclass properties and validation."""

import pytest

from settlewell.models import (
    Building,
    ConstructionPit,
    DewateringConfig,
    SoilLayer,
    SoilProfile,
    Well,
)


class TestSoilProfile:
    """
    Groups tests verifying the logic and property methods of the `SoilProfile` dataclass,
    ensuring that geological models correctly manage depth calculations and reject impossible geometries.
    """

    def test_gwl_depth_from_mtaw(self, flemish_profile):
        """
        This test checks that the soil profile accurately converts relative groundwater elevation (mTAW)
        into an absolute depth below the surface. This conversion is used heavily in stress calculations.
        It queries the `gwl_depth` property of a standard profile with surface at 5.0 mTAW and GWL at 4.0 mTAW.
        The expected result is precisely 1.0 m.
        """
        assert flemish_profile.gwl_depth == pytest.approx(1.0)

    def test_total_depth(self, flemish_profile):
        """
        This test ensures that the `total_depth` property of a soil profile accurately sums up the
        thicknesses of all its constituent layers. It verifies basic geometry aggregation. It queries a
        multi-layer test profile. The expected result is a total depth of 10.0 meters.
        """
        assert flemish_profile.total_depth == pytest.approx(10.0)

    def test_rejects_gwl_above_surface(self):
        """
        This test validates the safety check that prevents defining a groundwater table that
        floats above the physical ground surface. It attempts to construct a `SoilProfile` where
        `gwl_mtaw` (6.0) is higher than `surface_level_mtaw` (5.0). The expected result is that
        a `ValueError` is raised upon initialization.
        """
        with pytest.raises(ValueError):
            SoilProfile(
                layers=[
                    SoilLayer("X", 1.0, 17.0, 19.0, 1e-4, 0.5, 0.02, 0.005, 30000, 1e-2)
                ],
                gwl_mtaw=6.0,  # Above surface
                surface_level_mtaw=5.0,
            )

    def test_rejects_empty_layers(self):
        """
        This test ensures that a `SoilProfile` cannot be instantiated without any soil layers,
        which would crash downstream math. It attempts to create a profile passing an empty list
        to `layers`. The expected result is that a `ValueError` is raised.
        """
        with pytest.raises(ValueError):
            SoilProfile(layers=[], gwl_mtaw=4.0, surface_level_mtaw=5.0)


class TestSoilLayerValidation:
    """
    Groups parameter validation tests for the `SoilLayer` dataclass, guaranteeing that
    geotechnical inputs adhere to strict physical boundaries (e.g., no negative weights).
    """

    @pytest.mark.parametrize(
        "field,value",
        [
            ("thickness", -1.0),
            ("thickness", 0.0),
            ("gamma", -5.0),
            ("gamma_sat", -5.0),
            ("k_h", -1e-4),
            ("Eoed", 0.0),
            ("OCR", 0.5),
        ],
    )
    def test_rejects_invalid_values(self, field, value):
        """
        This parameterized test runs through multiple fields of the `SoilLayer` dataclass (like thickness,
        gamma, k_h) ensuring that physically impossible values (like zero or negative numbers for these specific
        parameters) are caught at instantiation. It systematically overrides a valid dictionary with bad values.
        The expected result is that every invalid variation raises a `ValueError`.
        """
        kwargs = {
            "name": "X",
            "thickness": 1.0,
            "gamma": 17.0,
            "gamma_sat": 19.0,
            "k_h": 1e-4,
            "e0": 0.5,
            "Cc": 0.02,
            "Cr": 0.005,
            "Eoed": 30000,
            "Cv": 1e-2,
            "OCR": 1.0,
        }
        kwargs[field] = value
        with pytest.raises(ValueError):
            SoilLayer(**kwargs)

    def test_rejects_gamma_sat_less_than_gamma(self):
        """
        This test validates the fundamental physical rule that a soil's saturated unit weight (`gamma_sat`)
        must always be greater than or equal to its dry unit weight (`gamma`). It attempts to create a
        layer violating this rule. The expected result is a `ValueError`.
        """
        with pytest.raises(ValueError):
            SoilLayer(
                name="X",
                thickness=1.0,
                gamma=19.0,
                gamma_sat=17.0,
                k_h=1e-4,
                e0=0.5,
                Cc=0.02,
                Cr=0.005,
                Eoed=30000,
                Cv=1e-2,
                OCR=1.0,
            )


class TestDewateringConfig:
    """
    Groups tests covering the logic of the `DewateringConfig` object, which represents
    the overall pumping scenario and operational constraints.
    """

    def test_target_drawdown_from_mtaw(self, six_well_config):
        """
        This test ensures that the configuration object correctly calculates the required drawdown distance
        by subtracting the target groundwater elevation from the original elevation. It queries the
        `target_drawdown` property of a configured setup. The expected result is exactly 2.5 meters.
        """
        assert six_well_config.target_drawdown == pytest.approx(2.5)


class TestBuilding:
    """
    Groups tests verifying the geometric functions of the `Building` dataclass, ensuring
    that spatial rotations and coordinate generations are mathematically accurate.
    """

    def test_corner_coordinates_no_rotation(self, building):
        """
        This test checks that the corner coordinate calculation works correctly for an axis-aligned
        (0 degree rotation) building. It is needed to confirm the base geometry logic before testing rotations.
        It calls `corner_coordinates` on a standard 10x6 building centered at (12, 0). The expected result
        is a list of four points matching the exact bounds: X from 7 to 17, and Y from -3 to 3.
        """
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
        """
        This test verifies that rotating the building footprint correctly applies the trigonometric
        transformation matrix to its corners. It sets up a building at the origin, rotated by 90 degrees,
        and extracts its corners. The expected result is that the X bounds now represent the width and the
        Y bounds represent the length, effectively swapping them.
        """
        b = Building(x=0, y=0, length=10, width=6, orientation_deg=90.0)
        corners = b.corner_coordinates()
        xs = sorted([c[0] for c in corners])
        ys = sorted([c[1] for c in corners])
        assert xs[0] == pytest.approx(-3.0, abs=1e-10)
        assert xs[-1] == pytest.approx(3.0, abs=1e-10)
        assert ys[0] == pytest.approx(-5.0, abs=1e-10)
        assert ys[-1] == pytest.approx(5.0, abs=1e-10)

    def test_evaluation_points_count(self, building):
        """
        This test ensures that the standard damage evaluation routine extracts the correct sequence of
        critical points from the building footprint. It calls `evaluation_points()` on a default building.
        The expected result is exactly 5 points, with the very first point being the building's center coordinate.
        """
        pts = building.evaluation_points()
        assert len(pts) == 5
        # First point should be center
        assert pts[0] == pytest.approx((12.0, 0.0))


class TestModelsEdgeCases:
    """
    Groups exhaustive edge case and validation tests for all dataclasses, ensuring
    that deeply nested attributes and strict relational rules are enforced across the board.
    """

    def test_soillayer_validation_edges(self):
        """
        This test checks the finer validation rules of `SoilLayer`, specifically the relationships
        between void ratios, compression indices, and recompression indices. It deliberately inputs negative
        or logically inverted values (e.g., `Cr > Cc`). The expected result is that every specific violation
        raises a correctly formatted `ValueError`.
        """
        kwargs = {
            "name": "X",
            "thickness": 1.0,
            "gamma": 17.0,
            "gamma_sat": 19.0,
            "k_h": 1e-4,
            "e0": 0.5,
            "Cc": 0.02,
            "Cr": 0.005,
            "Eoed": 30000,
            "Cv": 1e-2,
            "OCR": 1.0,
        }

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
        """
        This test confirms that the `SoilProfile` helper methods for converting between absolute depth
        and mTAW elevations work bidirectionally and consistently. It maps a depth to mTAW and vice versa.
        The expected results are mathematically sound transformations based on the profile's surface level.
        """
        # surface is 5.0 mTAW
        assert flemish_profile.mtaw_to_depth(3.0) == pytest.approx(2.0)
        assert flemish_profile.depth_to_mtaw(2.0) == pytest.approx(3.0)

    def test_well_validation_edges(self):
        """
        This test validates the safety checks on the `Well` dataclass to prevent unphysical pumping
        elements. It attempts to create wells with zero radius or inverted screen elevations (top lower than bottom).
        The expected result is that a `ValueError` is raised for each case.
        """
        # r_w <= 0
        with pytest.raises(ValueError, match="Well radius"):
            Well(x=0, y=0, Q=0.001, r_w=0.0)

        # screen_top < screen_bottom
        with pytest.raises(ValueError, match="cannot be below screen_bottom_mtaw"):
            Well(x=0, y=0, Q=0.001, screen_top_mtaw=-10.0, screen_bottom_mtaw=-5.0)

    def test_constructionpit_validation_edges(self):
        """
        This test ensures the `ConstructionPit` dataclass rejects non-physical dimensions.
        It attempts to instantiate pits with zero or negative length, width, or depth.
        The expected result is that a `ValueError` is raised for each invalid dimension.
        """
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
        """
        This test exhaustively verifies the validation logic within `DewateringConfig`, catching errors
        like targeting a drawdown above the original water table, or providing negative physical constants.
        It iterates through bad inputs. The expected result is that each bad input reliably triggers a `ValueError`.
        """
        well = Well(x=0, y=0, Q=0.001)
        # target_drawdown_mtaw > original_gwl_mtaw
        with pytest.raises(ValueError, match="cannot be above"):
            DewateringConfig(
                wells=[well],
                target_drawdown_mtaw=5.0,
                original_gwl_mtaw=4.0,
                pumping_duration_days=1,
            )

        # pumping_duration_days <= 0
        with pytest.raises(ValueError, match="pumping_duration_days must be"):
            DewateringConfig(
                wells=[well],
                target_drawdown_mtaw=2.0,
                original_gwl_mtaw=4.0,
                pumping_duration_days=0.0,
            )

        # R <= 0
        with pytest.raises(ValueError, match="Radius of influence R"):
            DewateringConfig(
                wells=[well],
                target_drawdown_mtaw=2.0,
                original_gwl_mtaw=4.0,
                pumping_duration_days=1,
                R=-1.0,
            )

        # T <= 0
        with pytest.raises(ValueError, match="Transmissivity T"):
            DewateringConfig(
                wells=[well],
                target_drawdown_mtaw=2.0,
                original_gwl_mtaw=4.0,
                pumping_duration_days=1,
                T=-1e-4,
            )

        # S <= 0
        with pytest.raises(ValueError, match="Storativity S"):
            DewateringConfig(
                wells=[well],
                target_drawdown_mtaw=2.0,
                original_gwl_mtaw=4.0,
                pumping_duration_days=1,
                S=-0.1,
            )

    def test_building_validation_edges(self):
        """
        This test checks that the `Building` dataclass refuses to accept impossible physical dimensions.
        It tries to create buildings with zero length, zero width, or negative foundation depth.
        The expected result is that `ValueError` exceptions are raised appropriately.
        """
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
        """
        This test specifically verifies that a negative coefficient of consolidation (`Cv`) is rejected
        when creating a `SoilLayer`. A negative Cv would imply time flows backwards in consolidation math.
        The expected result is a `ValueError`.
        """
        kwargs = {
            "name": "X",
            "thickness": 1.0,
            "gamma": 17.0,
            "gamma_sat": 19.0,
            "k_h": 1e-4,
            "e0": 0.5,
            "Cc": 0.02,
            "Cr": 0.005,
            "Eoed": 30000,
            "Cv": -1.0,
            "OCR": 1.0,
        }
        with pytest.raises(ValueError, match="Coefficient of consolidation Cv must be"):
            SoilLayer(**kwargs)
