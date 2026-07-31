"""Unit tests for settlewell.numerical — 2D finite-difference solver."""

import numpy as np
import pytest

from settlewell import AquiferType, Well
from settlewell.numerical import (
    create_grid,
    solve_steady_state,
    extract_drawdown_at_points,
)


class TestCreateGrid:
    def test_dimensions(self, standard_project):
        standard_project.pit = standard_project.pit.model_copy(
            update={"length": 100.0, "width": 100.0}
        )
        standard_project.settings = standard_project.settings.model_copy(
            update={
                "hydraulics_solver": "numerical",
                "grid_dx": 5.0,
                "grid_padding": 0.0,
            }
        )
        hyd = standard_project.solve_hydraulics()
        assert hyd.X_grid.shape == (21, 21)
        assert hyd.Y_grid.shape == (21, 21)
        assert hyd.drawdown_grid.shape == (21, 21)


class TestSolveSteadyState:
    def test_boundary_dirichlet(self, standard_project):
        standard_project.pit = standard_project.pit.model_copy(
            update={"length": 200.0, "width": 200.0}
        )
        standard_project.settings = standard_project.settings.model_copy(
            update={
                "hydraulics_solver": "numerical",
                "grid_dx": 5.0,
                "grid_padding": 0.0,
            }
        )
        hyd = standard_project.solve_hydraulics()

        H0_project = standard_project.soil.total_depth - standard_project.soil.gwl_depth
        head_grid = H0_project - hyd.drawdown_grid

        H0 = standard_project.dewatering.original_gwl_mtaw
        assert np.allclose(head_grid[0, :], H0, atol=0.01)  # bottom
        assert np.allclose(head_grid[-1, :], H0, atol=0.01)  # top
        assert np.allclose(head_grid[:, 0], H0, atol=0.01)  # left
        assert np.allclose(head_grid[:, -1], H0, atol=0.01)  # right

    def test_well_is_sink(self, standard_project):
        standard_project.pit = standard_project.pit.model_copy(
            update={"length": 200.0, "width": 200.0}
        )
        standard_project.settings = standard_project.settings.model_copy(
            update={
                "hydraulics_solver": "numerical",
                "grid_dx": 2.0,
                "grid_padding": 0.0,
            }
        )
        hyd = standard_project.solve_hydraulics()

        H0_project = standard_project.soil.total_depth - standard_project.soil.gwl_depth
        head_grid = H0_project - hyd.drawdown_grid

        H0 = standard_project.dewatering.original_gwl_mtaw
        assert np.min(head_grid[1:-1, 1:-1]) < H0

    def test_mass_balance(self, standard_project):
        from settlewell.hydraulics import compute_transmissivity

        standard_project.pit = standard_project.pit.model_copy(
            update={"length": 400.0, "width": 400.0}
        )
        standard_project.dewatering = standard_project.dewatering.model_copy(
            update={
                "wells": [Well(x=0.0, y=0.0, Q=0.001)],
                "target_drawdown_mtaw": 3.0,
                "original_gwl_mtaw": 4.0,
                "pumping_duration_days": 1,
                "aquifer_type": AquiferType.CONFINED,
            }
        )
        standard_project.settings = standard_project.settings.model_copy(
            update={
                "hydraulics_solver": "numerical",
                "grid_dx": 5.0,
                "grid_padding": 0.0,
            }
        )
        hyd = standard_project.solve_hydraulics()
        T = compute_transmissivity(standard_project.soil, standard_project.dewatering)

        H0_project = standard_project.soil.total_depth - standard_project.soil.gwl_depth
        head_grid = H0_project - hyd.drawdown_grid

        flux_bottom = T * np.sum(head_grid[0, :] - head_grid[1, :])
        flux_top = T * np.sum(head_grid[-1, :] - head_grid[-2, :])
        flux_left = T * np.sum(head_grid[:, 0] - head_grid[:, 1])
        flux_right = T * np.sum(head_grid[:, -1] - head_grid[:, -2])
        total_flux = flux_bottom + flux_top + flux_left + flux_right
        total_Q = sum(w.Q for w in standard_project.dewatering.wells)
        assert total_flux == pytest.approx(
            total_Q, rel=0.15
        )  # 15% tolerance for coarse grid


class TestExtractDrawdown:
    def test_at_grid_node(self, standard_project):
        standard_project.pit = standard_project.pit.model_copy(
            update={"length": 100.0, "width": 100.0}
        )
        standard_project.settings = standard_project.settings.model_copy(
            update={
                "hydraulics_solver": "numerical",
                "grid_dx": 5.0,
                "grid_padding": 0.0,
            }
        )
        hyd = standard_project.solve_hydraulics()
        ix, iy = 5, 5
        x_val, y_val = hyd.X_grid[iy, ix], hyd.Y_grid[iy, ix]

        H0_project = standard_project.soil.total_depth - standard_project.soil.gwl_depth
        head_grid = H0_project - hyd.drawdown_grid

        H0 = standard_project.dewatering.original_gwl_mtaw
        expected_drawdown = H0 - head_grid[iy, ix]

        grid = create_grid(x_range=(-50, 50), y_range=(-50, 50), dx=5.0)
        grid = solve_steady_state(
            grid,
            standard_project.dewatering,
            standard_project.soil,
            standard_project.pit,
        )
        result = extract_drawdown_at_points(grid, [(x_val, y_val)], H0)
        assert result[0] == pytest.approx(expected_drawdown, abs=1e-6)

    def test_well_on_boundary_warning(self, standard_project):
        standard_project.pit = standard_project.pit.model_copy(
            update={"length": 200.0, "width": 200.0}
        )
        standard_project.settings = standard_project.settings.model_copy(
            update={
                "hydraulics_solver": "numerical",
                "grid_dx": 10.0,
                "grid_padding": 0.0,
            }
        )
        standard_project.dewatering = standard_project.dewatering.model_copy(
            update={"wells": [Well(x=-100.0, y=0.0, Q=0.001)]}
        )

        with pytest.warns(UserWarning, match="is located on or outside grid boundary"):
            standard_project.solve_hydraulics()


class TestProjectNumericalIntegration:
    def test_project_numerical_solve(self, standard_project):
        standard_project.settings = standard_project.settings.model_copy(
            update={"hydraulics_solver": "numerical"}
        )
        res = standard_project.solve_hydraulics()
        assert res.drawdown_grid is not None
        assert res.X_grid is not None
        assert res.Y_grid is not None
