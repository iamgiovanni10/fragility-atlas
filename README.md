# Fragility Atlas

**Quantitative Portfolio Risk & Resilience Research Platform**

> **Release status:** v1.0.0rc1 — release candidate on `release/v1-comprehensive`, **not yet released**. The public deployment may still run the older v0.3 Risk Workbench. Do not interpret a successful CI run as proof of deployed functionality or independent model validation.

Fragility Atlas is an open-source, AI-assisted **quantitative-finance research prototype** built around interpretable linear factor exposures. It is not a live market-data platform, a trading system, or investment advice.

## Release-candidate capabilities

| Module | Implemented research functionality | Key limitation |
| --- | --- | --- |
| Portfolio analytics | CSV holdings, marked value, factor sensitivities, position/factor P&L reconciliation | Linear sensitivities; user-supplied inputs |
| Historical risk | Empirical VaR, fractional-tail expected shortfall, compounded drawdown, volatility | User-provided returns or synthetic seeded sample |
| Stress testing | Custom and illustrative preset scenarios, factor attribution, historical factor-shock CSV replay | Presets are not named historical crises |
| Reverse stress | Analytic minimum Mahalanobis-distance adverse scenario | Distance is not an estimated probability |
| Robust hedging | Illustrative cost-minimizing SLSQP hedge, independent feasibility diagnostics | No global optimality certificate or executable market prices |
| Scenario intelligence | Same-scenario hedged/unhedged P&L, uncertainty-set membership warning | Linear factor model |
| Validation | Rolling out-of-sample historical VaR coverage diagnostic | Kupiec asymptotic test is not a certification |
| Sensitivity | Reverse-stress sensitivity to modeled covariance/exposure assumptions | Synthetic or assumed covariance |
| Dashboard | Risk Workbench and separate Research Lab Streamlit page | Browser deployment acceptance pending |
| Reports | JSON, CSV and PDF research exports, UTC timestamps and input SHA-256 fingerprints | Download UX and staging deployment pending acceptance |

## Run locally

```bash
python -m pip install -e '.[dev,dashboard]'
python -m pytest -q
streamlit run dashboard.py
```

The Risk Workbench remains accessible from the dashboard. The Research Lab is in `pages/1_Research_Lab.py`. Download its synthetic sample portfolio, apply hypothetical factor shocks, optionally upload historical factor shocks and daily returns, and export a report.

Command-line demo:

```bash
fragility-atlas examples/demo.json --loss 1000000
fragility-atlas examples/demo.json --loss 1000000 --hedge --radius 2
```

## Reproducibility and data conventions

- Portfolio CSV: `position_id,quantity,price_usd,<factor columns...>`; factor sensitivities are USD P&L per unit decimal factor shock.
- Historical returns CSV: one column of chronological **daily simple decimal returns** (e.g. `-0.02` is -2%).
- Historical factor replay CSV: exactly the portfolio's factor columns; rows are chronological **decimal shocks**.
- VaR: empirical inverse-CDF order statistic; expected shortfall: fractional-tail average. These are one-period measures, not automatically annualized.
- Synthetic returns use a fixed random seed; reports label source assumptions and include input hashes. An input fingerprint verifies exact bytes, not authenticity or market provenance.

See [Research Lab documentation](docs/RESEARCH_LAB.md), [mathematical methodology](docs/METHODOLOGY.md), [release acceptance contract](docs/V1_RELEASE_ACCEPTANCE.md), and [deployment checklist](docs/RELEASE_DEPLOYMENT_CHECKLIST.md).

## Scientific boundaries and release gates

This project has **no independently verified market calibration or institutional model validation**. The hedge optimizer is SLSQP with feasibility checks, not a globally certified convex optimizer. Historical return-risk and factor-stress inputs are not automatically reconciled. VaR backtest p-values can be unreliable with few breaches. No nonlinear repricing, trading integration, or verified live pricing is provided.

Before v1.0 is released, verify CI for the exact release commit, staging navigation, real browser downloads, responsive layout, deployment configuration, and public smoke tests. Do not merge or tag the release candidate before these gates pass.

## Development and AI assistance

The implementation, tests and documentation were developed with substantial AI assistance under the project owner's direction. Numerical outputs and claims require independent review before consequential use.

## License

MIT — see [LICENSE](LICENSE).

---

