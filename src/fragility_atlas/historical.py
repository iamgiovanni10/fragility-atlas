"""Historical portfolio risk measures with explicit, reproducible conventions.

Input: chronological SIMPLE daily returns in decimal units, not prices or percentages.
No annualization is applied to quantiles or expected shortfall.
"""
from dataclasses import dataclass
import numpy as np


def _returns(values):
    r = np.asarray(values, dtype=float)
    if r.ndim != 1 or r.size < 2 or not np.all(np.isfinite(r)):
        raise ValueError("returns must be a finite one-dimensional series of length >= 2")
    if np.any(r < -1):
        raise ValueError("simple returns cannot be below -100%")
    return r


def historical_var_es(returns, confidence=0.99, portfolio_value=1.0):
    """Empirical loss quantile and ES, with fractional mass at the VaR cutoff.

    VaR is the upper-tail loss quantile using the empirical inverse-CDF order statistic (ceil(n*c)-1).
    ES is the average loss over exactly (1-confidence) probability mass,
    including fractional weight on the cutoff observation. Losses may be negative.
    """
    r = _returns(returns)
    if not np.isfinite(confidence) or not 0 < confidence < 1:
        raise ValueError("confidence must be in (0, 1)")
    if not np.isfinite(portfolio_value) or portfolio_value <= 0:
        raise ValueError("portfolio_value must be finite and positive")
    losses = np.sort(-r * portfolio_value)
    if not np.all(np.isfinite(losses)):
        raise ValueError("numeric overflow in historical loss calculation")
    n = len(losses)
    tail_mass = (1 - confidence) * n
    full = int(np.floor(tail_mass))
    fractional = tail_mass - full
    tail_sum = float(np.sum(losses[-full:])) if full else 0.0
    if fractional > 1e-12:
        tail_sum += fractional * float(losses[-full - 1])
    es = tail_sum / tail_mass
    if not np.isfinite(es):
        raise ValueError("numeric overflow in expected shortfall")
    index = int(np.ceil(confidence * n) - 1)
    var = float(losses[index])
    return {"confidence": float(confidence), "observations": n,
            "var": var, "expected_shortfall": float(es),
            "portfolio_value": float(portfolio_value),
            "convention": "empirical inverse-CDF VaR (ceil(n*c)-1); fractional-tail ES"}


def drawdown_statistics(returns):
    """Compounded wealth starts at 1; reports first peak-to-trough maximum drawdown."""
    r = _returns(returns)
    wealth = np.r_[1.0, np.cumprod(1.0 + r)]
    if not np.all(np.isfinite(wealth)):
        raise ValueError("numeric overflow in compounded wealth")
    peaks = np.maximum.accumulate(wealth)
    drawdowns = wealth / peaks - 1.0
    trough = int(np.argmin(drawdowns))
    peak = int(np.argmax(wealth[:trough + 1]))
    return {"maximum_drawdown": float(drawdowns[trough]),
            "peak_index": peak, "trough_index": trough,
            "ending_wealth_multiple": float(wealth[-1])}


def historical_summary(returns, confidence=0.99, portfolio_value=1.0,
                       periods_per_year=252):
    r = _returns(returns)
    if not isinstance(periods_per_year, int) or periods_per_year <= 0:
        raise ValueError("periods_per_year must be a positive integer")
    metrics = historical_var_es(r, confidence, portfolio_value)
    metrics.update(drawdown_statistics(r))
    metrics["mean_daily_return"] = float(np.mean(r))
    metrics["annualized_volatility"] = float(np.std(r, ddof=1) * np.sqrt(periods_per_year))
    if not np.isfinite(metrics["mean_daily_return"]) or not np.isfinite(metrics["annualized_volatility"]):
        raise ValueError("numeric overflow in return summary")
    metrics["periods_per_year"] = periods_per_year
    return metrics
