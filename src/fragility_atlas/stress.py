"""Historical replay and hypothetical linear-factor scenario evaluation."""
import numpy as np


def evaluate_scenarios(exposure, factor_names, scenarios):
    """Return scenario P&L and factor contributions; shocks are decimal returns.

    scenarios maps scenario name -> factor name -> decimal shock.
    Missing or extra factor names are rejected to avoid silent misalignment.
    """
    names = tuple(factor_names)
    b = np.asarray(exposure, dtype=float)
    if not names or len(set(names)) != len(names) or b.shape != (len(names),):
        raise ValueError("invalid factors/exposures")
    if not np.all(np.isfinite(b)) or not isinstance(scenarios, dict):
        raise ValueError("invalid inputs")
    results = {}
    for scenario_name, shock_map in scenarios.items():
        if not isinstance(scenario_name, str) or not scenario_name or not isinstance(shock_map, dict):
            raise ValueError("invalid scenario")
        if set(shock_map) != set(names):
            raise ValueError("scenario must specify every factor exactly once")
        x = np.asarray([shock_map[name] for name in names], dtype=float)
        if not np.all(np.isfinite(x)):
            raise ValueError("nonfinite scenario shock")
        contribution = b * x
        results[scenario_name] = {
            "pnl": float(np.sum(contribution)),
            "factor_pnl": dict(zip(names, map(float, contribution))),
            "shocks": dict(zip(names, map(float, x))),
        }
    return results


def replay_factor_history(exposure, factor_names, history):
    """Replay chronological historical factor shocks; returns P&L series.

    Each history row must contain exactly one decimal shock per factor.
    No market data or crisis dates are inferred by this function.
    """
    names = tuple(factor_names)
    b = np.asarray(exposure, dtype=float)
    h = np.asarray(history, dtype=float)
    if not names or len(set(names)) != len(names) or b.shape != (len(names),):
        raise ValueError("invalid factor exposures")
    if h.ndim != 2 or h.shape[1] != len(names) or h.shape[0] < 2:
        raise ValueError("history must contain at least two factor observations")
    if not np.all(np.isfinite(h)) or not np.all(np.isfinite(b)):
        raise ValueError("nonfinite history or exposure")
    return (h @ b).tolist()
