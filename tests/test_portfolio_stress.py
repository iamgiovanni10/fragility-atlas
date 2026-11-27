import pytest
from fragility_atlas.portfolio import read_portfolio_csv
from fragility_atlas.stress import evaluate_scenarios, replay_factor_history


SAMPLE = """position_id,quantity,price_usd,equities,rates
A,2,100,1000,-50
B,-1,40,200,20
"""


def test_portfolio_reconciliation():
    p = read_portfolio_csv(SAMPLE)
    assert p.value == pytest.approx(160)
    assert p.exposure.tolist() == pytest.approx([1800, -120])
    result = p.scenario([-0.1, 0.02])
    assert result["total_pnl"] == pytest.approx(-182.4)
    assert sum(result["position_pnl"].values()) == pytest.approx(result["total_pnl"])
    assert sum(result["factor_pnl"].values()) == pytest.approx(result["total_pnl"])


@pytest.mark.parametrize("bad", [
    "position_id,quantity,price_usd,equities\nA,1,2,3\nA,1,2,3\n",
    "position_id,quantity,price_usd,equities\nA,1,2,nan\n",
    "position_id,quantity,price_usd,equities\nA,1,-2,3\n",
    "position_id,quantity,price_usd,equities\nA,1,2\n",
    "position_id,quantity,price_usd,equities,equities\nA,1,2,3,4\n",
])
def test_rejects_bad_csv(bad):
    with pytest.raises(ValueError):
        read_portfolio_csv(bad)


def test_row_and_byte_limits():
    with pytest.raises(ValueError):
        read_portfolio_csv(SAMPLE, max_rows=1)
    with pytest.raises(ValueError):
        read_portfolio_csv(SAMPLE, max_bytes=5)


def test_stress_attribution_and_history():
    scenarios = evaluate_scenarios([100, -50], ["eq", "rates"], {"selloff": {"eq": -0.2, "rates": 0.01}})
    assert scenarios["selloff"]["pnl"] == pytest.approx(-20.5)
    assert sum(scenarios["selloff"]["factor_pnl"].values()) == pytest.approx(-20.5)
    assert replay_factor_history([100, -50], ["eq", "rates"], [[-0.2, 0.01], [0.1, -0.02]]) == pytest.approx([-20.5, 11])


def test_stress_missing_factor_rejected():
    with pytest.raises(ValueError):
        evaluate_scenarios([1, 2], ["a", "b"], {"bad": {"a": 0.1}})


def test_numeric_overflow_rejected():
    with pytest.raises(ValueError, match="overflow"):
        read_portfolio_csv("position_id,quantity,price_usd,eq\nA,1e308,1e308,1e308\n")


def test_excessive_factor_columns_rejected():
    factors = ",".join(f"factor{i}" for i in range(51))
    values = ",".join("1" for _ in range(51))
    with pytest.raises(ValueError, match="50 factor"):
        read_portfolio_csv(f"position_id,quantity,price_usd,{factors}\nA,1,1,{values}\n")


def test_scenario_overflow_is_rejected():
    portfolio = read_portfolio_csv("position_id,quantity,price_usd,eq\nA,1,1,1e308\n")
    with pytest.raises(ValueError, match="overflow"):
        portfolio.scenario([1e308])


def test_duplicate_position_id_rejected():
    with pytest.raises(ValueError, match="unique"):
        read_portfolio_csv("position_id,quantity,price_usd,eq\nA,1,1,2\nA,1,1,3\n")


def test_stress_rejects_numeric_overflow():
    with pytest.raises(ValueError, match="overflow"):
        evaluate_scenarios([1e308], ["eq"], {"extreme": {"eq": 1e308}})


def test_historical_replay_rejects_numeric_overflow():
    with pytest.raises(ValueError, match="overflow"):
        replay_factor_history([1e308], ["eq"], [[1e308], [0.1]])
