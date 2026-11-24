"""End-to-end numerical consistency checks across research modules."""
import numpy as np
import pytest

from fragility_atlas.portfolio import read_portfolio_csv
from fragility_atlas.stress import evaluate_scenarios, replay_factor_history
from fragility_atlas.factor_history import read_factor_history_csv
from fragility_atlas.historical import historical_summary
from fragility_atlas.reporting import report_json, report_csv, report_pdf


PORTFOLIO = """position_id,quantity,price_usd,eq,rates
STOCK,10,100,1000,-100
BOND,5,200,100,200
"""
HISTORY = """rates,eq
0.01,-0.05
-0.01,0.02
0.005,-0.08
"""


def test_full_portfolio_to_stress_to_replay_to_report():
    portfolio = read_portfolio_csv(PORTFOLIO)
    shocks = {"eq": -0.05, "rates": 0.01}
    scenario = evaluate_scenarios(portfolio.exposure, portfolio.factors,
                                  {"risk_off": shocks})["risk_off"]
    position_result = portfolio.scenario([shocks[f] for f in portfolio.factors])
    assert scenario["pnl"] == pytest.approx(position_result["total_pnl"])
    assert sum(position_result["position_pnl"].values()) == pytest.approx(scenario["pnl"])

    history = read_factor_history_csv(HISTORY, portfolio.factors)
    replay = replay_factor_history(portfolio.exposure, portfolio.factors, history)
    assert replay[0] == pytest.approx(scenario["pnl"])
    assert len(replay) == 3

    summary = historical_summary([-0.02, 0.01, -0.03, 0.015], confidence=0.75)
    report = {"metadata": {"source": "test fixture", "limitations": "synthetic"},
              "portfolio": {"value": portfolio.value, "exposure": portfolio.exposure.tolist()},
              "historical": summary, "stress": scenario, "replay": replay}
    assert '"risk_off"' not in report_json(report)  # scenario payload has no scenario label
    assert "historical.var" in report_csv(report)
    assert report_pdf(report).startswith(b"%PDF")
