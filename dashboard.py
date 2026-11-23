"""Interactive research dashboard for Fragility Atlas.

Run: pip install -e '.[dashboard]' && streamlit run dashboard.py
Synthetic portfolio data only. Not investment advice.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from fragility_atlas import Model

st.set_page_config(page_title="Fragility Atlas", page_icon="📊", layout="wide")
st.title("Fragility Atlas")
st.caption("Explainable reverse stress testing · Research prototype · Synthetic data")
st.warning("Experimental model. Synthetic inputs and illustrative hedge costs. Not validated for trading or investment decisions.")

DEMO = Path(__file__).resolve().parent / "examples" / "demo.json"


@st.cache_data
def load_demo():
    return json.loads(DEMO.read_text(encoding="utf-8"))


raw = load_demo()
with st.sidebar:
    st.header("Scenario controls")
    loss = st.number_input("Loss threshold (USD)", min_value=1.0, value=1_000_000.0, step=100_000.0)
    radius = st.slider("Hedge uncertainty radius", min_value=0.5, max_value=5.0, value=2.0, step=0.25)
    run_hedge = st.checkbox("Optimize illustrative hedge", value=False)
    st.caption("Distance uses assumed covariance geometry, not calibrated tail probability.")

try:
    model = Model.build(raw["factors"], raw["exposure"], raw["covariance"])
    report = {"reverse_stress": model.reverse_stress(loss)}
    result = report["reverse_stress"]
except (ValueError, KeyError, TypeError) as exc:
    st.error(f"Invalid model input: {exc}")
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Target loss", f"${loss:,.0f}")
c2.metric("Mahalanobis distance", f"{result['mahalanobis_distance']:.3f}")
c3.metric("Scenario P&L", f"${result['pnl']:,.0f}")

st.subheader("Minimum-distance stress scenario")
shocks = pd.DataFrame({
    "Factor": list(result["shock"].keys()),
    "Shock (%)": [v * 100 for v in result["shock"].values()],
})
st.bar_chart(shocks.set_index("Factor"), horizontal=True)
st.dataframe(shocks, hide_index=True, use_container_width=True)

st.subheader("Factor P&L attribution")
attribution = pd.DataFrame({
    "Factor": list(result["factor_pnl_contributions"].keys()),
    "P&L (USD)": list(result["factor_pnl_contributions"].values()),
})
st.bar_chart(attribution.set_index("Factor"), horizontal=True)
st.dataframe(attribution, hide_index=True, use_container_width=True)
st.caption("These are linear scenario contributions, not causal explanations.")

if run_hedge:
    st.subheader("Illustrative hedge optimization")
    try:
        h = raw["hedges"]
        hedge = model.hedge(loss, h["factor_sensitivities"], h["cost_per_unit"], h["names"], radius)
        report["hedge"] = hedge
        a, b = st.columns(2)
        a.metric("Illustrative hedge cost", f"${hedge['estimated_cost']:,.0f}")
        b.metric("Worst ellipsoid loss", f"${hedge['worst_ellipsoid_loss']:,.0f}")
        st.dataframe(pd.DataFrame({
            "Hedge": list(hedge["units"].keys()),
            "Units": list(hedge["units"].values()),
        }), hide_index=True, use_container_width=True)
        st.caption("SLSQP solution; independently validate feasibility, costs and tradability.")
    except (ValueError, RuntimeError, KeyError, TypeError, np.linalg.LinAlgError) as exc:
        st.error(f"Hedge optimization did not complete: {exc}")

st.download_button(
    "Export scenario report (JSON)",
    data=json.dumps(report, indent=2),
    file_name="fragility_atlas_report.json",
    mime="application/json",
)
st.caption("Prototype v0.1.0 · No live prices · No empirical backtesting")
