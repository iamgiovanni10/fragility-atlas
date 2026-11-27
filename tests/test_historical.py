import numpy as np
import pytest
from fragility_atlas.historical import historical_var_es, drawdown_statistics, historical_summary


def test_empirical_var_and_fractional_es():
    # losses sorted: -0.02, 0, 0.01, 0.04, 0.10
    r = [0.02, 0, -0.01, -0.04, -0.10]
    result = historical_var_es(r, confidence=0.7, portfolio_value=100)
    assert result["var"] == pytest.approx(4)
    # top 1.5 losses = 10 + 0.5 * 4
    assert result["expected_shortfall"] == pytest.approx(8)


def test_small_tail_uses_fraction_of_worst_observation():
    result = historical_var_es([-0.1, 0, 0.02], confidence=0.99)
    assert result["var"] == pytest.approx(0.1)
    assert result["expected_shortfall"] == pytest.approx(0.1)


def test_drawdown_compounds_and_tracks_peak():
    result = drawdown_statistics([0.10, -0.20, 0.05])
    assert result["maximum_drawdown"] == pytest.approx(-0.20)
    assert (result["peak_index"], result["trough_index"]) == (1, 2)


@pytest.mark.parametrize("bad", [[0.1], [0.1, np.nan], [[0.1, 0.2]], [-1.01, 0.2]])
def test_invalid_returns_rejected(bad):
    with pytest.raises(ValueError):
        historical_summary(bad)


def test_constant_returns_zero_volatility():
    result = historical_summary([0.01] * 5)
    assert result["annualized_volatility"] == pytest.approx(0)
    assert result["ending_wealth_multiple"] == pytest.approx(1.01 ** 5)


def test_invalid_confidence_and_portfolio_value():
    for confidence in (0, 1, float("nan")):
        with pytest.raises(ValueError):
            historical_var_es([0, 0.1], confidence)
    with pytest.raises(ValueError):
        historical_var_es([0, 0.1], portfolio_value=0)
