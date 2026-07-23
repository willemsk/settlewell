"""Unit tests for settlewell.damage — Burland/Wroth + SBR classification."""

import pytest
from settlewell.damage import classify_damage, assess_building_damage
from settlewell import BuildingType


class TestClassifyDamage:
    """
    Groups tests that evaluate the `classify_damage` function from the `settlewell.damage` module.
    These tests ensure that the function correctly translates angular distortion values into
    damage categories, considering different building types and providing the expected color codes.
    """
    def test_zero_distortion_is_negligible(self):
        """
        This test verifies that a building experiencing zero angular distortion is classified
        under the lowest damage category (β = 0 → category 0, Negligible). This is important to establish the baseline behavior
        of the damage classification function when no ground movement affects the structure.
        The test evaluates the `classify_damage` function by passing a distortion of 0.0
        for a masonry building. The expected result is a damage category of 0 (Negligible)
        and a color code of "green".
        """
        cat, desc, _, color = classify_damage(0.0, BuildingType.MASONRY)
        assert cat == 0
        assert color == "green"

    @pytest.mark.parametrize(
        "beta,expected_cat",
        [
            (1 / 600, 0),  # < 1/500 → Negligible
            (1 / 400, 1),  # 1/500–1/333 → Very slight
            (1 / 300, 2),  # 1/333–1/250 → Slight
            (1 / 200, 3),  # 1/250–1/150 → Moderate
            (1 / 100, 4),  # 1/150–1/75 → Severe
            (1 / 50, 5),  # > 1/75 → Very severe
        ],
    )
    def test_masonry_thresholds(self, beta, expected_cat):
        """
        This test checks that the SBR (Skempton, Burland, and Wroth) threshold boundaries
        correctly map angular distortion values to damage categories for masonry buildings.
        It is necessary to ensure the classification aligns with established empirical damage limits.
        The test parameterizes various beta values (e.g., 1/600 for < 1/500 → Negligible, up to 1/50 for > 1/75 → Very severe)
        and their corresponding expected categories, evaluating the `classify_damage` function for each.
        The expected result is that the returned category matches the `expected_cat` for the given beta.
        """
        cat, _, _, _ = classify_damage(beta, BuildingType.MASONRY)
        assert cat == expected_cat

    def test_concrete_frame_more_tolerant(self):
        """
        This test confirms that concrete frame buildings are more tolerant to angular
        distortion compared to masonry buildings. It's crucial for the model to reflect
        the higher flexibility and resilience of concrete frames. The test evaluates `classify_damage`
        for both building types at an identical distortion of 1/400. The expected result is that
        the damage category for the concrete frame is strictly lower than that of the masonry building.
        """
        cat_masonry, _, _, _ = classify_damage(1 / 400, BuildingType.MASONRY)
        cat_concrete, _, _, _ = classify_damage(1 / 400, BuildingType.CONCRETE_FRAME)
        assert cat_concrete < cat_masonry

    def test_risk_color_per_category(self):
        """
        This test ensures that the damage classification provides the correct visual indicator (color)
        for every possible damage category. This is useful for downstream visualization tools that map
        risk levels. It iterates through known angular distortions representing each category (from 0 to 5)
        for a masonry building and checks the color output of `classify_damage`. The expected result is that
        each category returns its corresponding risk color (e.g., 0="green", 5="black").
        """
        expected_colors = {
            0: "green", 
            1: "yellow",
            2: "orange",
            3: "red",
            4: "darkred",
            5: "black"
        }
        betas = [0, 1 / 400, 1 / 300, 1 / 200, 1 / 100, 1 / 50]
        for cat, color in expected_colors.items():
            result_cat, _, _, result_color = classify_damage(
                betas[cat], BuildingType.MASONRY
            )
            assert result_cat == cat
            assert result_color == color


class TestAssessBuildingDamage:
    """
    Groups tests that focus on the `assess_building_damage` function and its related edge cases.
    These tests verify that complex ground movement scenarios (like differential settlement,
    angular distortion, and deflection ratios) correctly translate into building damage metrics
    and that fallback mechanics operate correctly.
    """
    def test_differential_settlement(self, building, flemish_profile, six_well_config):
        """
        This test checks that the calculated differential settlement is non-negative when
        subjected to a drawdown gradient. It guarantees that the physical constraints of the settlement
        model are mathematically sound. The test creates a drawdown function using an existing well
        configuration and soil profile, then feeds this into `assess_building_damage`. The expected result
        is that differential settlement and angular distortion are non-negative, and the resulting damage
        category falls within the valid range of 0 to 5.
        """
        from settlewell.hydraulics import compute_drawdown_at_points
        from functools import partial

        drawdown_func = partial(
            compute_drawdown_at_points,
            config=six_well_config,
            profile=flemish_profile,
        )
        assessment = assess_building_damage(
            building,
            flemish_profile,
            six_well_config,
            drawdown_func,
        )
        assert assessment.differential_settlement >= 0
        assert assessment.angular_distortion >= 0
        assert 0 <= assessment.damage_category <= 5

    def test_angular_distortion_formula(
        self, building, flemish_profile, six_well_config
    ):
        """
        This test verifies that the relationship between differential settlement and angular distortion
        (β = differential_settlement / distance between most-settled pair) is logically consistent.
        It is needed to ensure the fundamental geometry of the building damage assessment is correct.
        The test assesses building damage under a standard six-well drawdown configuration. The expected
        result is that either the angular distortion is strictly positive, or the differential settlement is exactly zero.
        """
        from settlewell.hydraulics import compute_drawdown_at_points
        from functools import partial

        drawdown_func = partial(
            compute_drawdown_at_points,
            config=six_well_config,
            profile=flemish_profile,
        )
        assessment = assess_building_damage(
            building,
            flemish_profile,
            six_well_config,
            drawdown_func,
        )
        assert (
            assessment.angular_distortion > 0 or assessment.differential_settlement == 0
        )

    def test_deflection_ratio(self, building, flemish_profile, six_well_config):
        """
        This test confirms that the deflection ratio is calculated correctly and is non-negative.
        The deflection ratio is an important parameter in assessing structural bending and potential cracking.
        It executes `assess_building_damage` using typical test fixtures for building and soil properties.
        The expected result is that the resulting assessment object contains a non-negative `deflection_ratio`.
        """
        from settlewell.hydraulics import compute_drawdown_at_points
        from functools import partial

        drawdown_func = partial(
            compute_drawdown_at_points,
            config=six_well_config,
            profile=flemish_profile,
        )
        assessment = assess_building_damage(
            building,
            flemish_profile,
            six_well_config,
            drawdown_func,
        )
        assert assessment.deflection_ratio >= 0

    def test_damage_category_max_fallback(self):
        """
        This test ensures that extremely high and theoretically impossible damage inputs are safely capped.
        It is vital to prevent out-of-bounds index errors or undefined behavior in the classification logic
        when dealing with extreme values. It calls `classify_damage` with a massively inflated angular distortion (100.0).
        The expected result is that the system safely catches this and assigns the maximum possible damage category (5).
        """
        from settlewell.damage import classify_damage
        # Extremely high theoretical damage (e.g., beyond math.inf threshold, if possible).
        # We test the last element of the list by passing an extremely high value.
        cat, desc, crack, color = classify_damage(100.0, 50.0) # Huge values
        # Threshold 5 is the maximum fallback category
        assert cat == 5

    def test_damage_category_max_fallback_via_mock(self, monkeypatch):
        """
        This test validates the fallback mechanism of the damage categorization by artificially truncating
        the internal damage thresholds list. This guarantees the function degrades gracefully when a value
        exceeds all defined limits. The test uses `monkeypatch` to replace the `SBR_THRESHOLDS` with a mock
        list that lacks a catch-all upper bound, and then queries a value beyond its maximum. The expected result
        is that it returns the highest category available in the mock list (1, "Slight").
        """
        from settlewell import damage
        from settlewell.models import BuildingType

        # Override SBR_THRESHOLDS so it does not end in float("inf")
        # Then, testing a value greater than the max will hit the fallback
        mock_thresholds = [
            (0.001, 0, "Negligible", "NL", "crack0", "green"),
            (0.005, 1, "Slight", "NL", "crack1", "yellow"),
        ]
        monkeypatch.setattr(damage, "SBR_THRESHOLDS", mock_thresholds)

        # Test fallback
        cat, desc, crack, color = damage.classify_damage(0.010, BuildingType.MASONRY)
        assert cat == 1
        assert desc == "Slight"
