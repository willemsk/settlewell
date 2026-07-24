# Settlement & Building Damage Specification

This document specifies 1D Terzaghi consolidation settlement calculation (`src/settlewell/settlement.py`) and building damage assessment (`src/settlewell/damage.py`).

---

## 1D Consolidation Settlement (`src/settlewell/settlement.py`)

### Terzaghi Effective Stress Concept
Dewatering lowers the pore water pressure ($\Delta u = -\gamma_w \cdot s$), which causes an equal increase in vertical effective stress:
\[
\Delta \sigma' = \gamma_w \cdot s(x, y)
\]
where $\gamma_w = 9.81\text{ kN/m}^3$ and $s(x, y)$ is groundwater drawdown [m].

### Settlement Calculation Methods

#### 1. Non-linear Logarithmic Method (`cc_cr`)
Consolidation settlement $\Delta h$ for a sublayer of initial thickness $h_0$ with initial effective stress $\sigma'_{0}$:

- **Normally Consolidated Soil ($\text{OCR} = 1.0$ or $\sigma'_{0} \ge \sigma'_p$)**:
  \[
  \Delta h = h_0 \cdot \frac{C_c}{1 + e_0} \cdot \log_{10}\left(\frac{\sigma'_{0} + \Delta\sigma'}{\sigma'_{0}}\right)
  \]
- **Overconsolidated Soil ($\text{OCR} > 1.0$)**:
  - Case 1: $\sigma'_{0} + \Delta\sigma' \le \sigma'_p$:
    \[
    \Delta h = h_0 \cdot \frac{C_r}{1 + e_0} \cdot \log_{10}\left(\frac{\sigma'_{0} + \Delta\sigma'}{\sigma'_{0}}\right)
    \]
  - Case 2: $\sigma'_{0} + \Delta\sigma' > \sigma'_p$:
    \[
    \Delta h = h_0 \cdot \frac{C_r}{1 + e_0} \cdot \log_{10}\left(\frac{\sigma'_p}{\sigma'_{0}}\right) + h_0 \cdot \frac{C_c}{1 + e_0} \cdot \log_{10}\left(\frac{\sigma'_{0} + \Delta\sigma'}{\sigma'_p}\right)
    \]
where $\sigma'_p = \text{OCR} \cdot \sigma'_{0}$ is the preconsolidation pressure.

#### 2. Linear Oedometer Modulus Method (`eoed`)
\[
\Delta h = h_0 \cdot \frac{\Delta\sigma'}{E_{oed}}
\]
where $E_{oed}$ is the constrained oedometer modulus [kPa].

### Time-Dependent Consolidation (Terzaghi 1D Theory)
Degree of consolidation $U(t)$ as a function of dimensionless time factor $T_v$:
\[
T_v = \frac{C_v \cdot t}{H_{dr}^2}
\]
where $H_{dr} = h_0 / 2$ for double drainage (permeable sand/fill layers above and below clay) or $H_{dr} = h_0$ for single drainage.

Degree of consolidation approximation (`compute_degree_of_consolidation`):
- For $T_v \le 0.2827$:
  \[
  U(T_v) = 2 \sqrt{\frac{T_v}{\pi}}
  \]
- For $T_v > 0.2827$:
  \[
  U(T_v) = 1 - \frac{8}{\pi^2} \exp\left(-\frac{\pi^2}{4} T_v\right)
  \]
Time-dependent settlement:
\[
s(t) = U(T_v) \cdot s_{\text{final}}
\]

---

## Building Damage Assessment (`src/settlewell/damage.py`)

### Damage Metrics

#### Differential Settlement & Pairwise Angular Distortion ($\beta$)
For evaluation points across a building foundation (center and 4 corners):
\[
\Delta s = s_{max} - s_{min}
\]
\[
\beta = \max_{i < j} \frac{|s_i - s_j|}{\text{distance}(p_i, p_j)}
\]
where $\text{distance}(p_i, p_j)$ is the Euclidean distance between any pair of evaluation points $p_i$ and $p_j$.

#### Deflection Ratio ($\Delta / L$)
\[
\frac{\Delta}{L} = \frac{|s_{max} - s_{\text{corner\_avg}}|}{\max(L_{\text{diag}}, 10^{-3})}
\]
where $s_{\text{corner\_avg}} = \frac{1}{4} \sum_{k=1}^4 s_{\text{corner}_k}$ is the average settlement of the 4 building corners and $L_{\text{diag}} = \sqrt{\text{length}^2 + \text{width}^2}$.

### SBR / Burland & Wroth Classification Thresholds (`SBR_THRESHOLDS`)

| Damage Category | Description (EN / NL) | Crack Width Range | Angular Distortion $\beta$ Threshold | Risk Color |
|:---:|---|---|:---:|:---:|
| **0** | Negligible / Verwaarloosbaar | $< 0.1$ mm | $\beta < 1/500$ ($0.0020$) | `green` |
| **1** | Very slight / Zeer licht | $0.1 - 1.0$ mm | $1/500 \le \beta < 1/333$ ($0.003003$) | `yellow` |
| **2** | Slight / Licht | $1.0 - 5.0$ mm | $1/333 \le \beta < 1/250$ ($0.0040$) | `orange` |
| **3** | Moderate / Matig | $5.0 - 15.0$ mm | $1/250 \le \beta < 1/150$ ($0.006667$) | `red` |
| **4** | Severe / Ernstig | $15.0 - 25.0$ mm | $1/150 \le \beta < 1/75$ ($0.013333$) | `darkred` |
| **5** | Very severe / Zeer ernstig | $> 25.0$ mm | $\beta \ge 1/75$ ($0.013333$) | `black` |

#### Structural Type Adjustment
If `building_type == BuildingType.CONCRETE_FRAME`, the calculated damage category is discounted down by 1 category (`category = max(0, category - 1)`) to reflect greater ductility relative to load-bearing masonry.

### Result Structure (`DamageAssessment`)
```python
@dataclass
class DamageAssessment:
    settlement_at_points: dict[str, float]  # Point name -> settlement [m]
    max_settlement: float  # [m]
    min_settlement: float  # [m]
    differential_settlement: float  # [m]
    angular_distortion: float  # [-]
    deflection_ratio: float  # [-]
    damage_category: int  # 0 to 5
    damage_description: str  # Human-readable description
    expected_crack_width: str  # Expected crack width description
    risk_color: str  # Hex or named color string ("green", "yellow", etc.)
```
