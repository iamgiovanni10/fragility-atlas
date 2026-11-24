"""End-to-end default research-lab smoke test using Streamlit's testing harness."""
from pathlib import Path

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]


def test_research_lab_default_synthetic_journey():
    app = AppTest.from_file(str(ROOT / "pages" / "1_Research_Lab.py"),
                            default_timeout=60).run()
    assert not app.exception, [str(x.message) for x in app.exception]
    assert any("Research Lab" in str(x.value) for x in app.title)
    assert any("Historical VaR" in str(x.label) for x in app.metric)
    assert any("Maximum drawdown" in str(x.label) for x in app.metric)


def test_research_lab_scenario_comparison_and_exports():
    app = AppTest.from_file(str(ROOT / "pages" / "1_Research_Lab.py"),
                            default_timeout=60).run()
    assert not app.exception, [str(x.message) for x in app.exception]
    assert any("Scenario comparison" in str(x.value) for x in app.subheader)
    assert any("Export reproducible report" in str(x.value) for x in app.subheader)
    # AppTest exposes metric widgets; check the scenario P&L is calculated.
    assert any("Linear scenario P&L" in str(x.label) for x in app.metric)


def test_research_lab_custom_equities_shock_changes_pnl():
    app = AppTest.from_file(str(ROOT / "pages" / "1_Research_Lab.py"),
                            default_timeout=60).run()
    assert not app.exception, [str(x.message) for x in app.exception]
    before = next(str(x.value) for x in app.metric if x.label == "Linear scenario P&L (USD)")
    equities = next(x for x in app.number_input if x.label == "equities shock (%)")
    equities.set_value(-10.0)
    app.run()
    assert not app.exception, [str(x.message) for x in app.exception]
    after = next(str(x.value) for x in app.metric if x.label == "Linear scenario P&L (USD)")
    assert before != after
