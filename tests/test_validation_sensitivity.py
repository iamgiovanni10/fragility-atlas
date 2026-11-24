import numpy as np
import pytest
from fragility_atlas.core import Model
from fragility_atlas.validation import var_coverage, rolling_historical_var
from fragility_atlas.sensitivity import reverse_stress_sensitivity


def test_coverage_all_zero_exceedances_is_finite():
    result = var_coverage(np.zeros(100), np.ones(100), alpha=0.01)
    assert result["exceedances"] == 0
    assert np.isfinite(result["kupiec_lr_uc"])
    assert 0 <= result["p_value_chi2_1df"] <= 1


def test_coverage_all_exceedances_is_finite():
    result = var_coverage(np.ones(100), np.zeros(100), alpha=0.01)
    assert result["exceedances"] == 100
    assert np.isfinite(result["kupiec_lr_uc"])


def test_coverage_strict_exceedance():
    result = var_coverage([1.0] * 20, [1.0] * 20)
    assert result["exceedances"] == 0


def test_rolling_uses_prior_observations_only():
    r = [0.0] * 25 + [-0.5]
    out = rolling_historical_var(r, window=20, confidence=0.95)
    assert len(out["forecast_vars"]) == 6
    assert out["forecast_vars"][-1] == pytest.approx(0)
    assert out["realized_losses"][-1] == pytest.approx(0.5)


def test_sensitivity_uniform_scale_identity():
    m = Model.build(["eq"], [100.0], [[0.04]])
    rows = reverse_stress_sensitivity(m, 10, (1.0, 2.0), (1.0,))
    assert rows[0]["distance"] == pytest.approx(0.5)
    assert rows[1]["distance"] == pytest.approx(0.25)
    assert all(row["pnl"] == pytest.approx(-10) for row in rows)


def test_bad_grid_rejected():
    m = Model.build(["eq"], [100.0], [[0.04]])
    with pytest.raises(ValueError):
        reverse_stress_sensitivity(m, 10, (0,), (1,))
