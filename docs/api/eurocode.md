# Eurocode 7 API Reference

The `settlewell.eurocode` module provides utilities for applying Eurocode 7 partial material safety factors (NBN EN 1997-1) to geotechnical soil layer parameters.

## Design Approaches Supported

- **`SLS_CHARACTERISTIC`**: Serviceability Limit State verification using characteristic soil properties ($\gamma_M = 1.0$).
- **`EC7_DA1_M1`**: Design Approach 1 Combination 1 (Material factors = 1.0).
- **`EC7_DA1_M2`**: Design Approach 1 Combination 2 (Partial material factors applied: $E_{\text{oed}} / 1.25$, $C_c \times 1.25$, $C_r \times 1.25$).

::: settlewell.eurocode
