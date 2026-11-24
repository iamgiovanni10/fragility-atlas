"""Pure calculations supporting the v0.2 risk workbench.

No probabilities or live market data are implied.
"""
import numpy as np


def ellipsoid_worst_loss(exposure, covariance, radius):
    b = np.asarray(exposure, dtype=float)
    s = np.asarray(covariance, dtype=float)
    if b.ndim != 1 or b.size == 0 or s.shape != (b.size, b.size):
        raise ValueError("incompatible exposure/covariance dimensions")
    if not np.all(np.isfinite(b)) or not np.all(np.isfinite(s)):
        raise ValueError("exposure and covariance must be finite")
    if not np.allclose(s, s.T, rtol=1e-10, atol=1e-12):
        raise ValueError("covariance must be symmetric")
    np.linalg.cholesky(s)
    if not np.isfinite(radius) or radius <= 0:
        raise ValueError("radius must be positive and finite")
    return float(radius * np.sqrt(max(0.0, b @ s @ b)))


def scenario_pnl(exposure, shocks):
    b = np.asarray(exposure, dtype=float)
    x = np.asarray(shocks, dtype=float)
    if b.ndim != 1 or x.shape != b.shape or not np.all(np.isfinite(x)) or not np.all(np.isfinite(b)):
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


def scenario_comparison(exposure, covariance, shocks, radius, hedge_matrix=None, hedge_units=None):
    """Compare the same shock before/after hedging and classify ellipsoid membership.

    Membership is geometric only; it does not imply scenario probability.
    Hedge units must be in the same order as hedge_matrix columns.
    """
    b = np.asarray(exposure, dtype=float)
    s = np.asarray(covariance, dtype=float)
    x = np.asarray(shocks, dtype=float)
    if b.ndim != 1 or x.shape != b.shape or s.shape != (b.size, b.size):
        raise ValueError("incompatible factor dimensions")
    if not (np.all(np.isfinite(b)) and np.all(np.isfinite(s)) and np.all(np.isfinite(x))):
        raise ValueError("inputs must be finite")
    if not np.isfinite(radius) or radius <= 0:
        raise ValueError("radius must be positive and finite")
    np.linalg.cholesky(s)
    distance = float(np.sqrt(max(0.0, x @ np.linalg.solve(s, x))))
    before = float(b @ x)
    result = {
        "before_pnl": before,
        "mahalanobis_distance": distance,
        "uncertainty_radius": float(radius),
        "inside_uncertainty_set": bool(distance <= radius + 1e-10 * max(1.0, radius)),
    }
    if (hedge_matrix is None) != (hedge_units is None):
        raise ValueError("hedge matrix and units must be supplied together")
    if hedge_matrix is not None:
        H = np.asarray(hedge_matrix, dtype=float)
        h = np.asarray(hedge_units, dtype=float)
        if H.ndim != 2 or H.shape[0] != b.size or h.shape != (H.shape[1],):
            raise ValueError("incompatible hedge dimensions")
        if not (np.all(np.isfinite(H)) and np.all(np.isfinite(h))):
            raise ValueError("hedge inputs must be finite")
        after = float((b + H @ h) @ x)
        result.update({
            "after_pnl": after,
            "pnl_change": after - before,
            "after_factor_contributions": ((b + H @ h) * x).tolist(),
        })
    return result
