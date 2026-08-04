# Building Damage Risk

Uneven ground settlement beneath a structure induces internal stresses, potentially leading to cracking, architectural damage, or structural failure. `settlewell.damage` employs criteria from Burland & Wroth (1974) and the Dutch SBR guidelines (Stichting Bouwresearch) to assess damage risk.

## Evaluation Metrics

Buildings are modeled geometrically and evaluated at 5 key points: the four corners and the geometric center. Drawdown and subsequent settlement $s_i$ are calculated for each of these points.

### Differential Settlement ($\Delta s$)
The maximum difference in settlement across the foundation.
$$ \Delta s = \max(s_i) - \min(s_i) $$

### Angular Distortion ($\beta$)
The relative settlement between two points divided by the horizontal distance $L_{ij}$ between them. It is computed for all pairs of evaluation points to find the maximum distortion across the structure:
$$ \beta = \max \left( \frac{|s_i - s_j|}{L_{ij}} \right) $$

### Deflection Ratio ($\Delta / L$)
The ratio of the maximum deflection (relative to the average corner settlement) to the characteristic length of the building (its diagonal).
$$ \frac{\Delta}{L} = \frac{| \max(s_i) - s_{\text{corner, avg}} |}{L_{\text{diagonal}}} $$

## Damage Classification (SBR / Burland & Wroth)

Based on the maximum angular distortion $\beta$, the risk of damage is categorized into 6 classes (0 to 5). These thresholds are specifically calibrated for masonry structures, which are typically brittle and susceptible to differential settlement.

| Category | Description | Limit $\beta$ | Expected Crack Width | Risk Color |
| :--- | :--- | :--- | :--- | :--- |
| 0 | Negligible | $1/500$ | $< 0.1$ mm | Green |
| 1 | Very slight | $1/333$ | $0.1 - 1$ mm | Yellow |
| 2 | Slight | $1/250$ | $1 - 5$ mm | Orange |
| 3 | Moderate | $1/150$ | $5 - 15$ mm | Red |
| 4 | Severe | $1/75$ | $15 - 25$ mm | Dark Red |
| 5 | Very severe | $> 1/75$ | $> 25$ mm | Black |

### Structural Tolerance (`BuildingType`)
Different structures have varying capacities to tolerate angular distortion before exhibiting damage.

- **Masonry (`BuildingType.MASONRY`)**: The standard thresholds apply as shown in the table above.
- **Concrete Frame (`BuildingType.CONCRETE_FRAME`)**: Reinforced concrete frames are more flexible and can tolerate higher levels of distortion. For these structures, the assigned damage category is effectively reduced by 1 step (i.e., Category = $\max(0, \text{Category} - 1)$) for a given $\beta$.

## References
- Burland, J. B., & Wroth, C. P. (1974). Settlement of buildings and associated damage. *Conference on Settlement of Structures*, Cambridge, Pentech Press, London, 611-654.
- SBRCURnet (2014). *Richtlijn Meten en rekenen aan trillingen - Deel A: Schade aan gebouwen*.
