# Getting Started

## Installation

`settlewell` uses [`uv`](https://github.com/astral-sh/uv) for fast, deterministic Python package management.

### Clone and Install

```bash
git clone https://github.com/willemsk/settlewell.git
cd settlewell

# Install with all extras (web, testing, documentation)
uv sync --all-extras
```

### Running Tests

```bash
uv run pytest -v
```

### Building Documentation

```bash
uv run --extra docs mkdocs build
```

To serve documentation locally:

```bash
uv run --extra docs mkdocs serve
```

## Quick Example

```python
from settlewell import (
    SoilProfile,
    SoilLayer,
    DewateringConfig,
    Well,
    Building,
    AquiferType,
    compute_drawdown_at_points,
)

# 1. Define Soil Profile
profile = SoilProfile(
    surface_level_mtaw=5.0,
    gwl_mtaw=4.0,
    layers=[
        SoilLayer(
            name="Sand",
            thickness=2.0,
            gamma=17.5,
            gamma_sat=20.0,
            k_h=1e-4,
            e0=0.5,
            Cc=0.02,
            Cr=0.005,
            Eoed=30000,
            Cv=1e-2,
        ),
        SoilLayer(
            name="Clay",
            thickness=3.0,
            gamma=16.0,
            gamma_sat=18.5,
            k_h=1e-9,
            e0=1.0,
            Cc=0.30,
            Cr=0.06,
            Eoed=3000,
            Cv=1e-7,
            OCR=1.5,
        ),
    ],
)

# 2. Configure Dewatering System
wells = [Well(x=0.0, y=0.0, Q=0.001)]
config = DewateringConfig(
    wells=wells,
    target_drawdown_mtaw=1.5,
    original_gwl_mtaw=4.0,
    pumping_duration_days=90,
    aquifer_type=AquiferType.UNCONFINED,
)

# 3. Compute Drawdown at (x=10, y=0)
drawdown = compute_drawdown_at_points([(10.0, 0.0)], config, profile)
print(f"Drawdown at 10m distance: {drawdown[0]:.3f} m")
```
