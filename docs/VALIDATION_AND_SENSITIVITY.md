# Out-of-sample validation and sensitivity

## VaR coverage

`rolling_historical_var` uses the preceding `window` simple-return observations to forecast the next observation's empirical VaR; it never includes the observation being predicted. `var_coverage` accepts precomputed ex-ante VaR forecasts and realized losses in identical monetary units, with a strict breach criterion `loss > forecast`.

The Kupiec likelihood-ratio statistic tests unconditional Bernoulli coverage against the expected breach rate `alpha`. Its chi-squared p-value is asymptotic; small expected breach counts make the approximation unreliable. It does **not** test exceedance independence, tail severity, structural breaks, or future predictive accuracy. An insignificant p-value is not proof of a good risk model.

## Sensitivity

`reverse_stress_sensitivity` evaluates a bounded grid of uniformly scaled exposures and covariance matrices. This checks numerical stability and the response of the closed-form reverse-stress distance, but is **not** a full regime-switching or estimation-error analysis. All results use linear P&L and synthetic inputs unless the caller supplies independently sourced data.

## Reproducibility

```python
from fragility_atlas.validation import rolling_historical_var
from fragility_atlas.sensitivity import reverse_stress_sensitivity
from fragility_atlas.core import Model

print(rolling_historical_var([0.001, -0.002] * 150, window=100))
model = Model.build(["equities"], [1000000], [[0.04**2]])
print(reverse_stress_sensitivity(model, 100000))
```

These diagnostics are research aids, not regulatory validation or investment advice.
