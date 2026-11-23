"""Deterministic, auditable risk analysis for LINEAR factor exposures.

Units: shocks and volatilities are decimal returns (e.g. 0.02 = 2%).
Exposure amounts are dollars of P&L per unit factor return.
This is a local Gaussian/Mahalanobis model, not a calibrated probability model.
"""
from dataclasses import dataclass
from typing import Sequence
import numpy as np
from numpy.typing import ArrayLike
from scipy.optimize import minimize


@dataclass(frozen=True)
class Model:
    names: tuple[str, ...]
    exposure: np.ndarray
    covariance: np.ndarray

    @classmethod
    def build(cls, names: Sequence[str], exposure: ArrayLike, covariance: ArrayLike) -> "Model":
        names = tuple(names)
        b = np.asarray(exposure, dtype=float)
        s = np.asarray(covariance, dtype=float)
        n = len(names)
        if n == 0 or len(set(names)) != n or any(not x for x in names):
            raise ValueError("factor names must be nonempty and unique")
        if b.shape != (n,) or s.shape != (n, n):
            raise ValueError("incorrect exposure/covariance dimensions")
        if not np.all(np.isfinite(b)) or not np.all(np.isfinite(s)):
            raise ValueError("nonfinite parameters")
        if not np.allclose(s, s.T, atol=1e-12, rtol=1e-10):
            raise ValueError("covariance is not symmetric")
        if np.min(np.linalg.eigvalsh(s)) <= 1e-14:
            raise ValueError("covariance must be strictly positive definite")
        return cls(names, b.copy(), s.copy())

    def pnl(self, shock: ArrayLike) -> float:
        x = np.asarray(shock, float)
        if x.shape != self.exposure.shape or not np.all(np.isfinite(x)):
            raise ValueError("shock shape or values invalid")
        return float(self.exposure @ x)

    def reverse_stress(self, loss: float) -> dict:
        """Solve min x' Sigma^-1 x subject to b'x <= -loss.

        Closed-form x* = -loss * Sigma b / (b' Sigma b).
        Distance is a geometry-based sigma multiple; NOT a tail probability.
        """
        if not np.isfinite(loss) or loss <= 0:
            raise ValueError("loss must be strictly positive and finite")
        sigma_b = self.covariance @ self.exposure
        variance = float(self.exposure @ sigma_b)
        if variance <= 0:
            raise ValueError("zero exposure: finite loss is unreachable")
        shock = -(loss / variance) * sigma_b
        distance = float(loss / np.sqrt(variance))
        contributions = self.exposure * shock
        return {
            "threshold_loss": float(loss),
            "shock": dict(zip(self.names, map(float, shock))),
            "pnl": self.pnl(shock),
            "mahalanobis_distance": distance,
            "factor_pnl_contributions": dict(zip(self.names, map(float, contributions))),
            "portfolio_volatility_dollars": float(np.sqrt(variance)),
        }

    def hedge(self, loss: float, hedge_matrix: ArrayLike, hedge_cost: ArrayLike,
              hedge_names: Sequence[str], distance_budget: float = 2.0,
              max_units: float = 1e6) -> dict:
        """Minimize L1 hedge expenditure subject to conservative ellipsoid loss cap.

        Each hedge column is dollar P&L sensitivity per ONE purchased hedge unit.
        For h units, residual b+B h has ellipsoidal worst loss
        distance_budget * sqrt((b+B h)' Sigma (b+B h)).
        A split variable representation models |h|; SLSQP is deterministic but
        convergence is not a certificate of global optimality.
        """
        H = np.asarray(hedge_matrix, float)
        c = np.asarray(hedge_cost, float)
        names = tuple(hedge_names)
        k = len(names)
        if H.shape != (len(self.names), k) or c.shape != (k,):
            raise ValueError("bad hedge matrix or cost dimensions")
        if k == 0 or len(set(names)) != k or not np.all(np.isfinite(H)):
            raise ValueError("hedges must be finite and uniquely named")
        if not np.all(np.isfinite(c)) or np.any(c <= 0):
            raise ValueError("hedge costs must be strictly positive")
        if loss <= 0 or distance_budget <= 0 or max_units <= 0:
            raise ValueError("positive loss, distance_budget and max_units required")
        # Optimize hedge dollar P&L sensitivities in MILLION dollars.
        # Scale the nonlinear risk constraint to order-one for SLSQP.
        # z = [positive units, negative units], so h = z[:k]-z[k:].
        pnl_scale = max(1., float(np.linalg.norm(self.exposure)), float(loss))
        B = H / pnl_scale
        baseline = self.exposure / pnl_scale
        risk_limit = float(loss / pnl_scale)

        def residual(z):
            return baseline + B @ (z[:k] - z[k:])

        def norm_risk(z):
            v = residual(z)
            return float(distance_budget * np.sqrt(max(0., v @ self.covariance @ v)))

        # Feasible starting point when hedge matrix can span the exposure.
        initial_units = np.linalg.lstsq(H, -self.exposure, rcond=None)[0]
        initial_units = np.clip(initial_units, -max_units, max_units)
        initial = np.r_[np.maximum(initial_units, 0), np.maximum(-initial_units, 0)]
        cost_scale = max(1., float(c @ np.abs(initial_units)))
        objective_cost = c / cost_scale
        result = minimize(lambda z: float(objective_cost @ (z[:k] + z[k:])),
                          initial, method="SLSQP",
                          bounds=[(0., max_units)] * (2 * k),
                          constraints=[{"type": "ineq", "fun": lambda z: risk_limit - norm_risk(z)}],
                          options={"maxiter": 3000, "ftol": 1e-11})
        units = result.x[:k] - result.x[k:]
        cap = float(norm_risk(result.x) * pnl_scale)
        tol = 1e-6 * max(1., loss)
        if not result.success or cap > loss + tol:
            raise RuntimeError(f"no feasible hedge found: {result.message}; risk={cap}")
        return {
            "units": dict(zip(names, map(float, units))),
            "estimated_cost": float(c @ np.abs(units)),
            "worst_ellipsoid_loss": cap,
            "loss_cap": float(loss),
            "distance_budget": float(distance_budget),
            "solver": "SLSQP (locally solved; independently check constraints)",
        }
