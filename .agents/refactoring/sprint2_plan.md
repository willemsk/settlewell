# Sprint 2 Implementation Plan: Stress Functions

## 1. Context and Goals
This sprint aims to extract physical stress calculations (Fadum, Boussinesq, 2:1 method) from the GUI module (`solara_app/state.py`) into a pure, framework-agnostic core module `src/settlewell/stress.py`. 

All functions will be pure, heavily typed, and use SI units. Test-Driven Development (TDD) will be applied.

## 2. File Modifications

### `src/settlewell/stress.py` (New File)
Create a new module to hold all stress-related calculations.

#### Dependencies
```python
import numpy as np
from numpy.typing import NDArray
from settlewell.models import LoadGeometry, StressMethod, LoadType
```

#### Function 1: `fadum_corner_stress`
**Signature**:
```python
def fadum_corner_stress(b: float, l_dim: float, z: float) -> float:
    """
    Calculate Fadum (1948) corner stress influence value Iz for a rectangle b x l_dim at depth z.

    Parameters
    ----------
    b : float
        Width of the rectangular area [m].
    l_dim : float
        Length of the rectangular area [m].
    z : float
        Depth below the loaded area [m].

    Returns
    -------
    float
        Vertical stress influence factor Iz [-].
    """
```
**Algorithm**:
1. **Edge Case**: If `z <= 1e-6` or `b <= 1e-6` or `l_dim <= 1e-6`, return `0.25`.
2. Let $m = b / z$ and $n = l_{dim} / z$.
3. Let $m^2 = m^2$ and $n^2 = n^2$.
4. Let $v = m^2 + n^2 + 1.0$.
5. Let $v_{mn} = m^2 \cdot n^2$.
6. Calculate $\text{term1} = \left(\frac{2mn\sqrt{v}}{v + v_{mn}}\right) \cdot \left(\frac{v + 1.0}{v}\right)$.
7. Calculate $\text{arg2} = \frac{2mn\sqrt{v}}{v - v_{mn}}$.
8. If $v - v_{mn} < 0$, let $\text{arg2\_val} = \arctan(\text{arg2}) + \pi$. Otherwise, $\text{arg2\_val} = \arctan(\text{arg2})$.
9. Return $\frac{1}{4\pi} \cdot (\text{term1} + \text{arg2\_val})$.

#### Function 2: `boussinesq_strip_stress`
**Signature**:
```python
def boussinesq_strip_stress(q: float, B: float, x_rel: float, z: float) -> float:
    """
    Calculate vertical stress increment under a Boussinesq strip load.

    Parameters
    ----------
    q : float
        Applied uniform stress [kPa].
    B : float
        Width of the strip load [m].
    x_rel : float
        Horizontal distance from the center of the strip [m].
    z : float
        Depth below the load [m].

    Returns
    -------
    float
        Vertical stress increment [kPa].
    """
```
**Algorithm**:
1. **Edge Case**: If `z <= 1e-6`: if `abs(x_rel) <= B / 2.0`, return `q`, else return `0.0`.
2. Calculate left and right coordinates relative to center: $x_L = x_{rel} - B / 2.0$ and $x_R = x_{rel} + B / 2.0$.
3. Calculate angles: $\alpha = \arctan(x_R / z) - \arctan(x_L / z)$. Use `np.arctan2` to be safe if preferred, though `z` is strictly positive here.
4. Return $\frac{q}{\pi} \cdot (\alpha + \sin(\alpha)\cos(\alpha))$.

#### Function 3: `compute_load_stress_increment`
**Signature**:
```python
def compute_load_stress_increment(load: LoadGeometry, x_rel: float, z: float, method: StressMethod) -> float:
    """
    Compute vertical stress increment delta_sigma_z under a specific surface load geometry.

    Parameters
    ----------
    load : LoadGeometry
        The load geometry definition.
    x_rel : float
        Horizontal distance from the load's center [m].
    z : float
        Depth below the surface [m].
    method : StressMethod
        The stress distribution method to apply.

    Returns
    -------
    float
        Vertical stress increment [kPa].
    """
```
**Algorithm**:
1. Extract inputs: `q = max(0.0, load.stress_q)`, `B = max(0.1, load.width_B)`.
2. Effective depth: `depth = max(0.01, z + load.z_surface_offset)`.
3. If `method == StressMethod.TWO_TO_ONE`:
    - For `LoadType.STRIP`: if `abs(x_rel) <= (B + depth) / 2.0`, return `(q * B) / (B + depth)`, else `0.0`.
    - For `LoadType.RECTANGULAR`: let `L = max(0.1, load.length_L)`. If `abs(x_rel) <= (B + depth) / 2.0` (approximate horizontal extent), return `(q * B * L) / ((B + depth) * (L + depth))`, else `0.0`.
4. If `method == StressMethod.BOUSSINESQ`:
    - For `LoadType.STRIP`: return `boussinesq_strip_stress(q, B, x_rel, depth)`.
    - For `LoadType.RECTANGULAR` (or others): 
        - Let `L = max(0.1, load.length_L)`.
        - Let `y_half = L / 2.0`.
        - If `abs(x_rel) <= B / 2.0`: (Point inside load)
            - $b_1 = B/2 - |x_{rel}|$
            - $b_2 = B/2 + |x_{rel}|$
            - $I_z = 2.0 \cdot (\text{fadum\_corner\_stress}(b_1, y_{half}, depth) + \text{fadum\_corner\_stress}(b_2, y_{half}, depth))$
        - Else: (Point outside load)
            - $b_{far} = |x_{rel}| + B/2$
            - $b_{near} = |x_{rel}| - B/2$
            - $I_z = 2.0 \cdot (\text{fadum\_corner\_stress}(b_{far}, y_{half}, depth) - \text{fadum\_corner\_stress}(b_{near}, y_{half}, depth))$
        - Return `max(0.0, q * I_z)`.
5. If `method == StressMethod.WESTERGAARD`: raise `NotImplementedError("Westergaard method not yet implemented.")`

#### Function 4: `compute_stress_profile_under_loads`
**Signature**:
```python
def compute_stress_profile_under_loads(loads: list[LoadGeometry], z_points: NDArray[np.float64], x_eval: float, method: StressMethod) -> NDArray[np.float64]:
    """
    Compute 1D vertical stress increment profile over a depth grid at a specific x coordinate.
    
    Parameters
    ----------
    loads : list[LoadGeometry]
        List of surface loads.
    z_points : NDArray[np.float64]
        Array of depths [m].
    x_eval : float
        Absolute x-coordinate for evaluation [m].
    method : StressMethod
        Stress distribution method.
        
    Returns
    -------
    NDArray[np.float64]
        Array of stress increments [kPa] corresponding to z_points.
    """
```
**Algorithm**:
1. Initialize `delta_sigma_z = np.zeros_like(z_points)`.
2. For each `load` in `loads`:
    - Calculate `x_rel = x_eval - load.x_center`.
    - For each `idx, z` in `enumerate(z_points)`:
        - `delta_sigma_z[idx] += compute_load_stress_increment(load, x_rel, z, method)`
3. Return `delta_sigma_z`.

#### Function 5: `compute_stress_heatmap`
**Signature**:
```python
def compute_stress_heatmap(loads: list[LoadGeometry], z_points: NDArray[np.float64], x_points: NDArray[np.float64], method: StressMethod) -> NDArray[np.float64]:
    """
    Compute a 2D grid of stress ratios (delta sigma / primary load q).
    
    Parameters
    ----------
    loads : list[LoadGeometry]
        List of surface loads.
    z_points : NDArray[np.float64]
        Array of depths [m] (rows).
    x_points : NDArray[np.float64]
        Array of x-coordinates [m] (columns).
    method : StressMethod
        Stress distribution method.
        
    Returns
    -------
    NDArray[np.float64]
        2D array of stress ratios. Shape: (len(z_points), len(x_points)).
    """
```
**Algorithm**:
1. Initialize `heatmap = np.zeros((len(z_points), len(x_points)))`.
2. Determine `primary_q = loads[0].stress_q if loads else 100.0`.
3. For `i, z` in `enumerate(z_points)`:
    - For `j, x` in `enumerate(x_points)`:
        - Initialize `ds_sum = 0.0`.
        - For `load` in `loads`:
            - `x_rel = x - load.x_center`
            - `ds_sum += compute_load_stress_increment(load, x_rel, z, method)`
        - `heatmap[i, j] = ds_sum / max(1.0, primary_q)`
4. Return `heatmap`.

### `src/settlewell/__init__.py`
**Changes**:
Add imports for the new module:
```python
from settlewell.stress import (
    fadum_corner_stress,
    boussinesq_strip_stress,
    compute_load_stress_increment,
    compute_stress_profile_under_loads,
    compute_stress_heatmap,
)
```
Add to `__all__` list.

### `tests/test_stress.py` (New File)
Use `pytest` for running these tests.

**Test 1: Fadum corner at surface**
- **Action**: `fadum_corner_stress(b=1.0, l_dim=1.0, z=1e-7)`
- **Assertion**: Result is exactly `0.25`

**Test 2: Fadum known value (Poulos & Davis)**
- **Setup**: $m = 1, n = 1$ which means $b = 1.0, l_{dim} = 1.0, z = 1.0$.
- **Action**: `fadum_corner_stress(1.0, 1.0, 1.0)`
- **Assertion**: Result is approx `0.1752` (tolerance `1e-4`).

**Test 3: Boussinesq strip load at center and surface**
- **Action**: `boussinesq_strip_stress(q=100.0, B=2.0, x_rel=0.0, z=1e-7)`
- **Assertion**: Result is exactly `100.0`.

**Test 4: Rectangular load symmetry**
- **Setup**: Create a rectangular `LoadGeometry` with $B=4, L=4, q=100$. Method `BOUSSINESQ`.
- **Action**: Compute increment at `x_rel = 1.5, z = 2.0` and `x_rel = -1.5, z = 2.0`.
- **Assertion**: Both results should be identical.

**Test 5: Stress decays with depth**
- **Setup**: Create a rectangular `LoadGeometry` with $B=4, L=4, q=100$. Method `BOUSSINESQ`.
- **Action**: Compute at `z = 1.0` and `z = 5.0` (with `x_rel = 0`).
- **Assertion**: Result at $z=5.0$ must be `<` result at $z=1.0$.

**Test 6: 2:1 Method sanity check**
- **Setup**: Create a rectangular `LoadGeometry` with $B=4, L=4, q=100$. Method `TWO_TO_ONE`.
- **Action**: Compute increment at `x_rel = 0.0, z = 4.0`.
- **Expected calculation**: $(100 \cdot 4 \cdot 4) / ((4+4) \cdot (4+4)) = 1600 / 64 = 25.0$ kPa.
- **Assertion**: Result is exactly `25.0`.

### `docs/api/stress.md` (New File)
**Content**:
Create an API reference document that lists all functions in `settlewell.stress` with their signatures, short descriptions, and underlying assumptions (e.g. references to Fadum 1948, Boussinesq equations). Use Markdown formatting.

## 3. Verification Commands
Run the following after implementation:
- `uv run ruff check src/settlewell/stress.py tests/test_stress.py`
- `uv run ruff format src/settlewell/stress.py tests/test_stress.py`
- `uv run pytest tests/test_stress.py -v`
