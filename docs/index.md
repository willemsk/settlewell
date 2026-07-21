# Bronbemaling

**Bronbemaling** is a Python package for calculating ground settlement (zetting) at neighboring structures caused by dewatering of construction pits.

## Overview

Dewatering (bronbemaling) lowers the groundwater table around a construction excavation, inducing effective stress changes in underlying soil layers. In compressible layers (such as clay or peat), this effective stress increase causes consolidation settlement, which may result in differential settlement and structural damage to nearby buildings.

This package provides standard Flemish/Dutch geotechnical engineering models for:
- Analytical steady-state (Thiem, Dupuit) and transient (Theis) hydraulic drawdown.
- Multi-well drawdown superposition.
- 1D Terzaghi consolidation and settlement analysis.
- Burland & Wroth / SBR building damage classification.
- 2D finite-difference groundwater solver.
- 7 publication-quality visualizations.

## Navigation

- [Getting Started](getting-started.md): Installation and quick start guide.
- **API Reference**: Complete reference for all modules:
    - [Models](api/models.md) — Input data classes
    - [Hydraulics](api/hydraulics.md) — Drawdown calculations
    - [Settlement](api/settlement.md) — Consolidation engine
    - [Damage](api/damage.md) — Building damage classification
    - [Numerical](api/numerical.md) — Finite-difference solver
    - [Plotting](api/plotting.md) — Visualization functions
