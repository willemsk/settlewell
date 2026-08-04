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
- Elastic parameters: oedometric modulus ($E_{oed}$).
- Time-dependent parameters: coefficient of consolidation ($C_v$).
- Flow parameters: transmissivity ($T$) and storativity/specific yield ($S$), which can be explicitly provided or calculated from layer properties.

### 1.2 Coordinate System
Calculations in `settlewell` use a local Cartesian coordinate system for plan-view geometry $(x, y)$.

Elevations are typically defined relative to a datum, with the Belgian "mTAW" (Tweede Algemene Waterpassing) often used as the default nomenclature in the API. Internally, conversions are handled such that depth $z$ is positive downwards from the ground surface ($z=0$).

Let the ground surface elevation be $Z_{surf}$. The depth $z$ of an elevation $Z$ is simply:
$$ z = Z_{surf} - Z $$

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

## 3. Stress Distribution

The effective vertical stress in the soil can increase due to groundwater drawdown and surface loads.

### 3.1 Initial State and Drawdown Stress
At depth $z$, given an initial groundwater level $z_{gw}$:
- **Initial Total Stress ($\sigma_{v0}$)**: Calculated by summing the weights of overlying layers. $\gamma$ is used above the water table; $\gamma_{sat}$ below.
- **Initial Pore Water Pressure ($u_0$)**: $u_0 = \gamma_w \cdot (z - z_{gw})$ for $z \ge z_{gw}$, 0 otherwise.
- **Initial Effective Stress ($\sigma'_{v0}$)**: $\sigma'_{v0} = \sigma_{v0} - u_0$.

If a drawdown $s$ occurs, the pore pressure decreases. The change in effective vertical stress $\Delta\sigma'_v$ is:
- $0$ above the old groundwater level.
- $\gamma_w(z - z_{gw})$ between the old and new groundwater levels.
- $\gamma_w \cdot s$ below the new groundwater level.

### 3.2 Boussinesq & Fadum Surface Loads
For external surface loads, the increase in vertical stress $\Delta \sigma_z$ at depth $z$ is computed using the theory of elasticity (Boussinesq).
For **strip loads** (infinite length, width $B$, uniform load $q$):
$$ \Delta \sigma_z = \frac{q}{\pi} (\alpha + \sin \alpha \cos \alpha) $$
where $\alpha$ is the angle subtended by the strip load at the point of interest.

For **rectangular loads** (width $B$, length $L$, uniform load $q$), the Fadum (1948) corner solution is used:
$$ I_z = \frac{1}{4\pi} \left[ \frac{2mn\sqrt{m^2+n^2+1}}{m^2+n^2+1+m^2n^2} \cdot \frac{m^2+n^2+2}{m^2+n^2+1} + \arctan\left(\frac{2mn\sqrt{m^2+n^2+1}}{m^2+n^2+1-m^2n^2}\right) \right] $$
where $m = B/z$ and $n = L/z$. The stress under any point is found by superimposing up to 4 corner stresses.

Alternatively, the simplified **2:1 (Two-to-One) method** distributes the load over a linearly expanding area with depth.

## 4. Settlement and Consolidation

Groundwater lowering and surface loads increase the effective stress, leading to compression of the soil skeleton and resulting surface settlements. `settlewell.settlement` implements 1D consolidation theory.

### 4.1 Elastic Settlement
Instantaneous elastic settlement occurs in permeable layers (sand) or immediately upon loading. It is computed using the constrained oedometric modulus $E_{\text{oed}}$:
$$ s_e = \sum \frac{\Delta \sigma'_z}{E_{\text{oed}}} \cdot H $$

### 4.2 1D Primary Consolidation Settlement
For primary consolidation in clays, two methods are provided:

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

### 4.3 Time-Dependent Settlement (Terzaghi Theory)
For clay layers ($k_h < 10^{-5}$ m/s and $C_v > 0$), primary consolidation occurs progressively over time. Permeable sand boundaries dictate whether a layer undergoes single drainage ($H_{dr} = H$) or double drainage ($H_{dr} = H/2$).

The dimensionless time factor is $T_v = \frac{C_v t}{H_{dr}^2}$. The average degree of consolidation $U(T_v)$ is approximated:
- For $T_v \le 0.2827$ ($U < 60\%$): $U = \sqrt{\frac{4 T_v}{\pi}}$
- For $T_v > 0.2827$ ($U \ge 60\%$): $U = 1 - \frac{8}{\pi^2} \exp\left(-\frac{\pi^2 T_v}{4}\right)$

The time-dependent primary settlement of a layer is $U \cdot \Delta s_{ult}$. Sand layers are assumed to settle instantaneously ($U=1$).

**Equivalent $C_v$ for Layered Strata:**
For profiles with multiple clay layers, an equivalent coefficient of consolidation is computed to model them as a single draining unit:
$$ C_{v,eq} = \frac{H_{total}^2}{\left(\sum \frac{H_i}{\sqrt{C_{v,i}}}\right)^2} $$

### 4.4 Secondary Creep
Following primary consolidation, secondary compression (creep) occurs under constant effective stress.
$$ s_{creep} = s_{primary} \cdot \left(\frac{C_{\alpha}}{C_c}\right) \log_{10}\left(\frac{t}{t_p}\right) $$
where $t_p$ is the time required for primary consolidation to complete (default 365 days), and $C_{\alpha}/C_c$ is the creep ratio.

### References
- Terzaghi, K. (1943). *Theoretical Soil Mechanics*. John Wiley & Sons, New York.
- Fadum, R. E. (1948). *Influence values for estimating stresses in elastic foundations*.

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
Once the head field $h(x, y)$ is obtained at grid nodes, the drawdown $s(x,y) = H_0 - h(x,y)$ at any arbitrary continuous point is extracted using bilinear interpolation (`scipy.interpolate.RegularGridInterpolator`).

## 6. Advanced Topics

- For building damage risk assessment, see [Building Damage Risk](building_damage.md).
- For design approaches based on Eurocode 7, see [Eurocode 7 & Flemish ANB](eurocode7.md).
