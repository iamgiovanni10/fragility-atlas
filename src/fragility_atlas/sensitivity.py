"""Deterministic reverse-stress sensitivity under controlled perturbations."""
import numpy as np
from .core import Model


def reverse_stress_sensitivity(model, loss, exposure_scales=(0.9, 1.0, 1.1),
                               covariance_scales=(0.8, 1.0, 1.2)):
    """Grid of strictly positive exposure/covariance scalar multipliers.

    Uniform scaling is a diagnostic, not a simulation of covariance regime shifts.
    """
    rows = []
    if len(exposure_scales) * len(covariance_scales) > 100:
        raise ValueError("sensitivity grid too large")
    for e in exposure_scales:
        for c in covariance_scales:
            if not np.isfinite(e) or not np.isfinite(c) or e <= 0 or c <= 0:
                raise ValueError("scales must be finite and strictly positive")
            perturbed = Model.build(model.names, model.exposure * e, model.covariance * c)
            result = perturbed.reverse_stress(loss)
            rows.append({
                "exposure_scale": float(e), "covariance_scale": float(c),
                "distance": result["mahalanobis_distance"],
                "shock": result["shock"], "pnl": result["pnl"],
            })
    return rows
