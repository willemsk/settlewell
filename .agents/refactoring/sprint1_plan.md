# Sprint 1 Implementation Plan: Settlewell Pydantic Refactoring

## 1. Goal
Migrate all domain dataclasses in `settlewell.models` to Pydantic `BaseModel` using `ConfigDict(frozen=True)`. Merge GUI schemas into core models and introduce new classes (`LoadGeometry` and `SolverSettings`). Update all dependent tests and modules to support Pydantic.

## 2. File Modifications

### 2.1 `pyproject.toml`
Add `pydantic>=2.0` to the core `dependencies` section.

```diff
  dependencies = [
      "numpy>=1.24",
      "scipy>=1.10",
      "matplotlib>=3.7",
      "plotly>=5.15",
+     "pydantic>=2.0",
  ]
```
Note: Ensure `solara_app` requirements in `[project.optional-dependencies]` no longer strictly manage Pydantic independently since it's core now.

### 2.2 `src/settlewell/soils.py`
Remove `SoilTypeUSCS` and `FlemishSoilType` enum definitions and move them to `models.py`. 
Update the import in `soils.py`:

```python
from settlewell.models import SoilTypeUSCS, FlemishSoilType
```

### 2.3 `src/settlewell/models.py`
Completely rewrite to use Pydantic. Replace `dataclass` with `BaseModel`, implement `Field` constraints instead of `__post_init__`, and include the merged GUI fields and new enums.

```python
import math
from enum import StrEnum
from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import ClassVar

class AquiferType(StrEnum):
    CONFINED = "confined"
    UNCONFINED = "unconfined"

class BuildingType(StrEnum):
    MASONRY = "masonry"
    CONCRETE_FRAME = "concrete_frame"

# Moved from soils.py
class SoilTypeUSCS(StrEnum):
    SAND = "SAND"
    CLAY = "CLAY"
    GRAVEL = "GRAVEL"
    PEAT = "PEAT"

class FlemishSoilType(StrEnum):
    BOOMSE_KLEI = "BOOMSE_KLEI"
    IEPERSE_KLEI = "IEPERSE_KLEI"
    ALLUVIALE_KLEI = "ALLUVIALE_KLEI"
    BRABANTSE_LEEM = "BRABANTSE_LEEM"
    PLEISTOCEEN_ZAND = "PLEISTOCEEN_ZAND"
    DIESTIAAN_ZAND = "DIESTIAAN_ZAND"
    BRUSSELIAAN_ZAND = "BRUSSELIAAN_ZAND"
    MAASGRIND = "MAASGRIND"
    HOLOCEEN_VEEN = "HOLOCEEN_VEEN"
    ANTROPOGEEN = "ANTROPOGEEN"

# New Enums
class LoadType(StrEnum):
    STRIP = "STRIP"
    RECTANGULAR = "RECTANGULAR"
    EMBANKMENT = "EMBANKMENT"
    POINT = "POINT"

class StressMethod(StrEnum):
    BOUSSINESQ = "BOUSSINESQ"
    WESTERGAARD = "WESTERGAARD"
    TWO_TO_ONE = "2:1"

class DrainageType(StrEnum):
    DOUBLE = "DOUBLE"
    SINGLE = "SINGLE"

class DesignApproach(StrEnum):
    SLS_CHARACTERISTIC = "SLS_CHARACTERISTIC"
    EC7_DA1_M1 = "EC7_DA1_M1"
    EC7_DA1_M2 = "EC7_DA1_M2"

class SoilLayer(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    # GUI fields merged
    id: str | None = Field(default=None)
    color: str = Field(default="#f59e0b")
    uscs_type: SoilTypeUSCS = Field(default=SoilTypeUSCS.SAND)
    flemish_type: FlemishSoilType = Field(default=FlemishSoilType.PLEISTOCEEN_ZAND)
    
    name: str
    thickness: float = Field(gt=0.0)
    gamma: float = Field(gt=0.0)
    gamma_sat: float = Field(gt=0.0)
    k_h: float = Field(gt=0.0)
    e0: float = Field(gt=0.0)
    Cc: float = Field(ge=0.0)
    Cr: float = Field(ge=0.0)
    Eoed: float = Field(gt=0.0)
    Cv: float = Field(ge=0.0)
    OCR: float = Field(ge=1.0, default=1.0)

    @model_validator(mode="after")
    def validate_relationships(self) -> "SoilLayer":
        if self.gamma_sat < self.gamma:
            raise ValueError(f"Saturated unit weight ({self.gamma_sat}) cannot be less than dry unit weight ({self.gamma})")
        if self.Cr > self.Cc:
            raise ValueError(f"Recompression index Cr ({self.Cr}) cannot exceed virgin compression index Cc ({self.Cc})")
        return self

class SoilProfile(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    layers: list[SoilLayer] = Field(min_length=1)
    gwl_mtaw: float
    surface_level_mtaw: float

    @model_validator(mode="after")
    def validate_gwl(self) -> "SoilProfile":
        if self.gwl_mtaw > self.surface_level_mtaw:
            raise ValueError(f"Groundwater level ({self.gwl_mtaw} mTAW) cannot be above surface level ({self.surface_level_mtaw} mTAW).")
        return self

    @property
    def gwl_depth(self) -> float:
        return self.surface_level_mtaw - self.gwl_mtaw

    @property
    def total_depth(self) -> float:
        return sum(layer.thickness for layer in self.layers)

    def mtaw_to_depth(self, elevation_mtaw: float) -> float:
        return self.surface_level_mtaw - elevation_mtaw

    def depth_to_mtaw(self, depth: float) -> float:
        return self.surface_level_mtaw - depth

class Well(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    id: str | None = Field(default=None)
    name: str = Field(default="Well")
    x: float
    y: float
    Q: float
    r_w: float = Field(gt=0.0, default=0.075)
    screen_top_mtaw: float = 0.0
    screen_bottom_mtaw: float = 0.0

    @model_validator(mode="after")
    def validate_screen(self) -> "Well":
        if self.screen_top_mtaw < self.screen_bottom_mtaw:
            raise ValueError(f"Well screen_top_mtaw ({self.screen_top_mtaw}) cannot be below screen_bottom_mtaw ({self.screen_bottom_mtaw})")
        return self

class ConstructionPit(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    length: float = Field(gt=0.0)
    width: float = Field(gt=0.0)
    depth: float = Field(gt=0.0)
    center_x: float = 0.0
    center_y: float = 0.0
    bottom_mtaw: float = 0.0

class DewateringConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    wells: list[Well]
    target_drawdown_mtaw: float
    original_gwl_mtaw: float
    pumping_duration_days: float = Field(gt=0.0)
    aquifer_type: AquiferType = AquiferType.UNCONFINED
    R: float | None = Field(gt=0.0, default=None)
    T: float | None = Field(gt=0.0, default=None)
    S: float | None = Field(gt=0.0, default=None)

    @model_validator(mode="after")
    def validate_drawdown(self) -> "DewateringConfig":
        if self.target_drawdown_mtaw > self.original_gwl_mtaw:
            raise ValueError(f"target_drawdown_mtaw ({self.target_drawdown_mtaw}) cannot be above original_gwl_mtaw ({self.original_gwl_mtaw})")
        return self

    @property
    def target_drawdown(self) -> float:
        return self.original_gwl_mtaw - self.target_drawdown_mtaw

class Building(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    id: str | None = Field(default=None)
    name: str = Field(default="Building")
    x: float
    y: float
    length: float = Field(gt=0.0)
    width: float = Field(gt=0.0)
    orientation_deg: float = 0.0
    foundation_depth: float = Field(ge=0.0, default=0.6)
    building_type: BuildingType = BuildingType.MASONRY

    def corner_coordinates(self) -> list[tuple[float, float]]:
        dx = self.length / 2.0
        dy = self.width / 2.0
        rel_corners = [(-dx, -dy), (dx, -dy), (dx, dy), (-dx, dy)]
        rad = math.radians(self.orientation_deg)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        abs_corners = []
        for rx, ry in rel_corners:
            x_rot = rx * cos_a - ry * sin_a
            y_rot = rx * sin_a + ry * cos_a
            abs_corners.append((self.x + x_rot, self.y + y_rot))
        return abs_corners

    def evaluation_points(self) -> list[tuple[float, float]]:
        return [(self.x, self.y)] + self.corner_coordinates()

# New Models
class LoadGeometry(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    id: str | None = Field(default=None)
    name: str = Field(default="Footing Load")
    type: LoadType = Field(default=LoadType.RECTANGULAR)
    x_center: float = 0.0
    z_surface_offset: float = 0.0
    width_B: float = Field(gt=0.0, default=4.0)
    length_L: float = Field(gt=0.0, default=8.0)
    stress_q: float = Field(gt=0.0, default=100.0)

class SolverSettings(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    stress_method: StressMethod = Field(default=StressMethod.BOUSSINESQ)
    drainage: DrainageType = Field(default=DrainageType.DOUBLE)
    design_approach: DesignApproach = Field(default=DesignApproach.SLS_CHARACTERISTIC)
    z_max: float = Field(gt=0.0, default=20.0)
    delta_z: float = Field(gt=0.0, default=0.25)
    x_min: float = -15.0
    x_max: float = 15.0
    t_start_days: float = Field(ge=1.0, default=1.0)
    t_end_years: float = Field(gt=0.0, default=50.0)
    calculate_creep: bool = True
```

### 2.4 `src/settlewell/__init__.py`
Export new models and enums:
```python
from .models import (
    AquiferType, Building, BuildingType, ConstructionPit,
    DewateringConfig, SoilLayer, SoilProfile, Well,
    LoadGeometry, SolverSettings, SoilTypeUSCS, FlemishSoilType,
    LoadType, StressMethod, DrainageType, DesignApproach
)
```
Add new ones to `__all__`.

### 2.5 Tests Updates

#### `tests/test_models.py`
Because Pydantic raises `pydantic.ValidationError` on validation errors instead of `ValueError`, all tests catching `ValueError` must be changed. 
Change `pytest.raises(ValueError)` to `pytest.raises(pydantic.ValidationError)`.
Update test function names and changes required:

- `test_rejects_gwl_above_surface`: `with pytest.raises(pydantic.ValidationError):`
- `test_rejects_empty_layers`: `with pytest.raises(pydantic.ValidationError):`
- `test_rejects_invalid_values`: `with pytest.raises(pydantic.ValidationError):`
- `test_rejects_gamma_sat_less_than_gamma`: `with pytest.raises(pydantic.ValidationError):`
- `test_soillayer_validation_edges`: Change `match` strings if Pydantic errors are different, use `pydantic.ValidationError`.
- `test_soilprofile_validation_edges`: `pydantic.ValidationError`
- `test_well_validation_edges`: `pydantic.ValidationError`
- `test_constructionpit_validation_edges`: `pydantic.ValidationError`
- `test_dewateringconfig_validation_edges`: `pydantic.ValidationError`
- `test_building_validation_edges`: `pydantic.ValidationError`
- `test_soillayer_cv_edge`: `pydantic.ValidationError`

Add import: `import pydantic` to the top.

#### `tests/test_pydantic_models.py` (NEW FILE)
Create this file to test Pydantic-specific features:
```python
import pytest
from pydantic import ValidationError
from settlewell.models import SoilLayer, SoilProfile, LoadGeometry

def test_frozen_mutation():
    """Verify that setting fields on frozen models raises an error."""
    layer = SoilLayer(name="Test", thickness=2.0, gamma=16.0, gamma_sat=18.0, k_h=1e-4, e0=0.6, Cc=0.1, Cr=0.02, Eoed=10000, Cv=1e-2)
    with pytest.raises(ValidationError):
        layer.thickness = 3.0

def test_json_roundtrip():
    """Verify models can be serialized to and from JSON."""
    load = LoadGeometry(name="Slab", width_B=5.0, length_L=10.0, stress_q=150.0)
    data = load.model_dump_json()
    load2 = LoadGeometry.model_validate_json(data)
    assert load.name == load2.name
    assert load.stress_q == load2.stress_q

def test_model_dump():
    """Verify model dump works as expected."""
    layer = SoilLayer(name="Test", thickness=2.0, gamma=16.0, gamma_sat=18.0, k_h=1e-4, e0=0.6, Cc=0.1, Cr=0.02, Eoed=10000, Cv=1e-2)
    d = layer.model_dump()
    assert d["thickness"] == 2.0
    assert "uscs_type" in d
```

#### Other File Updates
Search for imports of `FlemishSoilType` and `SoilTypeUSCS` in `src/settlewell/solara_app/schemas.py` and change the import to point to `models.py` (which it currently does in `schemas.py`!). But `schemas.py` currently has schemas which will now be somewhat duplicated by models.py. 
However, for Sprint 1, we just need to ensure imports are satisfied and GUI schemas will be adapted.

### 2.6 Expected Breakages & How to Fix
1. **Mutation Errors**: Since `ConfigDict(frozen=True)` is used, any code dynamically updating fields like `layer.thickness = 5.0` will break. 
   **Fix**: Use `layer = layer.model_copy(update={"thickness": 5.0})` instead.
2. **Positional Arguments**: Dataclasses accepted positional args. By default, Pydantic does too if fields are typed clearly, but keyword args are safer. If a test passes `SoilLayer("Name", 1.0, 16.0...)`, it might still work but it's recommended to update to `SoilLayer(name="Name", thickness=1.0...)`.
3. **ValidationError vs ValueError**: Code that manually catches `ValueError` upon bad input instantiation will now need to catch `ValidationError`.
4. **Solara Schemas**: `schemas.py` in the GUI layer needs to be aligned to not redefine fields. The conversion helpers `to_domain_soil_layer` should be removed eventually, and GUI can use Pydantic `SoilLayer` directly.

This plan addresses all requirements and can be blindly executed by an implementing agent.
