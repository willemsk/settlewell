# Theoretical Background

This page provides the theoretical background, mathematical derivations, and assumptions that underpin the algorithms used in `settlewell`.

## 1. Physical and Geometric Models

The physical domain is conceptualized as a multi-layered half-space. The `settlewell.models` module defines the data structures for geotechnical parameters, geometric configurations, and boundary conditions.

### 1.1 Soil Properties
The subsurface is discretized into horizontal layers (strata). Each `SoilLayer` is assumed to be homogeneous and isotropic in the horizontal plane (though vertical heterogeneity is handled layer-by-layer).

Key parameters defining the mechanical and hydraulic behavior include:
- Unit weights: dry ($\gamma$) and saturated ($\gamma_{sat}$), governing the total vertical stress profile.
- Hydraulic conductivity ($k_h$), determining steady-state flow behavior.
- Compressibility parameters: initial void ratio ($e_0$), virgin compression index ($C_c$), recompression index ($C_r$), and the overconsolidation ratio ($OCR$). These form the basis for 1D consolidation settlement calculations.
- Flow parameters: transmissivity ($T$) and storativity/specific yield ($S$), which can be explicitly provided or calculated from layer properties.

### 1.2 Coordinate System
Calculations in `settlewell` use a local Cartesian coordinate system for plan-view geometry $(x, y)$.

Elevations are typically defined relative to a datum, with the Belgian "mTAW" (Tweede Algemene Waterpassing) often used as the default nomenclature in the API. Internally, conversions are handled such that depth $z$ is positive downwards from the ground surface ($z=0$).

Let the ground surface elevation be $Z_{surf}$. The depth $z$ of an elevation $Z$ is simply:
$$ z = Z_{surf} - Z $$

### References
- Terzaghi, K., Peck, R. B., & Mesri, G. (1996). *Soil Mechanics in Engineering Practice* (3rd ed.). John Wiley & Sons.

## 2. Hydraulics & Drawdown Calculations

The dewatering of construction pits induces a hydraulic gradient, resulting in a drawdown of the groundwater table. The `settlewell.hydraulics` module implements standard analytical solutions for steady-state and transient groundwater flow.

### 2.1 Aquifer Parameters
- **Transmissivity ($T$)**: The capacity of the aquifer to transmit water. For an unconfined aquifer, it is evaluated iteratively based on the saturated thickness. For a confined aquifer, it is computed as $T = \sum k_{h,i} \cdot H_i$.
- **Storativity ($S$)**:
  - For unconfined aquifers, this is the specific yield ($S_y$), estimated as $S_y \approx \frac{e_0}{1+e_0}$ for the dominant sandy layer.
  - For confined aquifers, it represents the elastic storativity, $S = \sum \frac{\gamma_w H_i}{E_{oed,i}}$.

### 2.2 Empirical Radius of Influence
In steady-state conditions, an empirical outer boundary is needed. Sichardt's formula is utilized:
$$ R = 3000 \cdot s \cdot \sqrt{k_{\text{rep}}} $$
where $s$ is the target drawdown in the pit and $k_{\text{rep}} = T / H_0$.

### 2.3 Steady-State Drawdown (Thiem & Dupuit)
For a single well extracting water at rate $Q$:

**Confined Aquifer (Thiem, 1906):**
Governed by linear flow equations:
$$ s(r) = \frac{Q}{2\pi T} \ln\left(\frac{R}{r}\right) $$

**Unconfined Aquifer (Dupuit, 1863):**
The saturated thickness $h$ is reduced, leading to a non-linear parabolic drawdown curve:
$$ h^2(r) = H_0^2 - \frac{Q}{\pi K} \ln\left(\frac{R}{r}\right) $$
The drawdown is then $s(r) = H_0 - h(r)$.

### 2.4 Transient Drawdown (Theis)
For transient flow (confined conditions typically, but often used as an approximation for unconfined at later times), the Theis (1935) well function is used:
$$ s(r, t) = \frac{Q}{4\pi T} W(u), \quad u = \frac{r^2 S}{4 T t} $$
where $W(u)$ is the exponential integral $E_1(u)$.

### 2.5 Superposition Principle
For multiple wells, drawdown or head squared drops are superimposed:
- **Confined**: Linear superposition of drawdowns $s_{total} = \sum s_i$.
- **Unconfined (Steady)**: Superposition of squared head drops $H_0^2 - h_{total}^2 = \sum (H_0^2 - h_i^2)$.

### References
- Thiem, G. (1906). *Hydrologische Methoden*. Gebhardt, Leipzig.
- Dupuit, J. (1863). *Études Théoriques et Pratiques sur le mouvement des Eaux dans les canaux découverts et à travers les terrains perméables* (2nd ed.). Dunod, Paris.
- Theis, C. V. (1935). The relation between the lowering of the piezometric surface and the rate and duration of discharge of a well using ground-water storage. *Transactions, American Geophysical Union*, 16(2), 519-524. [DOI: 10.1029/TR016i002p00519](https://doi.org/10.1029/TR016i002p00519)

## 3. Settlement and Consolidation

Groundwater lowering increases the effective stress in the soil mass due to the reduction of pore water pressure, leading to compression of the soil skeleton and resulting surface settlements. The `settlewell.settlement` module implements 1D consolidation theory.

### 3.1 Initial State and Stress Increase
At depth $z$, given an initial groundwater level $z_{gw}$:
- **Initial Total Stress ($\sigma_{v0}$)**: Calculated by summing the weights of overlying layers. $\gamma$ is used above the water table; $\gamma_{sat}$ below.
- **Initial Pore Water Pressure ($u_0$)**: $u_0 = \gamma_w \cdot (z - z_{gw})$ for $z \ge z_{gw}$, 0 otherwise.
- **Initial Effective Stress ($\sigma'_{v0}$)**: $\sigma'_{v0} = \sigma_{v0} - u_0$.

If a drawdown $s$ occurs, the pore pressure decreases. The change in effective vertical stress $\Delta\sigma'_v$ is:
- $0$ above the old groundwater level.
- $\gamma_w(z - z_{gw})$ between the old and new groundwater levels.
- $\gamma_w \cdot s$ below the new groundwater level.

### 3.2 1D Primary Consolidation Settlement
Two methods are provided:
**Linear Elastic (Oedometric) Method:**
$$ \Delta s = \frac{\Delta \sigma'_v}{E_{\text{oed}}} \cdot H $$

**Logarithmic Method ($C_c$/$C_r$):**
Using the virgin compression index ($C_c$), recompression index ($C_r$), and overconsolidation ratio ($OCR$). The preconsolidation pressure is $\sigma'_p = OCR \cdot \sigma'_{v0}$.

1. **Normally Consolidated ($\sigma'_{v0} \ge \sigma'_p$)**:
   $$ \Delta s = \frac{C_c}{1 + e_0} H \log_{10}\left(\frac{\sigma'_{v0} + \Delta \sigma'_v}{\sigma'_{v0}}\right) $$
2. **Overconsolidated ($\sigma'_{v0} + \Delta \sigma'_v \le \sigma'_p$)**:
   $$ \Delta s = \frac{C_r}{1 + e_0} H \log_{10}\left(\frac{\sigma'_{v0} + \Delta \sigma'_v}{\sigma'_{v0}}\right) $$
3. **Transitional ($\sigma'_{v0} < \sigma'_p < \sigma'_{v0} + \Delta \sigma'_v$)**:
   $$ \Delta s = \frac{C_r}{1 + e_0} H \log_{10}\left(\frac{\sigma'_p}{\sigma'_{v0}}\right) + \frac{C_c}{1 + e_0} H \log_{10}\left(\frac{\sigma'_{v0} + \Delta \sigma'_v}{\sigma'_p}\right) $$

### 3.3 Time-Dependent Settlement (Terzaghi Theory)
For clay layers ($k_h < 10^{-5}$ m/s and $C_v > 0$), consolidation occurs progressively over time. Permeable sand boundaries dictate whether a layer undergoes single drainage ($H_{dr} = H$) or double drainage ($H_{dr} = H/2$).

The dimensionless time factor is $T_v = \frac{C_v t}{H_{dr}^2}$.

The average degree of consolidation $U(T_v)$ is approximated:
- For $T_v \le 0.2827$ ($U < 60\%$): $U = \sqrt{\frac{4 T_v}{\pi}}$
- For $T_v > 0.2827$ ($U \ge 60\%$): $U = 1 - \frac{8}{\pi^2} \exp\left(-\frac{\pi^2 T_v}{4}\right)$

The time-dependent settlement of a clay layer is $U \cdot \Delta s_{ult}$. Sand layers are assumed to settle instantaneously ($U=1$).

### References
- Terzaghi, K. (1943). *Theoretical Soil Mechanics*. John Wiley & Sons, New York. [DOI: 10.1002/9780470172766](https://doi.org/10.1002/9780470172766)

## 4. Damage Assessment

Uneven ground settlement beneath a structure induces internal stresses, potentially leading to cracking or structural failure. `settlewell.damage` employs criteria from Burland & Wroth (1974) and the Dutch SBR guidelines (Stichting Bouwresearch) to assess damage risk.

### 4.1 Evaluation Metrics

Buildings are evaluated at 5 key points: the 4 corners and the geometric center. Drawdown and subsequent settlement $s_i$ are calculated for each point.

**Differential Settlement ($\Delta s$):**
The maximum difference in settlement across the foundation.
$$ \Delta s = \max(s_i) - \min(s_i) $$

**Angular Distortion ($\beta$):**
The relative settlement between two points divided by the horizontal distance $L$ between them. It is computed for all pairs of evaluation points to find the maximum distortion:
$$ \beta = \max \left( \frac{|s_i - s_j|}{L_{ij}} \right) $$

**Deflection Ratio ($\Delta / L$):**
The ratio of the maximum deflection (relative to the average corner settlement) to the characteristic length of the building (diagonal).

### 4.2 Damage Classification (SBR / Burland & Wroth)

Based on the maximum angular distortion $\beta$, damage is categorized into 6 classes (0 to 5), typically valid for masonry structures:

| Category | Description | Limit $\beta$ | Expected Crack Width |
| :--- | :--- | :--- | :--- |
| 0 | Negligible | $1/500$ | $< 0.1$ mm |
| 1 | Very slight | $1/333$ | $0.1 - 1$ mm |
| 2 | Slight | $1/250$ | $1 - 5$ mm |
| 3 | Moderate | $1/150$ | $5 - 15$ mm |
| 4 | Severe | $1/75$ | $15 - 25$ mm |
| 5 | Very severe | $> 1/75$ | $> 25$ mm |

*Note: For concrete frame structures (`BuildingType.CONCRETE_FRAME`), the structure's tolerance to distortion is higher, and the assigned risk category is effectively reduced by 1.*

### References
- Burland, J. B., & Wroth, C. P. (1974). Settlement of buildings and associated damage. *Conference on Settlement of Structures*, Cambridge, Pentech Press, London, 611-654.
- SBRCURnet (2014). *Richtlijn Meten en rekenen aan trillingen - Deel A: Schade aan gebouwen*.

## 5. Numerical Methods

While analytical solutions (`settlewell.hydraulics`) are exact for simple domains, complex domains are solved numerically using the `settlewell.numerical` module.

### 5.1 Finite-Difference Flow Solver
The groundwater flow equation is evaluated in steady-state 2D plan view:
$$ T \left( \frac{\partial^2 h}{\partial x^2} + \frac{\partial^2 h}{\partial y^2} \right) = - \sum_{w=1}^{N_w} Q_w \delta(x - x_w, y - y_w) $$
where $h$ is the hydraulic head, $T$ is the aquifer transmissivity, $Q_w$ is the pumping rate (sink, $Q_w > 0$ for extraction), and $\delta$ is the Dirac delta function.

The domain is discretized into a regular grid $(\Delta x, \Delta y)$. The Laplacian is approximated using a standard 5-point stencil central difference:
$$ \nabla^2 h \approx \frac{h_{i-1,j} - 2h_{i,j} + h_{i+1,j}}{(\Delta x)^2} + \frac{h_{i,j-1} - 2h_{i,j} + h_{i,j+1}}{(\Delta y)^2} $$

A Dirichlet boundary condition $h = H_0$ is enforced at the grid edges. The resulting sparse linear system $A\mathbf{h} = \mathbf{b}$ is assembled using `scipy.sparse` and solved with `scipy.sparse.linalg.spsolve`.

### 5.2 Interpolation
Once the head field $h(x, y)$ is obtained at grid nodes, the drawdown $s(x,y) = H_0 - h(x,y)$ at any arbitrary continuous point (such as a building corner) is extracted using bilinear interpolation (`scipy.interpolate.RegularGridInterpolator`).

### References
- Harbaugh, A. W. (2005). *MODFLOW-2005, the U.S. Geological Survey modular ground-water model—the Ground-Water Flow Process*. U.S. Geological Survey Techniques and Methods 6-A16.
