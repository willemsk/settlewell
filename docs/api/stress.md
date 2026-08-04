# Stress Distribution API Reference

The `settlewell.stress` module provides pure, framework-agnostic functions for calculating vertical stress distribution increments $\Delta\sigma_z$ in subsoil layers caused by surface loads (strip, rectangular, embankment, point).

## Methods Supported

- **Fadum (1948)**: Elastic corner stress influence values $I_z$ for flexible rectangular loaded areas.
- **Boussinesq (1885)**: Semi-infinite elastic half-space stress distribution for strip loads and rectangular loads (via 4-corner superposition).
- **2:1 Method**: Empirical load distribution method assuming stress spreads out at a 2 vertical to 1 horizontal slope ($1:2$ spread ratio).

::: settlewell.stress
