"""Reference cases for empirical quantile and fractional-tail ES conventions."""
import pytest

from fragility_atlas.historical import historical_var_es, drawdown_statistics


def test_empirical_var_uses_inverse_cdf_order_statistic():
    # Losses sorted: [1, 2, 3, 4]; 75% VaR is third order statistic.
    result = historical_var_es([-0.01, -0.02, -0.03, -0.04],
                               confidence=0.75, portfolio_value=100)
    assert result["var"] == pytest.approx(3.0)
    assert result["expected_shortfall"] == pytest.approx(4.0)


def test_fractional_tail_expected_shortfall():
    # Four losses: 1,2,3,4; 37.5% tail = worst 1.5 observations.
    result = historical_var_es([-0.01, -0.02, -0.03, -0.04],
                               confidence=0.625, portfolio_value=100)
    assert result["var"] == pytest.approx(3.0)
    assert result["expected_shortfall"] == pytest.approx((4 + 0.5 * 3) / 1.5)


def test_drawdown_includes_initial_wealth_peak():
    result = drawdown_statistics([-0.2, 0.1])
    assert result["maximum_drawdown"] == pytest.approx(-0.2)
    assert result["peak_index"] == 0
    assert result["trough_index"] == 1


@pytest.mark.parametrize("returns,notional,pattern", [
    ([-1e-2, 1e308], 1e308, "historical loss"),
    ([1e308, 1e308], 1.0, "expected shortfall"),
])
def test_historical_var_rejects_overflow(returns, notional, pattern):
    with pytest.raises(ValueError, match=pattern):
        historical_var_es(returns, confidence=0.75, portfolio_value=notional)


def test_drawdown_rejects_compounding_overflow():
    with pytest.raises(ValueError, match="compounded wealth"):
        drawdown_statistics([1e308, 1e308])
