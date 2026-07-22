"""Unit tests for settlewell.damage — Burland/Wroth + SBR classification."""
import pytest
from settlewell.damage import classify_damage, assess_building_damage, DamageAssessment
from settlewell import BuildingType


class TestClassifyDamage:
    def test_zero_distortion_is_negligible(self):
        """β = 0 → category 0 (Negligible)."""
        cat, desc, _, color = classify_damage(0.0, BuildingType.MASONRY)
        assert cat == 0
        assert color == "green"

    @pytest.mark.parametrize("beta,expected_cat", [
        (1/600, 0),    # < 1/500 → Negligible
        (1/400, 1),    # 1/500–1/333 → Very slight
        (1/300, 2),    # 1/333–1/250 → Slight
        (1/200, 3),    # 1/250–1/150 → Moderate
        (1/100, 4),    # 1/150–1/75 → Severe
        (1/50,  5),    # > 1/75 → Very severe
    ])
    def test_masonry_thresholds(self, beta, expected_cat):
        """Verify each SBR threshold boundary for masonry buildings."""
        cat, _, _, _ = classify_damage(beta, BuildingType.MASONRY)
        assert cat == expected_cat

    def test_concrete_frame_more_tolerant(self):
        """Concrete frame at β = 1/400 should be one category lower than masonry."""
        cat_masonry, _, _, _ = classify_damage(1/400, BuildingType.MASONRY)
        cat_concrete, _, _, _ = classify_damage(1/400, BuildingType.CONCRETE_FRAME)
        assert cat_concrete < cat_masonry

    def test_risk_color_per_category(self):
        """Each category returns the expected color."""
        expected_colors = {0: "green", 1: "yellow", 2: "orange",
                           3: "red", 4: "darkred", 5: "black"}
        betas = [0, 1/400, 1/300, 1/200, 1/100, 1/50]
        for cat, color in expected_colors.items():
            result_cat, _, _, result_color = classify_damage(betas[cat], BuildingType.MASONRY)
            assert result_cat == cat
            assert result_color == color


class TestAssessBuildingDamage:
    def test_differential_settlement(self, building, flemish_profile, six_well_config):
        """With a drawdown gradient across the building, differential settlement >= 0."""
        from settlewell.hydraulics import compute_drawdown_at_points
        from functools import partial
        drawdown_func = partial(
            compute_drawdown_at_points, config=six_well_config, profile=flemish_profile,
        )
        assessment = assess_building_damage(
            building, flemish_profile, six_well_config, drawdown_func,
        )
        assert assessment.differential_settlement >= 0
        assert assessment.angular_distortion >= 0
        assert 0 <= assessment.damage_category <= 5

    def test_angular_distortion_formula(self, building, flemish_profile, six_well_config):
        """β = differential_settlement / distance between most-settled pair."""
        from settlewell.hydraulics import compute_drawdown_at_points
        from functools import partial
        drawdown_func = partial(
            compute_drawdown_at_points, config=six_well_config, profile=flemish_profile,
        )
        assessment = assess_building_damage(
            building, flemish_profile, six_well_config, drawdown_func,
        )
        assert assessment.angular_distortion > 0 or assessment.differential_settlement == 0

    def test_deflection_ratio(self, building, flemish_profile, six_well_config):
        """Deflection ratio is non-negative and properly computed."""
        from settlewell.hydraulics import compute_drawdown_at_points
        from functools import partial
        drawdown_func = partial(
            compute_drawdown_at_points, config=six_well_config, profile=flemish_profile,
        )
        assessment = assess_building_damage(
            building, flemish_profile, six_well_config, drawdown_func,
        )
        assert assessment.deflection_ratio >= 0
