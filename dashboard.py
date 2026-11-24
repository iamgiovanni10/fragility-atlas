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
from fragility_atlas.workbench import hedge_diagnostics, scenario_pnl, scenario_comparison

st.set_page_config(page_title="Fragility Atlas", page_icon="📊", layout="wide")
st.title("Fragility Atlas")
st.caption("Scenario Intelligence v0.3 · Explainable reverse stress testing · Synthetic data")
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

tabs = st.tabs(["Risk Overview", "Scenario Explorer", "Hedge Analysis", "Validation & Reports"])
with tabs[0]:
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

with tabs[1]:
    st.subheader("Scenario Explorer")
    st.caption("Enter hypothetical factor shocks in percent. This is a linear sensitivity calculator, not a forecast.")
    shock_inputs = []
    for name in model.names:
        shock_inputs.append(st.number_input(f"{name} shock (%)", value=0.0, step=0.25, format="%.3f") / 100)
    manual_pnl = scenario_pnl(model.exposure, shock_inputs)
    st.metric("Hypothetical scenario P&L (unhedged)", f"${manual_pnl:,.0f}")
    comparison = scenario_comparison(model.exposure, model.covariance, shock_inputs, radius)
    st.metric("Scenario Mahalanobis distance", f"{comparison['mahalanobis_distance']:.3f}")
    if comparison["inside_uncertainty_set"]:
        st.success("Scenario is inside the selected covariance ellipsoid (geometric classification only).")
    else:
        st.warning("Scenario is OUTSIDE the selected covariance ellipsoid. The hedge worst-loss cap does not apply to this shock.")
    if run_hedge:
        try:
            hedges = raw["hedges"]
            scenario_hedge = model.hedge(loss, hedges["factor_sensitivities"], hedges["cost_per_unit"], hedges["names"], radius)
            ordered_units = [scenario_hedge["units"][name] for name in hedges["names"]]
            comparison = scenario_comparison(
                model.exposure, model.covariance, shock_inputs, radius,
                hedges["factor_sensitivities"], ordered_units
            )
            a, b = st.columns(2)
            a.metric("Same-scenario P&L before hedge", f"${comparison['before_pnl']:,.0f}")
            b.metric("Same-scenario P&L after hedge", f"${comparison['after_pnl']:,.0f}",
                     delta=f"${comparison['pnl_change']:,.0f} change")
            st.caption("This compares identical shocks, using synthetic linear exposures. It does not include hedge costs in scenario P&L.")
        except (ValueError, RuntimeError, KeyError, TypeError, np.linalg.LinAlgError) as exc:
            st.error(f"Scenario hedge comparison unavailable: {exc}")
    st.dataframe(pd.DataFrame({
        "Factor": model.names,
        "Shock (%)": np.asarray(shock_inputs) * 100,
        "P&L (USD)": model.exposure * np.asarray(shock_inputs),
    }), hide_index=True, use_container_width=True)
    report["manual_scenario"] = {"shocks": dict(zip(model.names, shock_inputs)), "pnl": manual_pnl, "comparison": comparison}

with tabs[2]:
    st.subheader("Hedge Analysis")
    if not run_hedge:
        st.info("Enable 'Optimize illustrative hedge' in the sidebar to calculate hedge positions.")
    else:
        try:
            h = raw["hedges"]
            hedge = model.hedge(loss, h["factor_sensitivities"], h["cost_per_unit"], h["names"], radius)
            diagnostics = hedge_diagnostics(model, hedge, h["factor_sensitivities"], loss, radius)
            report["hedge"] = hedge
            report["validation"] = diagnostics
            a, b, c = st.columns(3)
            a.metric("Illustrative hedge cost", f"${hedge['estimated_cost']:,.0f}")
            b.metric("Worst loss before hedge", f"${diagnostics['before_worst_loss']:,.0f}")
            c.metric("Worst loss after hedge", f"${diagnostics['after_worst_loss']:,.0f}")
            st.bar_chart(pd.DataFrame({"Worst-case loss (USD)": [diagnostics["before_worst_loss"], diagnostics["after_worst_loss"]]}, index=["Before hedge", "After hedge"]))
            st.dataframe(pd.DataFrame({
                "Hedge": list(hedge["units"].keys()),
                "Units": [0.0 if abs(v) < 1e-8 else round(v, 4) for v in hedge["units"].values()],
            }), hide_index=True, use_container_width=True)
            st.caption("Synthetic instruments and costs. Solver output requires independent validation.")
        except (ValueError, RuntimeError, KeyError, TypeError, np.linalg.LinAlgError) as exc:
            st.error(f"Hedge optimization did not complete: {exc}")

with tabs[3]:
    st.subheader("Model Validation & Reports")
    st.write("Reverse stress P&L residual:", f"${abs(result['pnl'] + loss):,.8f}")
    st.write("Factor contributions residual:", f"${abs(sum(result['factor_pnl_contributions'].values()) - result['pnl']):,.8f}")
    if "validation" in report:
        v = report["validation"]
        st.write("Hedge constraint satisfied:", v["constraint_satisfied"])
        st.write("Hedge constraint slack:", f"${v['constraint_slack']:,.4f}")
        st.write("Recomputed vs reported worst-loss difference:", f"${v['max_recomputed_vs_reported_error']:,.8f}")
    else:
        st.info("Enable hedge optimization to display hedge diagnostics.")
    st.download_button("Export research report (JSON)", data=json.dumps(report, indent=2),
                       file_name="fragility_atlas_report.json", mime="application/json")
    st.caption("Diagnostics check arithmetic and constraints, not empirical model accuracy.")

st.caption("Scenario Intelligence v0.3 · Synthetic inputs · No calibrated probabilities or live prices")
