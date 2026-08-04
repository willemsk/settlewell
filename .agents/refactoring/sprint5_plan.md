# Sprint 5 Implementation Plan: Test Suite Migration to `Project` API

## Overview
This sprint focuses on migrating the existing `settlewell` test suite to use the new `Project`-based orchestration API. Instead of calling individual functions from `hydraulics.py`, `settlement.py`, etc., tests will construct a `Project` instance, call the appropriate `solve_*` methods, and assert on the `project.results` object.

**CRITICAL REQUIREMENT:** The numerical values and assertions MUST remain identical to the pre-migration code. We are only changing the API used to compute these values.

## 1. conftest.py

### Modification Instructions
We need to add a fixture that provides a pre-initialized `Project` instance using the existing fixtures.

**Target File:** `tests/conftest.py`

**What to add/change:**
Add the `Project` import and a new fixture.

**Exact Code (Add to end of file):**
```python
from settlewell.project import Project

@pytest.fixture
def standard_project(flemish_profile, six_well_config, pit, building) -> Project:
    """A standard project fully initialized for testing."""
    return Project(
        profile=flemish_profile,
        config=six_well_config,
        pit=pit,
        buildings=[building]
    )
```

## 2. test_hydraulics.py

### Modification Instructions
Replace standalone `compute_*` calls with `Project` methods. 
When testing drawdown points, use `project.solve_hydraulics()` and inspect `project.results.hydraulics`.

**Target File:** `tests/test_hydraulics.py`

**Representative Before/After:**

*Before:*
```python
    def test_grid_shape(self, six_well_config, flemish_profile):
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
```

*After:*
```python
    def test_grid_shape(self, standard_project):
        standard_project.solve_hydraulics(
            grid_x_range=(-50, 50),
            grid_y_range=(-50, 50),
            grid_nx=20,
            grid_ny=15
        )
        results = standard_project.results.hydraulics
        assert results.grid_x.shape == (15, 20)
        assert results.grid_y.shape == (15, 20)
        assert results.drawdown_grid.shape == (15, 20)
```

**Properties to Assert in `ProjectResults`:**
- `project.results.hydraulics.drawdown_grid` (for grid computations)
- `project.results.hydraulics.drawdown_at_points` (for discrete points)
- `project.results.hydraulics.transmissivity`

## 3. test_settlement.py

### Modification Instructions
Replace standalone settlement computations with `project.solve_settlement()`. 
Use the `Project` to retrieve initial stresses, stress increases, and total settlements.

**Target File:** `tests/test_settlement.py`

**Representative Before/After:**

*Before:*
```python
    def test_zero_drawdown_zero_settlement(self, flemish_profile):
        total, per_layer = compute_total_settlement(flemish_profile, drawdown=0.0)
        assert total == pytest.approx(0.0, abs=1e-12)
        assert all(s == pytest.approx(0.0, abs=1e-12) for s in per_layer)
```

*After:*
```python
    def test_zero_drawdown_zero_settlement(self, standard_project):
        # Force drawdown to 0.0 for this test
        for well in standard_project.config.wells:
            well.Q = 0.0
            
        standard_project.solve_hydraulics()
        standard_project.solve_settlement()
        
        results = standard_project.results.settlement
        assert results.total_settlement == pytest.approx(0.0, abs=1e-12)
        assert all(s == pytest.approx(0.0, abs=1e-12) for s in results.per_layer_settlements)
```

**Properties to Assert in `ProjectResults`:**
- `project.results.settlement.total_settlement`
- `project.results.settlement.per_layer_settlements`
- `project.results.settlement.settlement_vs_time`

## 4. test_numerical.py

### Modification Instructions
Migrate `solve_steady_state` to `project.solve_hydraulics(engine='numerical')`. 
The `Project` API will encapsulate the finite difference grid logic internally.

**Target File:** `tests/test_numerical.py`

**Representative Before/After:**

*Before:*
```python
    def test_well_is_sink(self, six_well_config, flemish_profile, pit):
        grid = create_grid(x_range=(-100, 100), y_range=(-100, 100), dx=2.0)
        grid = solve_steady_state(grid, six_well_config, flemish_profile, pit)
        H0 = six_well_config.original_gwl_mtaw
        # Head should be less than H0 in the interior
        assert np.min(grid.head[1:-1, 1:-1]) < H0
```

*After:*
```python
    def test_well_is_sink(self, standard_project):
        standard_project.solve_hydraulics(
            engine='numerical',
            grid_x_range=(-100, 100),
            grid_y_range=(-100, 100),
            grid_dx=2.0
        )
        H0 = standard_project.config.original_gwl_mtaw
        head_grid = standard_project.results.hydraulics.head_grid
        assert np.min(head_grid[1:-1, 1:-1]) < H0
```

## 5. test_damage.py

### Modification Instructions
Replace `assess_building_damage()` calls with `project.solve_damage()`. The `Project` inherently holds the buildings and the computed hydraulics.

**Target File:** `tests/test_damage.py`

**Representative Before/After:**

*Before:*
```python
    def test_differential_settlement(self, building, flemish_profile, six_well_config):
        from functools import partial
        from settlewell.hydraulics import compute_drawdown_at_points
        
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
```

*After:*
```python
    def test_differential_settlement(self, standard_project):
        standard_project.solve_hydraulics()
        standard_project.solve_damage()
        
        assessment = standard_project.results.damage.assessments[0]
        assert assessment.differential_settlement >= 0
        assert assessment.angular_distortion >= 0
        assert 0 <= assessment.damage_category <= 5
```

## 6. test_plotting.py

### Modification Instructions
Replace `plot_*` standalone function calls with the unified `project.plot_*()` methods. The `Project` methods implicitly use `project.results`.

**Target File:** `tests/test_plotting.py`

**Representative Before/After:**

*Before:*
```python
    def test_plan_view(self, flemish_profile, pit, six_well_config, building):
        X, Y, S = compute_drawdown_grid(
            (-50, 50), (-50, 50), 20, 20, six_well_config, flemish_profile
        )
        drawdown_func = partial(
            compute_drawdown_at_points, config=six_well_config, profile=flemish_profile
        )
        assessment = assess_building_damage(
            building, flemish_profile, six_well_config, drawdown_func
        )
        fig = plot_plan_view(pit, six_well_config, building, X, Y, S, assessment)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)
```

*After:*
```python
    def test_plan_view(self, standard_project):
        standard_project.solve_hydraulics(
            grid_x_range=(-50, 50),
            grid_y_range=(-50, 50),
            grid_nx=20,
            grid_ny=20
        )
        standard_project.solve_damage()
        
        fig = standard_project.plot_plan_view()
        assert isinstance(fig, plt.Figure)
        plt.close(fig)
```

## 7. test_physics_convergence.py

### Modification Instructions
Handle solver convergence loops using `Project` instantiation and updating attributes dynamically if needed.

**Target File:** `tests/test_physics_convergence.py`

**Representative Before/After:**

*Before:*
```python
        errors = []
        for dx in [4.0, 2.0, 1.0]:
            grid = create_grid(x_range=(-R_val, R_val), y_range=(-R_val, R_val), dx=dx)
            grid = solve_steady_state(grid, config, flemish_profile, pit)
            s_numerical = extract_drawdown_at_points(grid, [(r_test, 0.0)], H0)[0]
            rel_error = abs(s_numerical - s_analytical) / s_analytical
            errors.append(rel_error)
```

*After:*
```python
        from settlewell.project import Project
        
        errors = []
        for dx in [4.0, 2.0, 1.0]:
            project = Project(profile=flemish_profile, config=config, pit=pit, buildings=[])
            project.solve_hydraulics(
                engine='numerical',
                grid_x_range=(-R_val, R_val),
                grid_y_range=(-R_val, R_val),
                grid_dx=dx
            )
            s_numerical = project.results.hydraulics.drawdown_at_points([(r_test, 0.0)])[0]
            rel_error = abs(s_numerical - s_analytical) / s_analytical
            errors.append(rel_error)
```

## 8. test_remediation_physics.py

### Modification Instructions
These tests currently use `run_full_consolidation_solve` which evaluates GUI schemas. They should be rewritten to use the core `Project` engine. Map `ScenarioSchema` components to standard `models.py` instances, initialize `Project`, and solve.

**Target File:** `tests/test_remediation_physics.py`

**Representative Before/After:**

*Before:*
```python
    sc_sand = ScenarioSchema(
        id="sand",
        stratigraphy=[
            SoilLayerSchema(
                id="l1", name="Coarse Sand", thickness=10.0, k_h=1e-3, uscs_type=SoilTypeUSCS.SAND
            )
        ],
        dewatering=DewateringConfigSchema(wells=[]),
    )
    res_sand = run_hydraulics_solve(sc_sand)
    assert res_sand["R_influence_m"] > res_clay["R_influence_m"]
```

*After:*
```python
    from settlewell.project import Project
    from settlewell.models import SoilProfile, SoilLayer, DewateringConfig, AquiferType
    
    layer_sand = SoilLayer(name="Coarse Sand", thickness=10.0, gamma=18, gamma_sat=20, k_h=1e-3, e0=0.5, Cc=0.0, Cr=0.0, Eoed=10000, Cv=0.01)
    profile_sand = SoilProfile(layers=[layer_sand], gwl_mtaw=0.0, surface_level_mtaw=10.0)
    config_sand = DewateringConfig(wells=[], target_drawdown_mtaw=-5.0, original_gwl_mtaw=0.0, pumping_duration_days=10, aquifer_type=AquiferType.UNCONFINED)
    
    project_sand = Project(profile=profile_sand, config=config_sand)
    project_sand.solve_hydraulics()
    
    assert project_sand.results.hydraulics.radius_of_influence > project_clay.results.hydraulics.radius_of_influence
```

## 9. test_flemish_soils.py

### Modification Instructions
Add tests verifying the initialization logic of `Project.from_template()`.

**Target File:** `tests/test_flemish_soils.py`

**What to add/change:**
Add a new test block verifying template loading in the new API.

**Exact Code:**
```python
from settlewell.project import Project

def test_project_from_template():
    """Verify loading Flemish profile templates into a Project instance."""
    project = Project.from_template("Antwerp Boom Clay Formation")
    
    assert len(project.profile.layers) == 3
    # Assuming Boomse Klei is layer index 2 based on the template definitions
    assert "Klei" in project.profile.layers[2].name
    assert project.profile.layers[2].OCR >= 1.0
```
