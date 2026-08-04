# Eurocode 7 & Flemish ANB

`settlewell` implements the application of partial safety factors for geotechnical design according to **Eurocode 7 (EN 1997-1)** and the Belgian National Annex (NBN EN 1997-1 ANB).

## Design Approaches

In geotechnical settlement calculations (Serviceability Limit State - SLS), the characteristic values of soil parameters are typically used. However, under specific design approaches (such as Design Approach 1, Combination 2), material parameters must be factored to ensure safety.

The `settlewell.eurocode` module exposes the `apply_partial_factors` function, which scales the soil profile based on the selected `DesignApproach`.

### SLS Characteristic (`DesignApproach.SLS_CHARACTERISTIC`)
Used for standard Serviceability Limit State calculations where settlement is the primary concern. No partial factors are applied to the material properties. The soil profile is returned unmodified.

### Design Approach 1, Combination 1 (`DesignApproach.EC7_DA1_M1`)
In Combination 1, partial factors are primarily applied to actions (loads) rather than ground material properties. Therefore, the soil profile's compressibility parameters are unmodified, and the characteristic values are retained.

### Design Approach 1, Combination 2 (`DesignApproach.EC7_DA1_M2`)
In Combination 2, partial factors are applied to the ground material properties (Set M2). According to the Belgian National Annex and Eurocode 7 rules for settlement parameters, a partial factor $\gamma_M = 1.25$ is typically applied to increase the assumed compressibility of the soil, yielding a more conservative (larger) settlement estimate.

The scaling rules for the soil parameters are as follows:

1. **Oedometric Modulus ($E_{oed}$):**
   The stiffness is reduced to reflect a weaker soil:
   $$ E_{oed,d} = \frac{E_{oed,k}}{1.25} $$

2. **Virgin Compression Index ($C_c$):**
   The compressibility is increased:
   $$ C_{c,d} = C_{c,k} \cdot 1.25 $$

3. **Recompression Index ($C_r$):**
   The recompressibility is increased:
   $$ C_{r,d} = C_{r,k} \cdot 1.25 $$

where subscript $k$ denotes the characteristic value and $d$ denotes the design value.

These factors are applied to each `SoilLayer` in the `SoilProfile` when calling `apply_partial_factors(profile, DesignApproach.EC7_DA1_M2)`. The modified profile is then used in standard settlement calculations to produce the required SLS design verifications.
