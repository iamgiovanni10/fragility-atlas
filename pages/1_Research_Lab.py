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
from fragility_atlas.stress import evaluate_scenarios, replay_factor_history
from fragility_atlas.factor_history import read_factor_history_csv
from fragility_atlas.historical import historical_summary
from fragility_atlas.validation import rolling_historical_var
from fragility_atlas.sensitivity import reverse_stress_sensitivity
from fragility_atlas.reporting import report_json, report_csv, report_pdf
from fragility_atlas.provenance import sha256_input_bytes

st.set_page_config(page_title="Research Lab | Fragility Atlas", layout="wide")
st.title("Research Lab")
st.sidebar.markdown("### Research modules")
for label, target in [
    ("Portfolio overview", "portfolio-overview"),
    ("Stress testing", "hypothetical-stress-scenarios"),
    ("Scenario comparison", "scenario-comparison"),
    ("Historical replay", "historical-factor-shock-replay"),
    ("Historical risk & coverage", "historical-risk-and-var-coverage"),
    ("Reverse stress", "reverse-stress-sensitivity"),
    ("Report exports", "export-reproducible-report"),
]:
    st.sidebar.markdown(f"[{label}](#{target})")

st.caption("Fragility Atlas v1.0 development preview · Linear factors · Research only")
st.warning("Synthetic demonstration by default. Uploaded data is not independently verified; no investment advice.")

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = (ROOT / "examples" / "sample_portfolio.csv").read_text(encoding="utf-8")
st.download_button("Download synthetic portfolio CSV", SAMPLE, "sample_portfolio.csv", "text/csv")
uploaded = st.file_uploader("Upload portfolio CSV (max 2 MB)", type=["csv"])
try:
    if uploaded is None:
        csv_text = SAMPLE
        portfolio_bytes = SAMPLE.encode("utf-8")
    else:
        if uploaded.size > 2_000_000:
            st.error("Portfolio CSV exceeds the 2 MB limit.")
            st.stop()
        portfolio_bytes = uploaded.getvalue()
        csv_text = portfolio_bytes.decode("utf-8-sig")
    portfolio = read_portfolio_csv(csv_text)
    portfolio_sha256 = sha256_input_bytes(portfolio_bytes)
except (ValueError, UnicodeDecodeError) as exc:
    st.error(f"Portfolio input rejected: {exc}")
    st.stop()

st.subheader("Portfolio overview")
st.caption("Marked value and linear factor sensitivities from the selected portfolio.")
a, b = st.columns(2)
a.metric("Net marked portfolio value (USD)", f"${portfolio.value:,.2f}")
b.metric("Risk factors", len(portfolio.factors))
st.dataframe(pd.DataFrame({"factor": portfolio.factors, "USD sensitivity": portfolio.exposure}),
             hide_index=True, use_container_width=True)

st.subheader("Hypothetical stress scenarios")
st.caption("Factor shocks are decimal returns entered as percentages; values are not market forecasts.")
shock = {
    name: st.number_input(f"{name} shock (%)", value=-5.0 if name == "equities" else 0.0,
                          step=0.25, format="%.2f", key=f"lab_{name}") / 100
    for name in portfolio.factors
}
try:
    stress = evaluate_scenarios(portfolio.exposure, portfolio.factors, {"custom": shock})["custom"]
    position_attribution = portfolio.scenario([shock[name] for name in portfolio.factors])
except (ValueError, OverflowError) as exc:
    st.error(f"Scenario calculation rejected: {exc}")
    st.stop()
if not np.isclose(stress["pnl"], position_attribution["total_pnl"], rtol=1e-10, atol=1e-6):
    st.error("Factor and position attribution do not reconcile.")
    st.stop()
st.metric("Linear scenario P&L (USD)", f"${stress['pnl']:,.2f}")
st.dataframe(pd.DataFrame({"factor": list(stress["factor_pnl"]),
                           "P&L (USD)": list(stress["factor_pnl"].values())}),
             hide_index=True, use_container_width=True)

st.caption("Position-level P&L attribution (same scenario)")
st.dataframe(pd.DataFrame({"position": list(position_attribution["position_pnl"]),
                           "P&L (USD)": list(position_attribution["position_pnl"].values())}),
             hide_index=True, use_container_width=True)

st.subheader("Scenario comparison")
st.caption("Illustrative hypothetical shocks, not reconstructions of named historical crises.")
preset_definitions = {
    "Broad risk-off (illustrative)": {"equities": -0.15, "rates": -0.01, "credit_spreads": 0.02},
    "Rates up (illustrative)": {"equities": -0.04, "rates": 0.02, "credit_spreads": 0.005},
    "Credit widening (illustrative)": {"equities": -0.07, "rates": 0.0, "credit_spreads": 0.03},
}
comparison_inputs = {"Custom": shock}
for scenario_name, preset in preset_definitions.items():
    comparison_inputs[scenario_name] = {
        factor: preset.get(factor, 0.0) for factor in portfolio.factors
    }
try:
    comparisons = evaluate_scenarios(portfolio.exposure, portfolio.factors, comparison_inputs)
except (ValueError, OverflowError) as exc:
    st.error(f"Scenario comparison rejected: {exc}")
    st.stop()
comparison_rows = []
for scenario_name, result in comparisons.items():
    pct = None
    if abs(portfolio.value) > 1e-12:
        with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
            candidate = (result["pnl"] / abs(portfolio.value)) * 100.0
        if np.isfinite(candidate):
            pct = float(candidate)
    comparison_rows.append({
        "scenario": scenario_name,
        "pnl_usd": result["pnl"],
        "pnl_pct_of_abs_net_value": pct,
    })
left, right = st.columns([3, 2])
with left:
    st.bar_chart(pd.DataFrame(comparison_rows).set_index("scenario")["pnl_usd"], horizontal=True)
with right:
    st.dataframe(pd.DataFrame(comparison_rows), hide_index=True, use_container_width=True)
st.caption("Unrecognized factors receive zero shock in the illustrative presets. "
           "Percentage P&L uses absolute net marked value; it is omitted when net value is near zero or the ratio is not finite.")

st.subheader("Historical factor-shock replay")
st.caption("Upload chronological factor shocks in decimal units, one column per portfolio factor. "
           "These must be independently sourced if interpreted as historical market observations.")
factor_history_file = st.file_uploader("Factor history CSV (max 2 MB)", type=["csv"],
                                      key="factor_history")
replay = None
factor_history_sha256 = None
if factor_history_file is not None:
    try:
        if factor_history_file.size > 2_000_000:
            raise ValueError("Factor history CSV exceeds 2 MB")
        factor_history_bytes = factor_history_file.getvalue()
        factor_history = read_factor_history_csv(
            factor_history_bytes.decode("utf-8-sig"), portfolio.factors
        )
        factor_history_sha256 = sha256_input_bytes(factor_history_bytes)
        replay = replay_factor_history(portfolio.exposure, portfolio.factors, factor_history)
        st.line_chart(pd.DataFrame({"Scenario P&L (USD)": replay}))
        st.metric("Worst observed replay P&L (USD)", f"${min(replay):,.2f}")
        st.caption("Fixed linear exposures; rows are observations, not independently verified crisis dates.")
    except (ValueError, UnicodeDecodeError) as exc:
        st.error(f"Historical factor replay rejected: {exc}")

st.subheader("Historical risk and VaR coverage")
st.caption("Upload one chronological daily simple-return column in decimal units, e.g. -0.02 for -2%.")
returns_file = st.file_uploader("Upload historical returns CSV (max 2 MB)", type=["csv"], key="returns")
if returns_file is None:
    # Fixed-seed synthetic illustration; NOT a real market time series.
    rng = np.random.default_rng(20261124)
    returns = rng.normal(0.0002, 0.012, 600)
    source = "Fixed-seed synthetic normal draws"
    returns_sha256 = sha256_input_bytes(returns.tobytes())
else:
    if returns_file.size > 2_000_000:
        st.error("Returns CSV exceeds the 2 MB limit.")
        st.stop()
    try:
        returns_bytes = returns_file.getvalue()
        df = pd.read_csv(io.BytesIO(returns_bytes))
        if df.shape[1] != 1:
            raise ValueError("CSV must contain exactly one return column")
        if len(df) > 10000:
            raise ValueError("Returns CSV exceeds 10,000 observations")
        returns = pd.to_numeric(df.iloc[:, 0], errors="raise").to_numpy(dtype=float)
        source = "User-supplied CSV (unverified)"
        returns_sha256 = sha256_input_bytes(returns_bytes)
    except (ValueError, pd.errors.ParserError, UnicodeDecodeError, pd.errors.EmptyDataError) as exc:
        st.error(f"Returns CSV rejected: {exc}")
        st.stop()
st.caption(f"Source: {source}")
confidence = st.selectbox("VaR confidence", [0.95, 0.975, 0.99], index=2)
value = st.number_input("Risk notional (USD)", min_value=1.0, value=1_000_000.0)
try:
    summary = historical_summary(returns, confidence, value)
    c1, c2, c3, c4 = st.columns(4)
    c4.metric("Annualized volatility", f"{summary['annualized_volatility']:.2%}")
    c1.metric("Historical VaR", f"${summary['var']:,.0f}")
    c2.metric("Expected shortfall", f"${summary['expected_shortfall']:,.0f}")
    c3.metric("Maximum drawdown", f"{summary['maximum_drawdown']:.2%}")
    wealth = np.r_[1.0, np.cumprod(1 + returns)]
    drawdown = wealth / np.maximum.accumulate(wealth) - 1.0
    left, right = st.columns(2)
    with left:
        st.markdown("#### Compounded wealth")
        st.line_chart(pd.DataFrame({"Wealth multiple": wealth}))
    with right:
        st.markdown("#### Drawdown history")
        st.area_chart(pd.DataFrame({"Drawdown (%)": 100 * drawdown}))
    st.caption(f"Maximum drawdown: peak observation {summary['peak_index']}, "
               f"trough observation {summary['trough_index']}. "
               "Observation 0 is the initial wealth; indices are not calendar dates.")
    if len(returns) >= 40:
        window = st.number_input("Backtest lookback observations", min_value=20,
                                 max_value=len(returns)-20, value=min(250, len(returns)-20))
        backtest = rolling_historical_var(returns, int(window), confidence, value)
        cov = backtest["coverage"]
        st.markdown("#### Out-of-sample VaR backtest")
        losses = np.asarray(backtest["realized_losses"])
        forecasts = np.asarray(backtest["forecast_vars"])
        breaches = losses > forecasts
        chart_data = pd.DataFrame({
            "Realized loss (USD)": losses,
            "VaR forecast (USD)": forecasts,
        }, index=pd.Index(np.arange(int(window) + 1, len(returns) + 1),
                          name="Observation"))
        st.line_chart(chart_data)
        st.caption("Positive values represent losses. Each forecast uses only preceding observations.")
        observed = chart_data.loc[breaches].reset_index()
        if not observed.empty:
            st.markdown("**VaR exceedances**")
            st.dataframe(observed, hide_index=True, use_container_width=True)
        else:
            st.info("No strict VaR exceedances in this holdout sample.")

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
                       "risk_conventions": "one-period empirical inverse-CDF VaR, fractional-tail ES; daily simple returns",
                       "portfolio_input_sha256": portfolio_sha256,
                       "returns_input_sha256": returns_sha256,
                       "factor_history_input_sha256": factor_history_sha256,
                       "synthetic_returns_seed": 20261124 if returns_file is None else None,
                       "factor_covariance": "illustrative independent factors with user-assumed identical volatility",
                       "source": source,
                       "portfolio_source": "synthetic example" if uploaded is None else "user-supplied CSV",
                       "limitations": "linear factors; no live data; no verified market calibration"},
          "portfolio": {"factor_names": portfolio.factors, "value": portfolio.value,
                        "exposure": portfolio.exposure.tolist()},
          "stress": stress, "scenario_comparison": comparisons,
          "historical_factor_replay": replay,
          "position_attribution": position_attribution,
          "historical": summary, "coverage": backtest,
          "sensitivity": sensitivity}
st.subheader("Export reproducible report")
st.caption("Exports include source labels, numerical results, and model limitations.")
st.download_button("Download JSON", report_json(report),
                   file_name="fragility_atlas_research_lab.json", mime="application/json", on_click="ignore")
st.download_button("Download CSV", report_csv(report),
                   file_name="fragility_atlas_research_lab.csv", mime="text/csv", on_click="ignore")
try:
    pdf_bytes = report_pdf(report)
    st.download_button("Download PDF", pdf_bytes,
                       file_name="fragility_atlas_research_lab.pdf", mime="application/pdf", on_click="ignore")
except (ValueError, ImportError) as exc:
    st.warning(f"PDF report unavailable: {exc}")
st.caption("Research prototype. Diagnostics and historical summaries are not investment recommendations.")
