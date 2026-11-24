# Historical risk methodology — research module

The `fragility_atlas.historical` module accepts a chronological vector of **simple returns in decimal units**, e.g. `-0.03` for a -3% return. It does not fetch market data or infer whether observations are daily. Returns must be finite, at least two observations long, and no return can be less than -100%.

## Definitions

Let `L_t = -V * r_t` denote loss on portfolio value `V`. Historical VaR at confidence `c` is the sorted-loss observation at zero-based index `ceil(c*n)-1`. Expected shortfall averages the worst `(1-c)*n` observations, assigning fractional weight to the boundary observation. Unlike some software conventions, **negative VaR is possible** when every observed period is profitable. ES and VaR are single-period quantities and are not annualized.

Maximum drawdown uses compounded wealth starting at 1.0 and includes the initial observation. Annualized volatility is sample standard deviation (`ddof=1`) multiplied by the square root of a user-specified annual periods count (default 252).

## Example

```python
from fragility_atlas.historical import historical_summary
print(historical_summary([0.02, 0, -0.01, -0.04, -0.10],
                         confidence=0.8, portfolio_value=1_000_000))
```

## Limitations

Historical VaR/ES describe the supplied observations, **not** guaranteed future tail losses. Results depend on sample size, stationarity, portfolio valuation, return frequency, selection bias, and market regimes. This module currently supports one aggregate return series only; it does not estimate a covariance matrix, validate factor mappings, ingest live data, or backtest forecasts. No claims of empirical validation are made.
