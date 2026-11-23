# Fragility Atlas — Explainable Reverse Stress Testing

**Research prototype** for the question: *What is the smallest joint market-factor shock that creates a defined portfolio loss, and what is an inexpensive hedge against a bounded shock set?*

## Why this matters

Traditional stress tests answer **“what happens under scenario X?”** Fragility Atlas answers **“what scenario is sufficient to exceed our loss limit?”** and provides factor-level P&L attribution. A second module searches for an affordable hedge against all shocks in an ellipsoidal uncertainty region. Reverse stress testing is established in academic literature: this project does **not** claim to invent it.

## Install / run

```bash
python -m pip install -e '.[dev]'
pytest -q
fragility-atlas examples/demo.json --loss 1000000
fragility-atlas examples/demo.json --loss 1000000 --hedge --radius 2
```

## Model

Let `b` be the vector of dollar P&L per unit return, `Σ` the symmetric positive definite risk-factor covariance, and `x` the factor-return shock. Under a **linear** valuation, P&L is `bᵀx`. Solve:

`min_x xᵀΣ⁻¹x  subject to bᵀx <= -L`

Closed form: `x* = -L Σ b / (bᵀΣb)`, with distance `L / sqrt(bᵀΣb)`.

For hedge sensitivities `H` and units `h`, robust (ellipsoidal) loss at radius `r` is `r sqrt((b+Hh)ᵀΣ(b+Hh))`. The hedge optimizer searches for low-cost positions under a loss cap. These **ellipsoids are assumptions**, not probabilistic confidence guarantees.

## Limitations and required validation

- **No trading advice.** Entirely synthetic demo inputs and illustrative hedge costs.
- Linear factor exposures only; no options gamma, nonlinear defaults, basis risk, liquidity feedback, slippage, dynamic hedging, regime switches, or causal inference.
- Gaussian geometry is a risk metric, not a calibrated likelihood; historical tails may be heavier or correlations may shift.
- Hedging uses SLSQP, a numerical solver; failure or success is not a formal global optimality certificate. Verify solver results, market feasibility, constraints, and prices before any use.
- Positive definite covariance and consistent factor units are mandatory; a production system needs data provenance, missing-data policy, backtesting, drift detection, independent validation, audit logging, and oversight.

## Research roadmap

1. Time-aligned market data ingestion with immutable snapshots and documented legal licenses.
2. Historical and forward-looking macro/credit/rates/FX factor models with out-of-sample regime evaluation.
3. Robust uncertainty sets beyond Gaussian ellipsoids (Wasserstein distributional robustness, EVT tail calibration) and certified convex hedge optimization.
4. Nonlinear instrument repricing (fixed income, derivatives), counterparty-credit and funding stress.
5. Network spillovers and endogenous asset fire sales; model uncertainty and causality caveats.
6. Counterfactual explanation reports with reproducible provenance and model-governance approval workflow.

## Prior research

- Crépey et al., *Quantitative reverse stress testing, bottom up* (2023): https://doi.org/10.1080/14697688.2023.2187315
- *Reverse stress testing: Scenario design for macroprudential stress tests*: https://doi.org/10.1111/mafi.12373
- Related open-source engines: https://github.com/octarisk/octarisk and https://github.com/fortitudo-tech/fortitudo.tech

## License

MIT — see LICENSE.
