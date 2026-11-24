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
