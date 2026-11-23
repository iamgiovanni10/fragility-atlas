import numpy as np
import pytest

from fragility_atlas import Model
from fragility_atlas.workbench import ellipsoid_worst_loss, scenario_pnl, hedge_diagnostics


def test_ellipsoid_matches_analytic():
    b = np.array([2.0, -1.0])
    s = np.eye(2)
    assert ellipsoid_worst_loss(b, s, 2) == pytest.approx(2 * np.sqrt(5))


def test_manual_scenario_pnl():
    assert scenario_pnl([100, -50], [-0.02, 0.01]) == pytest.approx(-2.5)


def test_manual_scenario_rejects_invalid_shape():
    with pytest.raises(ValueError):
        scenario_pnl([100, -50], [0.01])


def test_diagnostics_recompute_constraint():
    model = Model.build(["a"], [100.0], [[0.04]])
    hedge = {"units": {"h": 50.0}, "worst_ellipsoid_loss": 20.0}
    d = hedge_diagnostics(model, hedge, [[-1.0]], 25.0, 2.0)
    assert d["before_worst_loss"] == pytest.approx(40.0)
    assert d["after_worst_loss"] == pytest.approx(20.0)
    assert d["constraint_satisfied"]
    assert d["risk_reduction_pct"] == pytest.approx(50.0)
