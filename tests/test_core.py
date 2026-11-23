import numpy as np
import pytest
from fragility_atlas import Model


def model():
    return Model.build(["a", "b"], [10., -4.], [[0.04, 0.005], [0.005, 0.01]])


def test_exact_reverse_threshold():
    m = model()
    r = m.reverse_stress(3.)
    assert r["pnl"] == pytest.approx(-3.)
    assert sum(r["factor_pnl_contributions"].values()) == pytest.approx(-3.)
    assert r["mahalanobis_distance"] > 0


def test_reverse_solution_minimum_distance():
    m = model()
    r = m.reverse_stress(3.)
    x = np.array(list(r["shock"].values()))
    # Any perturbation orthogonal to the exposure preserves the loss and
    # should have equal or greater Mahalanobis distance.
    p = np.array([4., 10.])
    inv = np.linalg.inv(m.covariance)
    for t in [-2, -.5, .1, 1]:
        y = x + t * p
        assert m.exposure @ y == pytest.approx(-3.)
        assert y @ inv @ y >= x @ inv @ x - 1e-9


def test_invalid_covariance_rejected():
    with pytest.raises(ValueError):
        Model.build(["a", "b"], [1, 2], [[1, 2], [2, 1]])


def test_no_exposure_rejected():
    with pytest.raises(ValueError):
        Model.build(["a"], [0], [[1]]).reverse_stress(1)


def test_hedge_meets_risk_cap():
    m = model()
    result = m.hedge(1., [[-1., 0.], [0., 1.]], [1., 1.], ["x", "y"], 2.)
    assert result["worst_ellipsoid_loss"] <= 1. + 1e-6
    assert result["estimated_cost"] >= 0
