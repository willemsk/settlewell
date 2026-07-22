"""Unit tests for bronbemaling.hydraulics — drawdown calculations."""
import pytest
import numpy as np
from bronbemaling.hydraulics import (
    compute_transmissivity,
    thiem_drawdown_single_well,
    theis_drawdown_single_well,
    compute_drawdown_at_points,
    compute_radius_of_influence,
    compute_drawdown_grid,
)
from bronbemaling import AquiferType, DewateringConfig, Well


class TestTransmissivity:
    def test_simple_profile(self, simple_profile):
        """T for a 5m sand layer with k=1e-4 m/s → T = 5 * 1e-4 = 5e-4 m²/s
        (only the saturated portion: 5m - 1m gwl_depth = 4m saturated → T = 4e-4)."""
        config = DewateringConfig(
            wells=[], target_drawdown_mtaw=3.0, original_gwl_mtaw=4.0,
            pumping_duration_days=1, aquifer_type=AquiferType.UNCONFINED,
        )
        T = compute_transmissivity(simple_profile, config)
        assert T == pytest.approx(4e-4)


class TestThiemDrawdown:
    def test_hand_calculated_confined(self):
        """Confined Thiem: s(r) = Q/(2πT) * ln(R/r).
        Q=0.001, T=5e-4, R=100, r=10 → s = 0.001/(2π·5e-4) * ln(100/10)
        = (0.3183) * 2.3026 = 0.7330 m."""
        s = thiem_drawdown_single_well(
            r=10.0, Q=0.001, T=5e-4, R=100.0, H0=5.0,
            aquifer_type=AquiferType.CONFINED,
        )
        expected = (0.001 / (2 * np.pi * 5e-4)) * np.log(100 / 10)
        assert s == pytest.approx(expected, rel=1e-6)

    def test_zero_drawdown_at_R(self):
        """At r = R (radius of influence), drawdown should be 0."""
        s = thiem_drawdown_single_well(
            r=100.0, Q=0.001, T=5e-4, R=100.0, H0=5.0,
            aquifer_type=AquiferType.CONFINED,
        )
        assert s == pytest.approx(0.0, abs=1e-10)

    def test_drawdown_non_negative(self):
        """Drawdown is always >= 0."""
        s = thiem_drawdown_single_well(
            r=np.array([1.0, 10.0, 50.0, 100.0, 200.0]),
            Q=0.001, T=5e-4, R=100.0, H0=5.0,
            aquifer_type=AquiferType.CONFINED,
        )
        assert np.all(s >= 0)


class TestTheisDrawdown:
    def test_hand_calculated(self):
        """Theis: s = Q/(4πT) * W(u), u = r²S/(4Tt).
        Q=0.001, T=5e-4, S=0.1, r=10, t=86400 (1 day).
        u = 10² * 0.1 / (4 * 5e-4 * 86400) = 10 / 172.8 = 0.05787
        W(u) = scipy.special.exp1(u)."""
        from scipy.special import exp1
        Q, T, S, r, t = 0.001, 5e-4, 0.1, 10.0, 86400.0
        u = r**2 * S / (4 * T * t)
        expected = Q / (4 * np.pi * T) * float(exp1(u))
        s = theis_drawdown_single_well(r=r, t=t, Q=Q, T=T, S=S)
        assert s == pytest.approx(expected, rel=1e-6)


class TestSuperposition:
    def test_two_symmetric_wells_at_midpoint(self, simple_profile):
        """Drawdown at midpoint between 2 identical symmetric wells
        equals 2× the drawdown from a single well at the same distance."""
        well1 = Well(x=-10.0, y=0.0, Q=0.001)
        well2 = Well(x=10.0, y=0.0, Q=0.001)
        config_2 = DewateringConfig(
            wells=[well1, well2], target_drawdown_mtaw=-10.0,  # high limit so no clipping
            original_gwl_mtaw=4.0, pumping_duration_days=1,
            aquifer_type=AquiferType.CONFINED, R=200.0, T=5e-4,
        )
        config_1 = DewateringConfig(
            wells=[well1], target_drawdown_mtaw=-10.0,
            original_gwl_mtaw=4.0, pumping_duration_days=1,
            aquifer_type=AquiferType.CONFINED, R=200.0, T=5e-4,
        )
        s_2wells = compute_drawdown_at_points([(0.0, 0.0)], config_2, simple_profile)[0]
        s_1well = compute_drawdown_at_points([(0.0, 0.0)], config_1, simple_profile)[0]
        # At midpoint, r=10 for both wells; due to symmetry, s_2wells = 2 * s_1well
        assert s_2wells == pytest.approx(2 * s_1well, rel=1e-6)


class TestDrawdownGrid:
    def test_grid_shape(self, six_well_config, flemish_profile):
        """compute_drawdown_grid returns arrays with correct shape."""
        X, Y, S = compute_drawdown_grid(
            x_range=(-50, 50), y_range=(-50, 50), nx=20, ny=15,
            config=six_well_config, profile=flemish_profile,
        )
        assert X.shape == (15, 20)
        assert Y.shape == (15, 20)
        assert S.shape == (15, 20)

    def test_drawdown_clipped(self, six_well_config, flemish_profile):
        """All drawdown values are non-negative and bounded by saturated thickness H0."""
        H0 = flemish_profile.total_depth - flemish_profile.gwl_depth
        _, _, S = compute_drawdown_grid(
            x_range=(-50, 50), y_range=(-50, 50), nx=20, ny=15,
            config=six_well_config, profile=flemish_profile,
        )
        assert np.all(S >= 0)
        assert np.all(S <= H0 + 1e-10)

    def test_unconfined_drawdown_superposition(self, simple_profile):
        """Unconfined aquifer superposition uses Dupuit quadratic head relation."""
        well1 = Well(x=-10.0, y=0.0, Q=0.001)
        well2 = Well(x=10.0, y=0.0, Q=0.001)
        config_unconfined = DewateringConfig(
            wells=[well1, well2], target_drawdown_mtaw=1.0,
            original_gwl_mtaw=4.0, pumping_duration_days=1,
            aquifer_type=AquiferType.UNCONFINED, R=200.0, T=5e-4,
        )
        s = compute_drawdown_at_points([(0.0, 0.0)], config_unconfined, simple_profile)[0]
        assert s > 0
        H0 = simple_profile.total_depth - simple_profile.gwl_depth
        assert s < H0
