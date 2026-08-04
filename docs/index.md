# Settlewell

**Settlewell** is a Python package for calculating ground settlement (zetting) at neighboring structures caused by dewatering of construction pits.

## Overview

Dewatering (*bronbemaling*) lowers the groundwater table around a construction excavation, inducing effective stress changes in underlying soil layers. In compressible layers (such as clay or peat), this effective stress increase causes consolidation settlement, which may result in differential settlement and structural damage to nearby buildings.

Settlewell v0.2.0 introduces a unified **`Project` orchestrator API**, **Pydantic v2 domain models**, **3D Boussinesq stress distribution engines**, **Eurocode 7 partial safety factor verification**, **Burland & Wroth building damage assessments**, and **multi-format export engines**.

## Key Features (v0.2.0)

- **`Project` Orchestrator**: High-level unified API connecting soil profiles, hydraulics, 3D stress, settlement, building damage, and report exports.
- **Pydantic v2 Domain Models**: Strongly-typed, validated data structures for soil layers, dewatering wells, construction pits, and neighboring structures.
- **3D Boussinesq Stress Distribution**: Rectangular flexible/rigid surface load calculations and excavation stress relief profiles.
- **Eurocode 7 & Flemish ANB**: Design Approach verification (DA1, DA2, DA3) and partial factor calculations conforming to NBN EN 1997-1 ANB.
- **Burland & Wroth Damage Assessment**: Structural risk classification based on calculated tensile strain, tilt, deflection ratio, and damage categories.
- **Multi-Format Exports**: Automated publication-quality PDF calculation reports, DXF CAD layout drawings, and Excel calculation workbooks.
- **Interactive Solara Web Application**: Dynamic web GUI dashboard for parameter exploration and visual analysis.

## Core Geotechnical & Hydraulic Models

- Analytical steady-state (Thiem, Dupuit) and transient (Theis) hydraulic drawdown.
- Multi-well drawdown superposition and unconfined/confined aquifer modeling.
- 1D Terzaghi consolidation, Koppejan creep, and multi-layer settlement analysis.
- 2D finite-difference groundwater solver for complex boundary conditions.
- 7 publication-quality visualization routines (matplotlib and Plotly).

## Navigation

- [Getting Started](getting-started.md): Installation and quick start guide.
- **User Guides**:
    - [Project Workflows](guides/project_workflow.md): Comprehensive guide to using the `Project` orchestrator API.
    - [Solara Web Application](guides/solara_gui.md): Interactive GUI workflow and dashboard usage.
    - [Exporting Deliverables](guides/exporting.md): Generating PDF reports, DXF drawings, and Excel workbooks.
- **Theory & Eurocode 7**:
    - [Mechanics Overview](theory/index.md): Geotechnical formulations and hydraulic equations.
    - [Eurocode 7 & Flemish ANB](theory/eurocode7.md): Partial factor verification and local standard compliance.
    - [Building Damage Risk](theory/building_damage.md): Burland & Wroth strain limits and structural damage criteria.
    - [Physics Validation](validation.md): Limiting-case numerical convergence and benchmark comparisons.
- **Case Studies**:
    - [Kauwereelstraat 31 Ghent](case_studies/kauwereelstraat.md): Dewatering assessment for an urban infill project.
    - [Bridge Abutment Settlement](case_studies/example_analysis.md): Deep excavation settlement analysis.
- **API Reference**:
    - [Overview](api/index.md): Package architecture and module organization.
    - [Project Orchestrator](api/project.md): `settlewell.Project` class reference.
    - [Export Engine](api/export.md): PDF, DXF, and Excel exporters.
    - [Domain Models](api/models.md): Input data models and parameters.
    - [Stress Distribution](api/stress.md): Boussinesq stress profile engines.
    - [Hydraulics & Drawdown](api/hydraulics.md): Analytical drawdown calculators.
    - [Settlement & Creep](api/settlement.md): Consolidation engines.
    - [Eurocode 7 Factors](api/eurocode.md): Partial safety factor calculations.
    - [Building Damage](api/damage.md): Tensile strain & damage risk calculators.
    - [Numerical Solver](api/numerical.md): Finite-difference grid solver.
    - [Plotting & Visualizations](api/plotting.md): Matplotlib and Plotly visualizers.

