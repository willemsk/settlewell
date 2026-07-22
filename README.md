# Settlewell (`settlewell`)

A Python package and interactive Jupyter notebook for calculating ground settlement (zetting) at neighboring buildings caused by the dewatering (bronbemaling) of construction pits.

## Features

- **Hydraulic Drawdown**: Confined and unconfined analytical solutions (Thiem, Dupuit, Theis) with well superposition.
- **Consolidation & Settlement**: Terzaghi 1D consolidation theory, support for Cc/Cr and Eoed models, preconsolidation pressure (OCR), time-dependent consolidation.
- **Building Damage Assessment**: Burland & Wroth (1974) and SBR damage classification based on differential settlement and angular distortion.
- **Numerical Method**: 2D finite-difference groundwater solver.
- **Visualization**: Cross-sections, plan-view contour maps, settlement troughs, time-settlement curves, effective stress profiles, 3D drawdown surfaces, and damage summary tables.

## Quick Start & Installation

Using `uv`:

```bash
# Clone the repository
git clone https://github.com/willemsk/settlewell.git
cd settlewell

# Install dependencies and sync virtual environment
uv sync --extra test --extra notebook

# Run test suite
uv run pytest
```

## Usage Example

```python
from settlewell import SoilProfile, SoilLayer, DewateringConfig, Well, Building, BuildingType, AquiferType

# Define Soil Profile
profile = SoilProfile(
    surface_level_mtaw=5.0,
    gwl_mtaw=4.0,
    layers=[
        SoilLayer("Sand", thickness=2.0, gamma=17.5, gamma_sat=20.0, k_h=1e-4, e0=0.5, Cc=0.02, Cr=0.005, Eoed=30000, Cv=1e-2),
        SoilLayer("Clay", thickness=3.0, gamma=16.0, gamma_sat=18.5, k_h=1e-9, e0=1.0, Cc=0.30, Cr=0.06, Eoed=3000, Cv=1e-7, OCR=1.5),
    ]
)
```

## License

[MIT License](LICENSE) © 2026 Kherim Willems

