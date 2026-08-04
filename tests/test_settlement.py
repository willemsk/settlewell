"""Unit tests for settlewell.settlement — Terzaghi consolidation."""

import numpy as np
import pytest

from settlewell import SoilLayer
from settlewell.settlement import (
    compute_degree_of_consolidation,
    compute_initial_stress_profile,
    compute_layer_settlement_cc_cr,
    compute_layer_settlement_eoed,
    compute_stress_increase_from_drawdown,
    compute_total_settlement,
)

GAMMA_W = 9.81


class TestInitialStressProfile:
    """
    Groups tests that verify the calculation of the initial geostatic stress profile.
    Correctly determining the existing effective stresses in the ground is the necessary
    first step before calculating any settlement caused by stress changes.
    """

    def test_increases_with_depth(self, flemish_profile):
        """
        This test checks the physical rule that effective vertical stress must strictly increase
        with depth. This prevents anomalies like negative soil unit weights. The test calculates the initial
        stress profile for a standard Flemish soil column. The expected result is that the difference
        between consecutive stress values is always positive (monotonic increase).
        """
        _z, sigma_eff, _ = compute_initial_stress_profile(flemish_profile)
        assert np.all(np.diff(sigma_eff) > 0)

    def test_correct_switch_at_gwl(self, simple_profile):
        """
        This test verifies that the stress calculation correctly switches between using dry unit weight
        (above the groundwater level) and buoyant submerged weight (below the groundwater level).
        It is vital to accurately model the buoyant force of groundwater. It computes effective stress at
        0.5m (dry) and 1.5m (submerged) in a simple sand profile with a GWL at 1.0m. The expected results
        are 8.75 kPa for the dry portion and approximately 22.595 kPa for the submerged portion.
        """
        z_pts = np.array([0.5, 1.5])
        _z, sigma_eff, _ = compute_initial_stress_profile(
            simple_profile, z_points=z_pts
        )
        assert sigma_eff[0] == pytest.approx(17.5 * 0.5, rel=0.01)
        assert sigma_eff[1] == pytest.approx(
            17.5 * 1.0 + (20.0 - GAMMA_W) * 0.5, rel=0.01
        )


class TestStressIncrease:
    """
    Groups tests that check the calculation of effective stress increases resulting specifically
    from a drop in the groundwater table (drawdown). This is the direct driver of dewatering settlement.
    """

    def test_zero_above_gwl(self, simple_profile):
        """
        This test confirms that dewatering causes absolutely zero stress increase in soils that are
        already located above the original groundwater table. It prevents the model from artificially settling
        dry soil. The test queries the stress increase at a depth of 0.5m in a profile where the GWL is at 1.0m,
        given a 2.0m drawdown. The expected result is exactly 0.0 kPa stress increase.
        """
        _z, dsigma = compute_stress_increase_from_drawdown(
            simple_profile,
            drawdown=2.0,
            z_points=np.array([0.5]),
        )
        assert dsigma[0] == pytest.approx(0.0)

    def test_full_drawdown_below_new_gwl(self, simple_profile):
        """
        This test verifies that soil layers sitting completely below the new, lowered groundwater
        table experience the maximum possible stress increase: the unit weight of water multiplied by
        the total drawdown distance. The test queries a depth of 4.0m with a new GWL at 3.0m.
        The expected result is a stress increase equal to `9.81 * 2.0 = 19.62 kPa`.
        """
        _z, dsigma = compute_stress_increase_from_drawdown(
            simple_profile,
            drawdown=2.0,
            z_points=np.array([4.0]),
        )
        assert dsigma[0] == pytest.approx(GAMMA_W * 2.0, rel=0.01)

    def test_linear_in_transition_zone(self, simple_profile):
        """
        This test ensures that for points located inside the "transition zone" (between the original
        and the new lowered water table), the stress increase is linearly proportional to how much
        the water dropped relative to that specific point. It tests a depth of 2.0m where the GWL dropped
        from 1.0m to 3.0m. The expected result is a partial stress increase of `9.81 * 1.0 = 9.81 kPa`.
        """
        _z, dsigma = compute_stress_increase_from_drawdown(
            simple_profile,
            drawdown=2.0,
            z_points=np.array([2.0]),
        )
        assert dsigma[0] == pytest.approx(GAMMA_W * 1.0, rel=0.01)


class TestLayerSettlement:
    """
    Groups tests focusing on calculating the precise vertical compression of individual
    soil layers, testing the different geotechnical empirical methods (Cc/Cr and Eoed).
    """

    def test_nc_layer_cc_cr(self, single_clay_layer):
        """
        This test verifies the correct calculation of settlement for a Normally Consolidated (NC) clay layer
        using the Compression Index (Cc) method. It ensures the logarithmic compression formula is implemented correctly.
        The test creates a 3m clay layer with OCR=1 and applies a 20 kPa stress increase over an initial 50 kPa stress.
        The expected result matches the hand-calculated value of approximately 0.0657 m.
        """
        single_clay_layer_nc = SoilLayer(
            name="Klei",
            thickness=3.0,
            gamma=16.0,
            gamma_sat=18.5,
            k_h=1e-9,
            e0=1.0,
            Cc=0.30,
            Cr=0.06,
            Eoed=3000,
            Cv=1e-7,
            OCR=1.0,
        )
        s = compute_layer_settlement_cc_cr(
            single_clay_layer_nc, sigma_v0_eff=50.0, delta_sigma_v=20.0
        )
        expected = (0.30 / 2.0) * 3.0 * np.log10(70 / 50)
        assert s == pytest.approx(expected, rel=0.01)

    def test_oc_layer_uses_cr(self, single_clay_layer):
        """
        This test ensures that for an Overconsolidated (OC) soil where the final stress does not
        exceed the preconsolidation pressure, the model correctly uses only the Recompression Index (Cr).
        This is crucial because OC soils settle much less than NC soils. The test applies a small 20 kPa
        stress increase to a soil with OCR=1.5. The expected result is a much smaller settlement (approx 0.013 m)
        calculated exclusively using Cr.
        """
        s = compute_layer_settlement_cc_cr(
            single_clay_layer, sigma_v0_eff=50.0, delta_sigma_v=20.0
        )
        expected = (0.06 / 2.0) * 3.0 * np.log10(70 / 50)
        assert s == pytest.approx(expected, rel=0.01)

    def test_transitional_splits_correctly(self, single_clay_layer):
        """
        This test confirms the complex logic required when an overconsolidated soil crosses its
        preconsolidation threshold during a stress increase. It ensures the settlement is properly split into a
        recompression phase (using Cr) and a virgin compression phase (using Cc). The test applies a large 40 kPa
        stress increase to a layer with a preconsolidation pressure of 75 kPa. The expected result is exactly equal
        to the sum of the manually calculated Cr and Cc phases.
        """
        s = compute_layer_settlement_cc_cr(
            single_clay_layer, sigma_v0_eff=50.0, delta_sigma_v=40.0
        )
        cr_part = (0.06 / 2.0) * 3.0 * np.log10(75 / 50)
        cc_part = (0.30 / 2.0) * 3.0 * np.log10(90 / 75)
        assert s == pytest.approx(cr_part + cc_part, rel=0.01)

    def test_eoed_settlement(self, single_clay_layer):
        """
        This test validates the alternative Oedometer Modulus (Eoed) method for calculating settlement,
        which uses a simpler linear elastic approximation. The test calculates settlement for a 3m clay
        layer with Eoed=3000 kPa undergoing a 20 kPa stress increase. The expected result is a linear
        compression of exactly 0.020 meters.
        """
        s = compute_layer_settlement_eoed(single_clay_layer, delta_sigma_v=20.0)
        assert s == pytest.approx(20.0 / 3000 * 3.0, rel=0.01)


class TestTotalSettlement:
    """
    Groups tests that check the aggregation of individual layer settlements into a single
    total settlement value for the entire soil profile.
    """

    def test_zero_drawdown_zero_settlement(self, standard_project):
        """
        This test performs a basic validation: if there is no drawdown applied to the profile,
        the total resulting settlement must be precisely zero. It computes total settlement on a
        standard profile with `drawdown=0.0`. The expected result is exactly 0.0 total settlement
        and 0.0 for every individual layer.
        """
        new_wells = [
            w.model_copy(update={"Q": 0.0}) for w in standard_project.dewatering.wells
        ]
        standard_project.dewatering = standard_project.dewatering.model_copy(
            update={"wells": new_wells}
        )

        hyd_res = standard_project.solve_hydraulics()
        str_res = standard_project.solve_stress()
        set_res = standard_project.solve_settlement(hyd_res, str_res)

        assert set_res.total_settlement == pytest.approx(0.0, abs=1e-12)
        assert all(
            s == pytest.approx(0.0, abs=1e-12) for s in set_res.per_layer_settlements
        )

    def test_sum_matches_total(self, standard_project):
        """
        This test verifies the accounting mechanism of the total settlement function.
        It ensures the reported total value is exactly equal to the mathematical sum of the returned list
        of individual layer settlements. The test calculates a 2.0m drawdown scenario. The expected
        result is that `total == sum(per_layer)` within floating-point tolerance.
        """
        hyd_res = standard_project.solve_hydraulics()
        str_res = standard_project.solve_stress()
        set_res = standard_project.solve_settlement(hyd_res, str_res)
        expected_total = sum(set_res.per_layer_settlements) + set_res.elastic_settlement + set_res.creep_settlement
        assert set_res.total_settlement == pytest.approx(
            expected_total, rel=1e-10
        )


class TestDegreeOfConsolidation:
    """
    Groups tests validating Terzaghi's 1D consolidation theory, which dictates how fast
    water is squeezed out of soil over time, delaying the final settlement.
    """

    def test_zero_at_t0(self):
        """
        This test confirms that at time zero (represented by time factor Tv=0), the degree of
        consolidation (U) is exactly 0. This ensures settlement starts at zero. The expected result
        is 0.0.
        """
        assert compute_degree_of_consolidation(0.0) == pytest.approx(0.0)

    def test_converges_to_one(self):
        """
        This test verifies that at extremely large times (represented by an effectively infinite time
        factor Tv=100.0), the degree of consolidation asymptotically approaches 1.0 (100% completion).
        The expected result is approximately 1.0.
        """
        assert compute_degree_of_consolidation(100.0) == pytest.approx(1.0, abs=1e-6)

    def test_known_value_at_tv_05(self):
        """
        This test checks the accuracy of the infinite series approximation used for the consolidation
        curve against a known textbook value. It evaluates `compute_degree_of_consolidation` at Tv = 0.5.
        The expected result is approximately 0.764.
        """
        U = compute_degree_of_consolidation(0.5)
        assert U == pytest.approx(0.764, abs=0.005)


class TestSettlementVsTime:
    """
    Groups tests that combine the final total settlement calculations with the time-dependent
    degree of consolidation, producing realistic settlement-over-time curves.
    """

    def test_settlement_vs_time_monotonic(self, flemish_profile):
        """
        This test ensures that generated settlement curves always grow monotonically larger as time
        progresses. Buildings do not spontaneously rebound during constant pumping. The test calculates
        settlement at various intervals up to 10 years. The expected result is that the array of settlement
        values has all positive or zero step differences.
        """
        from settlewell.settlement import compute_settlement_vs_time

        times = np.array([0, 1, 10, 30, 90, 365, 3650])
        s_t = compute_settlement_vs_time(
            flemish_profile, drawdown=1.5, times_days=times
        )
        assert s_t[0] >= 0
        assert np.all(np.diff(s_t) >= 0)

    def test_settlement_vs_time_eoed(self, flemish_profile):
        """
        This test verifies that time-dependent settlement can be successfully calculated even if the
        profile is configured to use the simpler `eoed` linear elastic method instead of the default Cc/Cr method.
        It evaluates a time array under a 1.5m drawdown. The expected result is a monotonic array of values
        that finally approaches the analytically calculated `eoed` total ultimate settlement.
        """
        from settlewell.settlement import compute_settlement_vs_time

        times = np.array([0, 10, 100, 1000])
        s_t = compute_settlement_vs_time(
            flemish_profile, drawdown=1.5, times_days=times, method="eoed"
        )
        assert s_t[0] >= 0
        assert np.all(np.diff(s_t) >= 0)
        total_eoed, _ = compute_total_settlement(
            flemish_profile, drawdown=1.5, method="eoed"
        )
        assert s_t[-1] == pytest.approx(total_eoed, rel=0.05)


class TestSettlementEdgeCases:
    """
    Groups tests ensuring stability and predictable error handling when the settlement module
    encounters unusual arguments, bad configurations, or single-drainage edge cases.
    """

    def test_default_z_eval(self, flemish_profile):
        """
        This test confirms that if a user does not explicitly provide depths (`z_eval=None`) when computing
        stress increases, the function intelligently defaults to calculating at the exact vertical midpoint of
        each soil layer. It calls `compute_stress_increase_from_drawdown` with `None`. The expected result
        is an output array of stress increases perfectly matching the number of layers in the profile.
        """
        from settlewell.settlement import compute_stress_increase_from_drawdown

        # Passing z_eval=None should trigger the default calculation (center of each layer)
        drawdown = 1.0
        delta_sigma, _final_h = compute_stress_increase_from_drawdown(
            flemish_profile, drawdown, None
        )
        assert len(delta_sigma) == len(flemish_profile.layers)

    def test_unknown_settlement_method(self, standard_project):
        """
        This test ensures that requesting an invalid or unsupported settlement calculation method
        ("unknown") explicitly raises a clear `ValueError`, preventing silent failures. It calls
        `compute_total_settlement` with the bad method string. The expected result is a caught `ValueError`.
        """
        standard_project.settings = standard_project.settings.model_copy(
            update={"settlement_method": "unknown"}
        )
        with pytest.raises(ValueError, match="Unknown settlement method 'unknown'"):
            hyd_res = standard_project.solve_hydraulics()
            str_res = standard_project.solve_stress()
            standard_project.solve_settlement(hyd_res, str_res)

    def test_single_drainage_condition(self):
        """
        This test validates that time-dependent consolidation accurately handles a "single drainage" condition,
        where water can only escape a clay layer from the top because it sits on an impermeable rock base.
        This fundamentally changes the drainage path length (Hdr). The test builds a Sand-Clay-Rock profile
        and computes time-based settlement. The expected result is a successfully computed, non-zero transient
        settlement trajectory.
        """
        import numpy as np

        from settlewell.models import SoilLayer, SoilProfile
        from settlewell.settlement import compute_settlement_vs_time

        # Profile where a clay layer is bounded by impermeable rock below (single drainage)
        profile = SoilProfile(
            layers=[
                SoilLayer(
                    "Sand", 5.0, 18, 20, 1e-4, 0.5, 0.02, 0.005, 10000, 1e-2
                ),  # Sand above
                SoilLayer(
                    "Clay", 5.0, 17, 19, 1e-8, 0.5, 0.02, 0.005, 10000, 1e-2
                ),  # Clay
                SoilLayer(
                    "Rock", 5.0, 22, 22, 1e-12, 0.5, 0.02, 0.005, 10000, 1e-2
                ),  # Rock below
            ],
            gwl_mtaw=4.0,
            surface_level_mtaw=5.0,
        )

        times_s = np.array([0, 86400, 864000])
        settlements_t = compute_settlement_vs_time(profile, 1.0, times_s)
        # Verify it calculates a result correctly for single drainage
        assert len(settlements_t) == 3
        assert settlements_t[1] > 0


class TestProjectSettlementIntegration:
    """Test settlement solving using the Project orchestrator API."""

    def test_project_solve_settlement(self, standard_project):
        """Test Project.solve_settlement populates SettlementResults."""
        hyd = standard_project.solve_hydraulics()
        str_res = standard_project.solve_stress()
        set_res = standard_project.solve_settlement(hyd, str_res)

        assert set_res.total_settlement > 0
        assert len(set_res.per_layer_settlements) == len(standard_project.soil.layers)
        assert set_res.time_settlement_curve is not None
        assert set_res.times_days is not None
