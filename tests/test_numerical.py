"""Unit tests for settlewell.numerical — 2D finite-difference solver."""
import pytest
import numpy as np
from settlewell.numerical import create_grid, solve_steady_state, extract_drawdown_at_points
from settlewell import DewateringConfig, Well, AquiferType


class TestCreateGrid:
    def test_dimensions(self):
        """Grid has correct nx, ny based on range and spacing."""
        grid = create_grid(x_range=(-50, 50), y_range=(-50, 50), dx=5.0)
        assert grid.nx == 21  # (-50, -45, ..., 50) = 21 nodes
        assert grid.ny == 21
        assert grid.dx == 5.0
        assert grid.head.shape == (21, 21)


class TestSolveSteadyState:
    def test_boundary_dirichlet(self, six_well_config, flemish_profile, pit):
        """Head at boundary nodes equals H0 (undisturbed head)."""
        grid = create_grid(x_range=(-100, 100), y_range=(-100, 100), dx=5.0)
        grid = solve_steady_state(grid, six_well_config, flemish_profile, pit)
        H0 = six_well_config.original_gwl_mtaw
        # Check all 4 boundary edges
        assert np.allclose(grid.head[0, :], H0, atol=0.01)   # bottom
        assert np.allclose(grid.head[-1, :], H0, atol=0.01)  # top
        assert np.allclose(grid.head[:, 0], H0, atol=0.01)   # left
        assert np.allclose(grid.head[:, -1], H0, atol=0.01)  # right

    def test_well_is_sink(self, six_well_config, flemish_profile, pit):
        """Head at well locations is lower than surrounding nodes."""
        grid = create_grid(x_range=(-100, 100), y_range=(-100, 100), dx=2.0)
        grid = solve_steady_state(grid, six_well_config, flemish_profile, pit)
        H0 = six_well_config.original_gwl_mtaw
        # Head should be less than H0 in the interior
        assert np.min(grid.head[1:-1, 1:-1]) < H0

    def test_mass_balance(self, flemish_profile, pit):
        """Total well extraction ≈ total boundary outflow (conservation of mass).
        Sum Q_wells should equal net flux through boundaries within tolerance."""
        from settlewell.hydraulics import compute_transmissivity
        single_well_config = DewateringConfig(
            wells=[Well(x=0.0, y=0.0, Q=0.001)],
            target_drawdown_mtaw=3.0, original_gwl_mtaw=4.0,
            pumping_duration_days=1, aquifer_type=AquiferType.CONFINED,
        )
        grid = create_grid(x_range=(-200, 200), y_range=(-200, 200), dx=5.0)
        grid = solve_steady_state(grid, single_well_config, flemish_profile, pit)
        T = compute_transmissivity(flemish_profile, single_well_config)
        # Compute boundary flux: Q_boundary = T * dh/dn * ds (summed over boundary)
        dx = grid.dx
        flux_bottom = T * np.sum(grid.head[0, :] - grid.head[1, :]) / dx * dx
        flux_top = T * np.sum(grid.head[-1, :] - grid.head[-2, :]) / dx * dx
        flux_left = T * np.sum(grid.head[:, 0] - grid.head[:, 1]) / dx * dx
        flux_right = T * np.sum(grid.head[:, -1] - grid.head[:, -2]) / dx * dx
        total_flux = flux_bottom + flux_top + flux_left + flux_right
        total_Q = sum(w.Q for w in single_well_config.wells)
        assert total_flux == pytest.approx(total_Q, rel=0.15)  # 15% tolerance for coarse grid


class TestExtractDrawdown:
    def test_at_grid_node(self, six_well_config, flemish_profile, pit):
        """Drawdown extracted at a grid node matches the grid value exactly."""
        grid = create_grid(x_range=(-50, 50), y_range=(-50, 50), dx=5.0)
        grid = solve_steady_state(grid, six_well_config, flemish_profile, pit)
        H0 = six_well_config.original_gwl_mtaw
        # Pick a specific grid node
        ix, iy = 5, 5
        x_val, y_val = grid.x[ix], grid.y[iy]
        expected_drawdown = H0 - grid.head[iy, ix]
        result = extract_drawdown_at_points(grid, [(x_val, y_val)], H0)
        assert result[0] == pytest.approx(expected_drawdown, abs=1e-6)
