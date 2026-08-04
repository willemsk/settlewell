# API Overview

Welcome to the `settlewell` API Reference.

`settlewell` provides domain models, physics solvers, building damage evaluators, and reporting tools. The top-level orchestrator is the [`Project`](project.md) class, which ties together all operations over domain inputs.

## Structure

* [**Project**](project.md) - The main orchestrator.
* [**Models**](models.md) - Data models (Wells, Buildings, Soils, etc.).
* [**Hydraulics**](hydraulics.md) - Analytical groundwater models (Thiem, Theis).
* [**Numerical**](numerical.md) - 2D finite-difference steady-state solver.
* [**Stress**](stress.md) - Boussinesq stress distribution.
* [**Settlement**](settlement.md) - 1D consolidation and primary settlement calculations.
* [**Damage**](damage.md) - Building distortion and strain mapping.
* [**Eurocode**](eurocode.md) - Eurocode 7 design limits.
* [**Export**](export.md) - Result serialization and caching.
* [**Plotting**](plotting.md) - Matplotlib plotting tools.
