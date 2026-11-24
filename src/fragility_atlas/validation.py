"""Out-of-sample VaR exceedance diagnostics (not a model certification)."""
import math
import numpy as np
from scipy.stats import chi2


def var_coverage(realized_losses, forecast_vars, alpha=0.01):
    """Kupiec unconditional coverage LR test of Bernoulli exceedances.

    Inputs are aligned one-step-ahead VaR forecasts and subsequent realized
    losses, in matching currency units. alpha is expected breach probability.
    A p-value is descriptive, not proof of model validity or independence.
    """
    y = np.asarray(realized_losses, dtype=float)
    q = np.asarray(forecast_vars, dtype=float)
    if y.ndim != 1 or q.shape != y.shape or y.size < 20:
        raise ValueError("aligned series with at least 20 observations required")
    if not (np.all(np.isfinite(y)) and np.all(np.isfinite(q))):
        raise ValueError("nonfinite losses or forecasts")
    if not np.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError("alpha must be in (0,1)")
    breaches = y > q
    n = len(y)
    k = int(np.sum(breaches))
    p_hat = k / n
    def term(count, p):
        return 0.0 if count == 0 else count * math.log(p)
    ll_null = term(k, alpha) + term(n - k, 1 - alpha)
    ll_alt = term(k, p_hat) + term(n - k, 1 - p_hat)
    statistic = max(0.0, 2 * (ll_alt - ll_null))
    return {
        "observations": n, "exceedances": k, "expected_exceedances": float(n * alpha),
        "observed_exceedance_rate": float(p_hat), "expected_exceedance_rate": float(alpha),
        "kupiec_lr_uc": float(statistic), "p_value_chi2_1df": float(chi2.sf(statistic, 1)),
        "definition": "breach if realized loss > ex-ante VaR forecast",
        "warning": "Requires genuinely out-of-sample forecasts; does not test breach independence.",
    }


def rolling_historical_var(returns, window=250, confidence=0.99, portfolio_value=1.0):
    """Forecast each next observation using ONLY the preceding rolling window."""
    from .historical import _returns, historical_var_es
    r = _returns(returns)
    if not isinstance(window, int) or window < 20 or window >= len(r):
        raise ValueError("window must be >=20 and smaller than series length")
    forecasts = [
        historical_var_es(r[t - window:t], confidence, portfolio_value)["var"]
        for t in range(window, len(r))
    ]
    losses = (-r[window:] * portfolio_value).tolist()
    return {"forecast_vars": forecasts, "realized_losses": losses,
            "window": window, "confidence": float(confidence),
            "coverage": var_coverage(losses, forecasts, alpha=1-confidence)}
