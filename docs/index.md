# Bronbemaling

**Bronbemaling** is a Python package for calculating ground settlement (zetting) at neighboring structures caused by dewatering of construction pits.

## Overview

Dewatering (bronbemaling) lowers the groundwater table around a construction excavation, inducing effective stress changes in underlying soil layers. In compressible layers (such as clay or peat), this effective stress increase causes consolidation settlement, which may result in differential settlement and structural damage to nearby buildings.

This package provides standard Flemish/Dutch geotechnical engineering models for:
- Analytical steady-state (Thiem, Dupuit) and transient (Theis) hydraulic drawdown.
- Multi-well drawdown superposition.
- 1D Terzaghi consolidation and settlement analysis.
- Burland & Wroth / SBR building damage classification.

## Navigation

- [Getting Started](getting-started.md): Installation and quick start guide.
- [Models API Reference](api/models.md): Complete reference for input data classes.
- [Hydraulics API Reference](api/hydraulics.md): Complete reference for drawdown calculation functions.
