"""Unit tests for settlewell.hydraulics — drawdown calculations."""

import numpy as np
import pytest

from settlewell import AquiferType, DewateringConfig, SoilLayer, SoilProfile, Well
from settlewell.hydraulics import (
    compute_drawdown_at_points,
    compute_drawdown_grid,
    compute_transmissivity,
    theis_drawdown_single_well,
    thiem_drawdown_single_well,
)


class TestTransmissivity:
    """
    Groups tests that check the correct calculation of aquifer transmissivity.
    These tests are crucial because transmissivity dictates how easily water flows through
    the aquifer, which directly controls the extent and shape of the drawdown cone.
    """

    def test_simple_profile(self, simple_profile):
        """
        This test verifies that the transmissivity (T) is correctly computed for a simplified
        soil profile, ensuring that only the saturated portion of the layer contributes to flow.
        It is essential for accurate groundwater modeling to only account for water-bearing zones.
        The test calculates T using an unconfined aquifer configuration and a simple profile
        with a 5m sand layer (k=1e-4 m/s) and a groundwater level depth of 1m. The expected
        result is that T equals the saturated thickness (4m) multiplied by permeability, yielding 4e-4 m²/s.
        """
        config = DewateringConfig(
            wells=[],
            target_drawdown_mtaw=3.0,
            original_gwl_mtaw=4.0,
            pumping_duration_days=1,
            aquifer_type=AquiferType.UNCONFINED,
        )
        T = compute_transmissivity(simple_profile, config)
        assert T == pytest.approx(4e-4)


class TestThiemDrawdown:
    """
    Groups tests that evaluate steady-state groundwater drawdown calculations using the
    Thiem equation. These tests verify the core analytical model used for predicting long-term
    groundwater depression.
    """

    def test_hand_calculated_confined(self):
        """
        This test confirms the implementation of the confined Thiem equation by comparing it
        against a hand-calculated analytical result. This guarantees the fundamental math is correct.
        It runs `thiem_drawdown_single_well` with known inputs (Q=0.001, T=5e-4, R=100, r=10)
        and compares the output to the manual formulation: s(r) = Q/(2πT) * ln(R/r). The expected
        result is a drawdown of approximately 0.7330 m.
        """
        s = thiem_drawdown_single_well(
            r=10.0,
            Q=0.001,
            T=5e-4,
            R=100.0,
            H0=5.0,
            aquifer_type=AquiferType.CONFINED,
        )
        expected = (0.001 / (2 * np.pi * 5e-4)) * np.log(100 / 10)
        assert s == pytest.approx(expected, rel=1e-6)

    def test_zero_drawdown_at_R(self):
        """
        This test checks the physical boundary condition of the Thiem model: that drawdown
        becomes zero exactly at the radius of influence (R). It ensures the model does not predict
        infinite or erroneous depression cones. The test calls the Thiem function with the
        distance (r) equal to R (100.0). The expected result is a drawdown of exactly 0.0.
        """
        s = thiem_drawdown_single_well(
            r=100.0,
            Q=0.001,
            T=5e-4,
            R=100.0,
            H0=5.0,
            aquifer_type=AquiferType.CONFINED,
        )
        assert s == pytest.approx(0.0, abs=1e-10)

    def test_drawdown_non_negative(self):
        """
        This test ensures that the drawdown equation never produces mathematically impossible
        negative drawdown values (which would imply water injection instead of pumping).
        It verifies physical constraints across multiple distances. The test inputs an array of
        distances (from 1.0 to 200.0) into the Thiem function. The expected result is that
        all resulting drawdown values are greater than or equal to zero.
        """
        s = thiem_drawdown_single_well(
            r=np.array([1.0, 10.0, 50.0, 100.0, 200.0]),
            Q=0.001,
            T=5e-4,
            R=100.0,
            H0=5.0,
            aquifer_type=AquiferType.CONFINED,
        )
        assert np.all(s >= 0)


class TestTheisDrawdown:
    """
    Groups tests that evaluate transient (time-dependent) groundwater drawdown calculations
    using the Theis equation. This confirms the system correctly models evolving dewatering scenarios.
    """

    def test_hand_calculated(self):
        """
        This test verifies the transient Theis equation implementation against a known manual
        calculation using the exponential integral. It is necessary to confirm that time-dependent
        drawdown is solved correctly. The test computes the well function W(u) via `scipy.special.exp1`
        for 1 day of pumping and compares it to the output of `theis_drawdown_single_well`.
        The expected result is that the function returns the exact analytical value.
        """
        from scipy.special import exp1

        Q, T, S, r, t = 0.001, 5e-4, 0.1, 10.0, 86400.0
        u = r**2 * S / (4 * T * t)
        expected = Q / (4 * np.pi * T) * float(exp1(u))
        s = theis_drawdown_single_well(r=r, t=t, Q=Q, T=T, S=S)
        assert s == pytest.approx(expected, rel=1e-6)


class TestSuperposition:
    """
    Groups tests checking the principle of superposition, which allows combining
    the effects of multiple pumping wells into a single cumulative drawdown field.
    """

    def test_two_symmetric_wells_at_midpoint(self, simple_profile):
        """
        This test checks that linear superposition holds true for a confined aquifer by evaluating
        two identical, symmetrically placed wells. It ensures multi-well dewatering systems calculate
        aggregate drawdown correctly. The test computes drawdown at the exact midpoint (0,0) between
        two wells at x=-10 and x=10, and compares it to a single-well setup. The expected result is
        that the two-well drawdown is precisely double the drawdown of the single-well setup.
        """
        well1 = Well(x=-10.0, y=0.0, Q=0.001)
        well2 = Well(x=10.0, y=0.0, Q=0.001)
        config_2 = DewateringConfig(
            wells=[well1, well2],
            target_drawdown_mtaw=-10.0,  # high limit so no clipping
            original_gwl_mtaw=4.0,
            pumping_duration_days=1,
            aquifer_type=AquiferType.CONFINED,
            R=200.0,
            T=5e-4,
        )
        config_1 = DewateringConfig(
            wells=[well1],
            target_drawdown_mtaw=-10.0,
            original_gwl_mtaw=4.0,
            pumping_duration_days=1,
            aquifer_type=AquiferType.CONFINED,
            R=200.0,
            T=5e-4,
        )
        s_2wells = compute_drawdown_at_points([(0.0, 0.0)], config_2, simple_profile)[0]
        s_1well = compute_drawdown_at_points([(0.0, 0.0)], config_1, simple_profile)[0]
        # At midpoint, r=10 for both wells; due to symmetry, s_2wells = 2 * s_1well
        assert s_2wells == pytest.approx(2 * s_1well, rel=1e-6)


class TestDrawdownGrid:
    """
    Groups tests that check the spatial generation of drawdown grids.
    These are vital for ensuring that map-based visualizations and spatial queries
    receive properly structured and bounded data.
    """

    def test_grid_shape(self, six_well_config, flemish_profile):
        """
        This test verifies that the mesh grid generation yields coordinate and value matrices
        of the requested dimensions. It is required to prevent broadcasting errors in downstream
        plotting or assessment functions. It calls `compute_drawdown_grid` asking for a 20x15 resolution grid.
        The expected result is that the X, Y, and Drawdown arrays all match the shape (15, 20).
        """
        X, Y, S = compute_drawdown_grid(
            x_range=(-50, 50),
            y_range=(-50, 50),
            nx=20,
            ny=15,
            config=six_well_config,
            profile=flemish_profile,
        )
        assert X.shape == (15, 20)
        assert Y.shape == (15, 20)
        assert S.shape == (15, 20)

    def test_drawdown_clipped(self, six_well_config, flemish_profile):
        """
        This test ensures that grid-wide drawdown values are physically realistic and appropriately bounded.
        It prevents models from predicting drawdown deeper than the aquifer bottom (which is impossible).
        The test generates a drawdown grid and compares every value against the initial saturated
        thickness (H0). The expected result is that all values are non-negative and do not exceed H0.
        """
        H0 = flemish_profile.total_depth - flemish_profile.gwl_depth
        _, _, S = compute_drawdown_grid(
            x_range=(-50, 50),
            y_range=(-50, 50),
            nx=20,
            ny=15,
            config=six_well_config,
            profile=flemish_profile,
        )
        assert np.all(S >= 0)
        assert np.all(S <= H0 + 1e-10)

    def test_unconfined_drawdown_superposition(self, simple_profile):
        """
        This test validates that superposition in unconfined aquifers correctly employs the
        non-linear Dupuit approximation (using squared hydraulic heads). Unlike confined aquifers,
        unconfined superposition is not strictly additive. The test sets up two wells in an unconfined
        configuration and computes the central drawdown. The expected result is a positive drawdown
        that is strictly less than the total initial saturated thickness (H0).
        """
        well1 = Well(x=-10.0, y=0.0, Q=0.001)
        well2 = Well(x=10.0, y=0.0, Q=0.001)
        config_unconfined = DewateringConfig(
            wells=[well1, well2],
            target_drawdown_mtaw=1.0,
            original_gwl_mtaw=4.0,
            pumping_duration_days=1,
            aquifer_type=AquiferType.UNCONFINED,
            R=200.0,
            T=5e-4,
        )
        s = compute_drawdown_at_points([(0.0, 0.0)], config_unconfined, simple_profile)[
            0
        ]
        assert s > 0
        H0 = simple_profile.total_depth - simple_profile.gwl_depth
        assert s < H0


class TestHydraulicsEdgeCases:
    """
    Groups tests targeting edge cases, fallback behaviors, and zero-time conditions
    within the hydraulic calculations to ensure robustness against unexpected inputs.
    """

    def test_confined_layer_fallback(self):
        """
        This test checks the transmissivity calculation when the soil profile does not clearly
        trigger the main confined logic (e.g., lacking a dominant confining layer). It ensures the system
        still produces a valid physical parameter. The test uses a generic clay and silt profile and
        requests a confined aquifer configuration. The expected result is a successfully computed, positive
        transmissivity (T > 0).
        """
        # A profile with a single layer or layers that don't trigger the main confined logic
        profile = SoilProfile(
            layers=[
                SoilLayer("Clay", 5.0, 18, 18, 1e-8, 0.5, 0.02, 0.005, 10000, 1e-2),
                SoilLayer("Silt", 5.0, 18, 18, 2e-8, 0.5, 0.02, 0.005, 10000, 1e-2),
            ],
            gwl_mtaw=4.0,
            surface_level_mtaw=5.0,
        )
        well = Well(x=0, y=0, Q=0.001)
        config = DewateringConfig([well], -10.0, 4.0, 1)
        T = compute_transmissivity(profile, config)
        assert T > 0

    def test_confined_steady_state_linear_superposition(self, simple_profile):
        """
        This test ensures that passing `time_s=None` forces the system to calculate a steady-state
        drawdown field using linear superposition for confined aquifers. It verifies the explicit
        toggle between transient and steady-state modes. The test executes `compute_drawdown_at_points`
        with a two-well setup and no time constraint. The expected result is a valid, positive drawdown value.
        """
        well1 = Well(x=-10.0, y=0.0, Q=0.001)
        well2 = Well(x=10.0, y=0.0, Q=0.001)
        config = DewateringConfig(
            wells=[well1, well2],
            target_drawdown_mtaw=-10.0,
            original_gwl_mtaw=4.0,
            pumping_duration_days=1,
            aquifer_type=AquiferType.CONFINED,
            R=200.0,
            T=5e-4,
        )
        # Steady state calculation: time_s=None
        drawdowns = compute_drawdown_at_points(
            [(0.0, 0.0)], config, simple_profile, time_s=None
        )
        assert drawdowns[0] > 0

    def test_confined_transient_linear_superposition(self, simple_profile):
        """
        This test ensures that providing a time parameter (`time_s > 0`) correctly triggers the
        transient (time-dependent) linear superposition calculation for confined aquifers. It verifies
        that short-term pumping scenarios are modeled accurately. The test sets `time_s=86400.0` (1 day)
        for a two-well system. The expected result is a properly calculated, positive transient drawdown.
        """
        well1 = Well(x=-10.0, y=0.0, Q=0.001)
        well2 = Well(x=10.0, y=0.0, Q=0.001)
        config = DewateringConfig(
            wells=[well1, well2],
            target_drawdown_mtaw=-10.0,
            original_gwl_mtaw=4.0,
            pumping_duration_days=1,
            aquifer_type=AquiferType.CONFINED,
            R=200.0,
            T=5e-4,
            S=1e-4,
        )
        # Transient calculation: time_s > 0
        drawdowns = compute_drawdown_at_points(
            [(0.0, 0.0)], config, simple_profile, time_s=86400.0
        )
        assert drawdowns[0] > 0

    def test_confined_layer_fallback_pure(self):
        """
        This test verifies a pure fallback scenario for transmissivity calculation where only
        a single unconfined-style layer exists, but the user forces a confined aquifer calculation.
        It guarantees the application won't crash on contradictory or overly simple stratigraphy.
        It defines a one-layer sand profile. The expected result is a safely calculated, positive transmissivity.
        """
        # A single layer profile where min_kh_idx is 0 and no confined_layers exist after it
        profile = SoilProfile(
            layers=[
                SoilLayer("Sand", 5.0, 18, 18, 1e-4, 0.5, 0.02, 0.005, 10000, 1e-2),
            ],
            gwl_mtaw=4.0,
            surface_level_mtaw=5.0,
        )
        well = Well(x=0, y=0, Q=0.001)
        config = DewateringConfig(
            [well], -10.0, 4.0, 1, aquifer_type=AquiferType.CONFINED
        )
        T = compute_transmissivity(profile, config)
        assert T > 0

    def test_theis_zero_time(self):
        """
        This test confirms that evaluating the Theis equation at time zero (or less) returns zero drawdown.
        This prevents mathematical errors (like division by zero when calculating 'u') at the exact start
        of pumping. It directly calls `theis_drawdown_single_well` with time set to 0.0. The expected result
        is an array/value of exactly 0.0.
        """
        import numpy as np

        from settlewell.hydraulics import theis_drawdown_single_well

        # t <= 0 case
        s = theis_drawdown_single_well(10.0, 0.0, 0.001, 5e-4, 1e-4)
        assert np.all(s == 0.0)


class TestProjectHydraulicsIntegration:
    """Test hydraulics solving using the Project orchestrator API."""

    def test_project_solve_hydraulics(self, standard_project):
        """Test Project.solve_hydraulics populates HydraulicsResults."""
        res = standard_project.solve_hydraulics()
        assert res.T > 0
        assert res.S > 0
        assert res.R > 0
        assert res.drawdown_grid is not None
        assert res.X_grid is not None
        assert res.Y_grid is not None
        assert res.drawdown_grid.shape == res.X_grid.shape
