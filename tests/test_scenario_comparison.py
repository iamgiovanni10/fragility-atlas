import numpy as np
import pytest

from fragility_atlas.workbench import scenario_comparison


def test_inside_and_outside_ellipsoid():
    s = np.eye(2)
    inside = scenario_comparison([100, 50], s, [0.5, 0.5], 1)
    outside = scenario_comparison([100, 50], s, [2, 0], 1)
    assert inside["inside_uncertainty_set"]
    assert not outside["inside_uncertainty_set"]
    assert outside["mahalanobis_distance"] == pytest.approx(2)


def test_same_scenario_hedge_changes_pnl():
    result = scenario_comparison([100, 0], np.eye(2), [-0.05, 0.01], 1, [[-10], [0]], [5])
    assert result["before_pnl"] == pytest.approx(-5)
    assert result["after_pnl"] == pytest.approx(-2.5)
    assert result["pnl_change"] == pytest.approx(2.5)
    assert sum(result["after_factor_contributions"]) == pytest.approx(result["after_pnl"])


def test_rejects_mismatched_hedges():
    with pytest.raises(ValueError):
        scenario_comparison([1], [[1]], [0.1], 1, [[1]], None)


def test_rejects_singular_covariance():
    with pytest.raises(np.linalg.LinAlgError):
        scenario_comparison([1, 1], [[1, 1], [1, 1]], [0.1, 0.2], 1)
