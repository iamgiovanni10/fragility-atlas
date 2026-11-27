import numpy as np
import pytest
from fragility_atlas.core import Model


def test_reverse_stress_matches_threshold_and_contributions():
    m = Model.build(["eq", "rates"], [1_000_000, -250_000],
                    [[0.0004, 0.0], [0.0, 0.0001]])
    result = m.reverse_stress(50_000)
    assert result["pnl"] == pytest.approx(-50_000)
    assert sum(result["factor_pnl_contributions"].values()) == pytest.approx(-50_000)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -1, 0])
def test_hedge_rejects_invalid_loss(bad):
    m = Model.build(["eq"], [100.0], [[0.04]])
    with pytest.raises(ValueError):
        m.hedge(bad, [[-100]], [1], ["short_eq"])


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -1, 0])
def test_hedge_rejects_invalid_radius(bad):
    m = Model.build(["eq"], [100.0], [[0.04]])
    with pytest.raises(ValueError):
        m.hedge(1, [[-100]], [1], ["short_eq"], distance_budget=bad)


def test_hedge_residual_risk_recomputed():
    m = Model.build(["eq"], [100.0], [[0.04]])
    result = m.hedge(1, [[-100.0]], [1.0], ["short_eq"], distance_budget=2.0)
    units = result["units"]["short_eq"]
    independent = 2 * abs(100 - 100 * units) * 0.2
    assert independent == pytest.approx(result["worst_ellipsoid_loss"])
    assert independent <= 1.000001
