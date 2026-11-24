"""Fragility Atlas research lab: CSV portfolios, stress, historical risk, diagnostics.

All example observations are synthetic. Uploaded data is processed in session only.
"""
import io
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from fragility_atlas.core import Model
from fragility_atlas.portfolio import read_portfolio_csv
from fragility_atlas.stress import evaluate_scenarios
from fragility_atlas.historical import historical_summary
from fragility_atlas.validation import rolling_historical_var
from fragility_atlas.sensitivity import reverse_stress_sensitivity
from fragility_atlas.reporting import report_json, report_csv, report_pdf

st.set_page_config(page_title="Research Lab | Fragility Atlas", layout="wide")
st.title("Research Lab")
st.caption("Fragility Atlas v1.0 development preview · Linear factors · Research only")
st.warning("Synthetic demonstration by default. Uploaded data is not independently verified; no investment advice.")

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = (ROOT / "examples" / "sample_portfolio.csv").read_text(encoding="utf-8")
st.download_button("Download synthetic portfolio CSV", SAMPLE, "sample_portfolio.csv", "text/csv")
uploaded = st.file_uploader("Upload portfolio CSV (max 2 MB)", type=["csv"])
try:
    if uploaded is None:
        csv_text = SAMPLE
    else:
        if uploaded.size > 2_000_000:
            st.error("Portfolio CSV exceeds the 2 MB limit.")
            st.stop()
        csv_text = uploaded.getvalue().decode("utf-8-sig")
    portfolio = read_portfolio_csv(csv_text)
except (ValueError, UnicodeDecodeError) as exc:
    st.error(f"Portfolio input rejected: {exc}")
    st.stop()

st.metric("Net marked portfolio value (USD)", f"${portfolio.value:,.2f}")
st.dataframe(pd.DataFrame({"factor": portfolio.factors, "USD sensitivity": portfolio.exposure}),
             hide_index=True, use_container_width=True)

st.subheader("Hypothetical stress scenarios")
st.caption("Factor shocks are decimal returns entered as percentages; values are not market forecasts.")
shock = {
    name: st.number_input(f"{name} shock (%)", value=-5.0 if name == "equities" else 0.0,
                          step=0.25, format="%.2f", key=f"lab_{name}") / 100
    for name in portfolio.factors
}
stress = evaluate_scenarios(portfolio.exposure, portfolio.factors, {"custom": shock})["custom"]
st.metric("Linear scenario P&L (USD)", f"${stress['pnl']:,.2f}")
st.dataframe(pd.DataFrame({"factor": list(stress["factor_pnl"]),
                           "P&L (USD)": list(stress["factor_pnl"].values())}),
             hide_index=True, use_container_width=True)

st.subheader("Historical risk and VaR coverage")
st.caption("Upload one chronological daily simple-return column in decimal units, e.g. -0.02 for -2%.")
returns_file = st.file_uploader("Upload historical returns CSV (max 2 MB)", type=["csv"], key="returns")
if returns_file is None:
    # Fixed-seed synthetic illustration; NOT a real market time series.
    rng = np.random.default_rng(20261124)
    returns = rng.normal(0.0002, 0.012, 600)
    source = "Fixed-seed synthetic normal draws"
else:
    if returns_file.size > 2_000_000:
        st.error("Returns CSV exceeds the 2 MB limit.")
        st.stop()
    try:
        df = pd.read_csv(io.BytesIO(returns_file.getvalue()))
        if df.shape[1] != 1:
            raise ValueError("CSV must contain exactly one return column")
        returns = pd.to_numeric(df.iloc[:, 0], errors="raise").to_numpy(dtype=float)
        source = "User-supplied CSV (unverified)"
    except (ValueError, pd.errors.ParserError, UnicodeDecodeError) as exc:
        st.error(f"Returns CSV rejected: {exc}")
        st.stop()
st.caption(f"Source: {source}")
confidence = st.selectbox("VaR confidence", [0.95, 0.975, 0.99], index=2)
value = st.number_input("Risk notional (USD)", min_value=1.0, value=1_000_000.0)
try:
    summary = historical_summary(returns, confidence, value)
    c1, c2, c3 = st.columns(3)
    c1.metric("Historical VaR", f"${summary['var']:,.0f}")
    c2.metric("Expected shortfall", f"${summary['expected_shortfall']:,.0f}")
    c3.metric("Maximum drawdown", f"{summary['maximum_drawdown']:.2%}")
    st.line_chart(pd.DataFrame({"Compounded wealth": np.r_[1.0, np.cumprod(1 + returns)]}))
    if len(returns) >= 40:
        window = st.number_input("Backtest lookback observations", min_value=20,
                                 max_value=len(returns)-20, value=min(250, len(returns)-20))
        backtest = rolling_historical_var(returns, int(window), confidence, value)
        cov = backtest["coverage"]
        st.write(f"VaR breaches: {cov['exceedances']} of {cov['observations']}; "
                 f"Kupiec asymptotic p-value: {cov['p_value_chi2_1df']:.4f}")
        st.caption("The coverage test does not establish predictive accuracy or independence. "
                   "Very few expected breaches make the chi-square approximation unreliable.")
    else:
        backtest = None
        st.info("At least 40 observations are needed for the rolling backtest here.")
except (ValueError, TypeError) as exc:
    st.error(f"Historical risk calculation unavailable: {exc}")
    st.stop()

st.subheader("Reverse-stress sensitivity")
st.caption("Assumed diagonal factor covariance for demonstration only; not estimated from uploaded returns.")
vol = st.number_input("Assumed per-factor volatility (%)", min_value=0.01,
                      max_value=100.0, value=2.0, step=0.25) / 100
target = st.number_input("Target loss (USD)", min_value=1.0, value=100_000.0, step=10_000.0)
try:
    if not np.any(portfolio.exposure):
        st.info("Sensitivity requires a nonzero net factor exposure.")
        sensitivity = []
    else:
        model = Model.build(portfolio.factors, portfolio.exposure,
                            np.eye(len(portfolio.factors)) * vol ** 2)
        sensitivity = reverse_stress_sensitivity(model, target)
        st.dataframe(pd.DataFrame([{k: v for k, v in row.items() if k != "shock"}
                                   for row in sensitivity]), hide_index=True, use_container_width=True)
except (ValueError, np.linalg.LinAlgError) as exc:
    st.error(f"Sensitivity calculation unavailable: {exc}")
    sensitivity = []

report = {"metadata": {"app": "Fragility Atlas Research Lab",
                       "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                       "risk_conventions": "one-period empirical VaR (higher order statistic), fractional-tail ES; daily simple returns",
                       "factor_covariance": "illustrative independent factors with user-assumed identical volatility",
                       "source": source,
                       "portfolio_source": "synthetic example" if uploaded is None else "user-supplied CSV",
                       "limitations": "linear factors; no live data; no verified market calibration"},
          "portfolio": {"factor_names": portfolio.factors, "value": portfolio.value,
                        "exposure": portfolio.exposure.tolist()},
          "stress": stress, "historical": summary, "coverage": backtest,
          "sensitivity": sensitivity}
st.subheader("Export reproducible report")
st.caption("Exports include source labels, numerical results, and model limitations.")
st.download_button("Download JSON", report_json(report),
                   file_name="fragility_atlas_research_lab.json", mime="application/json")
st.download_button("Download CSV", report_csv(report),
                   file_name="fragility_atlas_research_lab.csv", mime="text/csv")
try:
    pdf_bytes = report_pdf(report)
    st.download_button("Download PDF", pdf_bytes,
                       file_name="fragility_atlas_research_lab.pdf", mime="application/pdf")
except (ValueError, ImportError) as exc:
    st.warning(f"PDF report unavailable: {exc}")
st.caption("Research prototype. Diagnostics and historical summaries are not investment recommendations.")
