import numpy as np
import pytest

from settlewell.models import LoadGeometry, LoadType, StressMethod
from settlewell.stress import (
    boussinesq_rectangular_stress,
    boussinesq_strip_stress,
    compute_load_stress_increment,
    compute_stress_heatmap,
    compute_stress_profile_under_loads,
    fadum_corner_stress,
)


class TestFadumCornerStress:
    def test_surface_edge_case(self):
        """Test Fadum corner stress returns 0.25 at surface and 0.0 for zero dimensions."""
        assert fadum_corner_stress(b=1.0, l_dim=1.0, z=1e-7) == pytest.approx(0.25)
        assert fadum_corner_stress(b=0.0, l_dim=1.0, z=2.0) == pytest.approx(0.0)
        assert fadum_corner_stress(b=1.0, l_dim=0.0, z=2.0) == pytest.approx(0.0)

    def test_poulos_and_davis_known_value(self):
        """Test Fadum corner stress for m=1, n=1 (b=1, l=1, z=1) matches ~0.1752."""
        iz = fadum_corner_stress(b=1.0, l_dim=1.0, z=1.0)
        assert iz == pytest.approx(0.1752, abs=1e-4)


class TestBoussinesqStripStress:
    def test_strip_load_at_surface_center(self):
        """Test Boussinesq strip stress directly under load center at surface equals q."""
        val = boussinesq_strip_stress(q=100.0, B=2.0, x_rel=0.0, z=1e-7)
        assert val == pytest.approx(100.0)

    def test_strip_load_at_surface_outside(self):
        """Test Boussinesq strip stress outside loaded area at surface equals 0.0."""
        val = boussinesq_strip_stress(q=100.0, B=2.0, x_rel=3.0, z=1e-7)
        assert val == pytest.approx(0.0)


class TestBoussinesqRectangularStress:
    def test_rectangular_stress_center_and_outside(self):
        """Test Boussinesq rectangular stress at load center and outside."""
        val_center = boussinesq_rectangular_stress(
            q=100.0, B=4.0, L=4.0, x_rel=0.0, z=2.0
        )
        val_outside = boussinesq_rectangular_stress(
            q=100.0, B=4.0, L=4.0, x_rel=5.0, z=2.0
        )
        assert val_center > val_outside
        assert val_outside > 0.0


class TestComputeLoadStressIncrement:
    def test_rectangular_load_symmetry(self):
        """Test stress increment is symmetric with respect to x_rel."""
        load = LoadGeometry(
            type=LoadType.RECTANGULAR, width_B=4.0, length_L=4.0, stress_q=100.0
        )
        val_pos = compute_load_stress_increment(
            load, x_rel=1.5, z=2.0, method=StressMethod.BOUSSINESQ
        )
        val_neg = compute_load_stress_increment(
            load, x_rel=-1.5, z=2.0, method=StressMethod.BOUSSINESQ
        )
        assert val_pos == pytest.approx(val_neg)

    def test_stress_decays_with_depth(self):
        """Test stress increment decays as depth increases."""
        load = LoadGeometry(
            type=LoadType.RECTANGULAR, width_B=4.0, length_L=4.0, stress_q=100.0
        )
        val_shallow = compute_load_stress_increment(
            load, x_rel=0.0, z=1.0, method=StressMethod.BOUSSINESQ
        )
        val_deep = compute_load_stress_increment(
            load, x_rel=0.0, z=5.0, method=StressMethod.BOUSSINESQ
        )
        assert val_deep < val_shallow

    def test_two_to_one_rectangular(self):
        """Test 2:1 method for rectangular load: q * B * L / ((B+z)*(L+z))."""
        load = LoadGeometry(
            type=LoadType.RECTANGULAR, width_B=4.0, length_L=4.0, stress_q=100.0
        )
        # B=4, L=4, z=4 -> (100 * 4 * 4) / ((4+4)*(4+4)) = 1600 / 64 = 25.0
        val = compute_load_stress_increment(
            load, x_rel=0.0, z=4.0, method=StressMethod.TWO_TO_ONE
        )
        assert val == pytest.approx(25.0)

    def test_two_to_one_strip(self):
        """Test 2:1 method for strip load: q * B / (B+z)."""
        load = LoadGeometry(type=LoadType.STRIP, width_B=4.0, stress_q=100.0)
        # B=4, z=4 -> (100 * 4) / (4+4) = 50.0
        val = compute_load_stress_increment(
            load, x_rel=0.0, z=4.0, method=StressMethod.TWO_TO_ONE
        )
        assert val == pytest.approx(50.0)

    def test_westergaard_raises_not_implemented(self):
        """Test Westergaard method raises NotImplementedError."""
        load = LoadGeometry(width_B=4.0, length_L=4.0, stress_q=100.0)
        with pytest.raises(NotImplementedError):
            compute_load_stress_increment(
                load, x_rel=0.0, z=2.0, method=StressMethod.WESTERGAARD
            )


class TestStressProfileAndHeatmap:
    def test_compute_stress_profile_under_loads(self):
        """Test 1D vertical stress profile vector output."""
        loads = [
            LoadGeometry(
                type=LoadType.RECTANGULAR, width_B=4.0, length_L=4.0, stress_q=100.0
            )
        ]
        z_points = np.array([1.0, 2.0, 5.0, 10.0])
        profile = compute_stress_profile_under_loads(
            loads, z_points, x_eval=0.0, method=StressMethod.BOUSSINESQ
        )

        assert len(profile) == 4
        assert profile[0] > profile[1] > profile[2] > profile[3]

    def test_compute_stress_heatmap(self):
        """Test 2D stress heatmap output shape and normalized values."""
        loads = [
            LoadGeometry(
                type=LoadType.RECTANGULAR, width_B=4.0, length_L=4.0, stress_q=100.0
            )
        ]
        z_points = np.linspace(0.5, 10.0, 5)
        x_points = np.linspace(-5.0, 5.0, 11)

        heatmap = compute_stress_heatmap(
            loads, z_points, x_points, method=StressMethod.BOUSSINESQ
        )

        assert heatmap.shape == (5, 11)
        # Center at shallow depth should have max stress ratio close to ~1.0
        assert np.max(heatmap) <= 1.05
        assert np.min(heatmap) >= 0.0
