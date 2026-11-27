import numpy as np
import pytest
from fragility_atlas.workbench import ellipsoid_worst_loss, scenario_pnl


def test_ellipsoid_matches_analytic_diagonal_case():
    result = ellipsoid_worst_loss([100, 50], [[0.04, 0], [0, 0.01]], 2)
    assert result == pytest.approx(2 * np.sqrt(425))


@pytest.mark.parametrize("exposure,covariance", [
    ([1, 2], [[1]]),
    ([1], [[float("nan")]]),
    ([float("nan")], [[1]]),
    ([1, 2], [[1, 0.1], [0.2, 1]]),
    ([1], [[-1]]),
    ([], []),
])
def test_ellipsoid_rejects_invalid_inputs(exposure, covariance):
    with pytest.raises((ValueError, np.linalg.LinAlgError)):
        ellipsoid_worst_loss(exposure, covariance, 2)


def test_scenario_pnl_rejects_nonfinite_exposure():
    with pytest.raises(ValueError):
        scenario_pnl([float("nan")], [0.1])
