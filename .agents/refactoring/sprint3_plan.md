# Sprint 3 Implementation Plan: Settlement Refactoring

This document outlines the detailed implementation plan for extending the core `settlewell` settlement module. The goal is to transplant physics from the GUI layer into the core library, covering elastic settlement, secondary creep, equivalent $C_v$ for layered strata, and full consolidation curves, plus Eurocode 7 utilities.

---

## 1. File Modifications

### 1.1 `src/settlewell/eurocode.py` (New File)
Create a new file for Eurocode 7 utilities.

**Enum: `DesignApproach`**
```python
from enum import Enum
import copy
from .models import SoilProfile

class DesignApproach(Enum):
    SLS_CHARACTERISTIC = "sls_characteristic"
    EC7_DA1_M1 = "ec7_da1_m1"
    EC7_DA1_M2 = "ec7_da1_m2"
```

**Function: `apply_partial_factors()`**
```python
def apply_partial_factors(profile: SoilProfile, approach: DesignApproach) -> SoilProfile:
    """Applies Eurocode 7 partial material factors to a soil profile.
    
    Parameters
    ----------
    profile : SoilProfile
        The original soil profile.
    approach : DesignApproach
        The design approach to apply.
        
    Returns
    -------
    SoilProfile
        A new SoilProfile with scaled parameters.
    """
```
**Algorithm:**
1. If `approach` is `SLS_CHARACTERISTIC` or `EC7_DA1_M1`, return a deep copy of `profile` unmodified (or factors = 1.0).
2. If `approach` is `EC7_DA1_M2`:
   - Iterate over each layer in the copied profile.
   - Divide `Eoed` by 1.25.
   - Multiply `Cc` by 1.25.
   - Multiply `Cr` by 1.25.
3. Return the modified profile copy.


### 1.2 `src/settlewell/settlement.py`
Add four new functions to the end of the file. Do not modify existing functions.

**1. `compute_elastic_settlement()`**
```python
import numpy as np
from .models import SoilProfile

def compute_elastic_settlement(profile: SoilProfile, delta_sigma_z: np.ndarray) -> float:
    """Compute instant elastic settlement of the soil profile.
    
    Parameters
    ----------
    profile : SoilProfile
        The soil profile.
    delta_sigma_z : np.ndarray
        The stress increase at the midpoint of each layer [kPa]. Length must match profile.layers.
        
    Returns
    -------
    float
        Total elastic settlement [m].
    """
```
**Algorithm:**
1. Initialize `s_e = 0.0`
2. Loop over `profile.layers` and `delta_sigma_z` simultaneously.
3. For each layer `i`: 
   $ds_i = \frac{\Delta\sigma_{z,i} \cdot H_i}{E_{\text{oed},i}}$
   (Ensure $E_{\text{oed},i} > 0$ to avoid division by zero. If $E_{\text{oed},i} \le 0$, skip or treat as 0).
4. `s_e += ds_i`
5. Return `s_e`.


**2. `compute_secondary_creep()`**
```python
def compute_secondary_creep(s_primary: float, c_alpha_to_cc: float, t_days: float, t_p_days: float = 365.0) -> float:
    """Compute secondary compression (creep) settlement.
    
    Parameters
    ----------
    s_primary : float
        Ultimate primary consolidation settlement [m].
    c_alpha_to_cc : float
        Ratio of secondary compression index to primary compression index (C_alpha / C_c).
    t_days : float
        Elapsed time [days].
    t_p_days : float, default 365.0
        Time for completion of primary consolidation [days].
        
    Returns
    -------
    float
        Creep settlement [m].
    """
```
**Algorithm:**
1. If `t_days <= t_p_days`, return `0.0`.
2. Compute $s_{\text{creep}} = s_{\text{primary}} \cdot c_{\alpha\_to\_cc} \cdot \log_{10}\left(\frac{t_{\text{days}}}{t_p\_days}\right)$.
3. Return `max(0.0, s_creep)`.


**3. `compute_equivalent_cv()`**
```python
def compute_equivalent_cv(profile: SoilProfile) -> float:
    """Compute equivalent coefficient of consolidation (Cv_eq) for layered strata.
    
    Parameters
    ----------
    profile : SoilProfile
        The soil profile.
        
    Returns
    -------
    float
        Equivalent Cv [m^2/s].
    """
```
**Algorithm:**
1. Calculate $H_{\text{total}} = \sum H_i$. If 0, return 0.
2. Initialize `denom = 0.0`.
3. For each layer `i`, if `Cv_i > 0`, add $\frac{H_i}{\sqrt{C_{v,i}}}$ to `denom`. If `Cv_i <= 0`, substitute a small value e.g., $10^{-7}$ for $C_{v,i}$.
4. $C_{v,\text{eq}} = \frac{H_{\text{total}}^2}{\text{denom}^2}$.
5. Return $C_{v,\text{eq}}$.


**4. `compute_full_consolidation_curve()`**
```python
def compute_full_consolidation_curve(
    s_elastic: float,
    s_primary_ult: float,
    cv_eq: float,
    h_dr: float,
    times_days: np.ndarray,
    c_alpha_to_cc: float = 0.05,
    t_p_days: float = 365.0
) -> np.ndarray:
    """Compute full time-consolidation settlement curve.
    
    Parameters
    ----------
    s_elastic : float
        Instant elastic settlement [m].
    s_primary_ult : float
        Ultimate primary consolidation settlement [m].
    cv_eq : float
        Equivalent coefficient of consolidation [m^2/s].
    h_dr : float
        Drainage path length [m].
    times_days : np.ndarray
        Array of elapsed times [days].
    c_alpha_to_cc : float, default 0.05
        Creep ratio.
    t_p_days : float, default 365.0
        Time to end of primary consolidation [days].
        
    Returns
    -------
    np.ndarray
        Total settlement at each time step [m].
    """
```
**Algorithm:**
1. Convert `times_days` to seconds for $T_v$ calc.
2. Loop over `times_days`:
3. Calculate $T_v = \frac{cv\_eq \cdot t_{\text{sec}}}{h\_dr^2}$. If $h\_dr \le 0$, $U=1.0$.
4. Calculate $U = \text{compute\_degree\_of\_consolidation}(T_v)$.
5. Calculate $s_{primary} = s\_primary\_ult \cdot U$.
6. Calculate $s_{creep} = \text{compute\_secondary\_creep}(s\_primary\_ult, c\_alpha\_to\_cc, t_{\text{days}}, t_p\_days)$.
7. $s(t) = s\_elastic + s_{primary} + s_{creep}$.
8. Store and return the array of total settlement.

### 1.3 `src/settlewell/__init__.py`
Update `__init__.py` to export the new functions and modules.
```python
from .eurocode import DesignApproach, apply_partial_factors
from .settlement import (
    compute_elastic_settlement,
    compute_secondary_creep,
    compute_equivalent_cv,
    compute_full_consolidation_curve
)
```

---

## 2. Testing Plan

### 2.1 `tests/test_elastic_settlement.py` (New File)
Write tests covering the 4 new functions in `settlement.py`.

**Test 1: `test_elastic_settlement()`**
- **Setup**: Create a SoilProfile with 2 layers (H=2m, Eoed=10000 kPa; H=3m, Eoed=15000 kPa). `delta_sigma_z` = [20.0, 30.0].
- **Action**: Call `compute_elastic_settlement(profile, delta_sigma_z)`.
- **Assertion**: Expected value = $(20 * 2 / 10000) + (30 * 3 / 15000) = 0.004 + 0.006 = 0.010$ m.

**Test 2: `test_secondary_creep()`**
- **Setup**: `s_primary` = 0.1 m, `c_alpha_to_cc` = 0.05, `t_p_days` = 100.
- **Action**: Compute at `t_days` = 50 and `t_days` = 1000.
- **Assertion**: For t=50, expect 0.0. For t=1000, expect $0.1 * 0.05 * \log_{10}(1000/100) = 0.005$ m.

**Test 3: `test_equivalent_cv()`**
- **Setup**: Profile with 2 layers (H1=2m, Cv1=1e-7; H2=8m, Cv2=4e-7).
- **Action**: Call `compute_equivalent_cv(profile)`.
- **Assertion**: Total H=10. Denom = $2/\sqrt{10^{-7}} + 8/\sqrt{4 \cdot 10^{-7}} = 6324.55 + 12649.11 = 18973.66$. $Cv_{eq} = 10^2 / (18973.66)^2 \approx 2.77 \cdot 10^{-7} \text{ m}^2\text{/s}$.

**Test 4: `test_full_consolidation_curve()`**
- **Setup**: `s_elastic` = 0.01, `s_primary_ult` = 0.1, `cv_eq` = 1e-7, `h_dr` = 5.0, `times_days` = [0, 365, 3650].
- **Action**: Call `compute_full_consolidation_curve()`.
- **Assertion**: Check values at t=0 (expect 0.01) and t=3650 (expect 0.01 + U*0.1 + creep).

### 2.2 `tests/test_eurocode.py` (New File)
Write tests for Eurocode factor application.

**Test 1: `test_sls_characteristic_no_change()`**
- **Setup**: Standard `SoilProfile` with some `Eoed`, `Cc`, `Cr`.
- **Action**: `apply_partial_factors(profile, DesignApproach.SLS_CHARACTERISTIC)`.
- **Assertion**: Values are identical to original profile.

**Test 2: `test_ec7_da1_m2_scales_parameters()`**
- **Setup**: `SoilProfile` with a layer having `Eoed=10000`, `Cc=0.10`, `Cr=0.02`.
- **Action**: `apply_partial_factors(profile, DesignApproach.EC7_DA1_M2)`.
- **Assertion**: `Eoed == 10000 / 1.25 = 8000`. `Cc == 0.10 * 1.25 = 0.125`. `Cr == 0.02 * 1.25 = 0.025`.

---

## 3. Execution Commands
Run the tests using standard test commands to verify before considering the sprint complete:
```bash
uv run pytest tests/test_elastic_settlement.py
uv run pytest tests/test_eurocode.py
```
