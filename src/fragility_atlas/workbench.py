"""Pure calculations supporting the v0.2 risk workbench.

No probabilities or live market data are implied.
"""
import numpy as np


def ellipsoid_worst_loss(exposure, covariance, radius):
    b = np.asarray(exposure, dtype=float)
    s = np.asarray(covariance, dtype=float)
    if not np.isfinite(radius) or radius <= 0:
        raise ValueError("radius must be positive and finite")
    return float(radius * np.sqrt(max(0.0, b @ s @ b)))


def scenario_pnl(exposure, shocks):
    b = np.asarray(exposure, dtype=float)
    x = np.asarray(shocks, dtype=float)
    if b.ndim != 1 or x.shape != b.shape or not np.all(np.isfinite(x)):
        raise ValueError("invalid scenario shocks")
    return float(b @ x)


def hedge_diagnostics(model, hedge, hedge_matrix, loss, radius):
    """Recompute residual risk independently of solver's reported values."""
    h = np.asarray(list(hedge["units"].values()), dtype=float)
    H = np.asarray(hedge_matrix, dtype=float)
    residual = model.exposure + H @ h
    before = ellipsoid_worst_loss(model.exposure, model.covariance, radius)
    after = ellipsoid_worst_loss(residual, model.covariance, radius)
    tolerance = 1e-6 * max(1.0, float(loss))
    return {
        "before_worst_loss": before,
        "after_worst_loss": after,
        "risk_reduction": before - after,
        "risk_reduction_pct": 100 * (1 - after / before) if before > 0 else 0.0,
        "constraint_slack": float(loss - after),
        "constraint_satisfied": bool(after <= loss + tolerance),
        "residual_exposure": residual.tolist(),
        "max_recomputed_vs_reported_error": abs(after - float(hedge["worst_ellipsoid_loss"])),
    }
