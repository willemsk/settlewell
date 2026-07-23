"""Unit tests for settlewell.numerical — 2D finite-difference solver."""

import pytest
import numpy as np
from settlewell.numerical import (
    create_grid,
    solve_steady_state,
    extract_drawdown_at_points,
)
from settlewell import DewateringConfig, Well, AquiferType


class TestCreateGrid:
    """
    Groups tests checking the initialization of the 2D finite-difference computational grid.
    These tests ensure that the spatial domain is correctly discretized into nodes.
    """
    def test_dimensions(self):
        """
        This test verifies that calculating grid dimensions (`nx`, `ny`) from a given coordinate range
        and cell size (`dx`) works correctly, producing the correct number of computational nodes.
        It initializes a grid from -50 to 50 with a 5.0m cell size. The expected result is a grid of
        exactly 21x21 nodes, including both edges.
        """
        grid = create_grid(x_range=(-50, 50), y_range=(-50, 50), dx=5.0)
        assert grid.nx == 21  # (-50, -45, ..., 50) = 21 nodes
        assert grid.ny == 21
        assert grid.dx == 5.0
        assert grid.head.shape == (21, 21)


class TestSolveSteadyState:
    """
    Groups tests validating the core finite-difference solver. These tests ensure the numerical
    engine converges correctly and obeys physical boundary and mass balance conditions.
    """
    def test_boundary_dirichlet(self, six_well_config, flemish_profile, pit):
        """
        This test confirms that Dirichlet boundary conditions are properly enforced at the edges of the grid.
        This means the edges of the model remain at the original undisturbed groundwater level (H0).
        The test runs the steady-state solver and checks the head values along all four borders.
        The expected result is that all border nodes equal the initial GWL.
        """
        grid = create_grid(x_range=(-100, 100), y_range=(-100, 100), dx=5.0)
        grid = solve_steady_state(grid, six_well_config, flemish_profile, pit)
        H0 = six_well_config.original_gwl_mtaw
        # Check all 4 boundary edges
        assert np.allclose(grid.head[0, :], H0, atol=0.01)  # bottom
        assert np.allclose(grid.head[-1, :], H0, atol=0.01)  # top
        assert np.allclose(grid.head[:, 0], H0, atol=0.01)  # left
        assert np.allclose(grid.head[:, -1], H0, atol=0.01)  # right

    def test_well_is_sink(self, six_well_config, flemish_profile, pit):
        """
        This test serves as a basic sanity check: pumping wells should act as sinks, meaning the
        groundwater head in the interior of the grid drops below the initial level. It runs the solver
        with a standard dewatering setup. The expected result is that the minimum computed head in
        the active interior grid is strictly less than the original H0.
        """
        grid = create_grid(x_range=(-100, 100), y_range=(-100, 100), dx=2.0)
        grid = solve_steady_state(grid, six_well_config, flemish_profile, pit)
        H0 = six_well_config.original_gwl_mtaw
        # Head should be less than H0 in the interior
        assert np.min(grid.head[1:-1, 1:-1]) < H0

    def test_mass_balance(self, flemish_profile, pit):
        """
        This test verifies the physical conservation of mass within the numerical model. At steady state,
        the total amount of water pumped out by the wells must closely match the amount of water flowing into
        the model through the grid boundaries. The test calculates the boundary fluxes using Darcy's law and
        compares the sum to the total well extraction rate. The expected result is that the fluxes match within
        a 15% tolerance (accounting for coarse grid discretization error).
        """
        from settlewell.hydraulics import compute_transmissivity

        single_well_config = DewateringConfig(
            wells=[Well(x=0.0, y=0.0, Q=0.001)],
            target_drawdown_mtaw=3.0,
            original_gwl_mtaw=4.0,
            pumping_duration_days=1,
            aquifer_type=AquiferType.CONFINED,
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
        assert total_flux == pytest.approx(
            total_Q, rel=0.15
        )  # 15% tolerance for coarse grid


class TestExtractDrawdown:
    """
    Groups tests that check the interpolation logic used to extract specific point values
    from the discretized finite-difference grid solution.
    """
    def test_at_grid_node(self, six_well_config, flemish_profile, pit):
        """
        This test ensures that if a requested evaluation point falls exactly on a grid node,
        the extraction function does not introduce any interpolation artifacts or errors.
        It requests drawdown at the coordinates of node (5,5). The expected result is that
        the returned value perfectly matches the calculated `H0 - head` at that grid index.
        """
        grid = create_grid(x_range=(-50, 50), y_range=(-50, 50), dx=5.0)
        grid = solve_steady_state(grid, six_well_config, flemish_profile, pit)
        H0 = six_well_config.original_gwl_mtaw
        # Pick a specific grid node
        ix, iy = 5, 5
        x_val, y_val = grid.x[ix], grid.y[iy]
        expected_drawdown = H0 - grid.head[iy, ix]
        result = extract_drawdown_at_points(grid, [(x_val, y_val)], H0)
        assert result[0] == pytest.approx(expected_drawdown, abs=1e-6)

    def test_well_on_boundary_warning(self, flemish_profile, pit):
        """
        This test verifies that the system gracefully handles and warns the user if they place
        a pumping well exactly on or outside the model boundaries, which violates the Dirichlet conditions
        and can cause the solver to break. It positions a well at `x=-100` on a grid ending at `x=-100`.
        The expected result is that a `UserWarning` is triggered during the solve step.
        """
        from settlewell.numerical import create_grid, solve_steady_state
        import warnings

        # Create well exactly on the boundary x=-100
        well = Well(x=-100.0, y=0.0, Q=0.001)
        config = DewateringConfig([well], -10.0, 4.0, 1)
        grid = create_grid(x_range=(-100, 100), y_range=(-100, 100), dx=10.0)

        with pytest.warns(UserWarning, match="is located on or outside grid boundary"):
            solve_steady_state(grid, config, flemish_profile, pit)
