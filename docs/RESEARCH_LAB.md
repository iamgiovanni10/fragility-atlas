# Research Lab — v1.0 development preview

Run from repository root:

```bash
python -m pip install -e '.[dashboard,dev]'
streamlit run dashboard.py
```

Use the **Research Lab** page in Streamlit navigation. The Dashboard provides the reverse-stress and hedging workbench. The Research Lab sidebar provides section shortcuts.

## Data contracts

**Portfolio CSV**: `position_id,quantity,price_usd` plus one or more factor sensitivity columns. Factor sensitivity is USD P&L per unit held for a decimal factor shock of 1.0. The bundled sample is synthetic. File size limit is 2 MB and row count limit is 10,000.

**Historical returns CSV**: exactly one column with a header and chronological simple daily returns in decimals, such as `-0.02` for -2%. The default synthetic sample uses a fixed random seed. Uploaded returns are not checked against an external data source.

**Risk metrics**: empirical VaR and fractional-tail expected shortfall are single-period dollar losses, not annualized. Drawdown uses compounded wealth. Backtesting uses only preceding returns; Kupiec's test does not establish model validity.

**Sensitivity**: a diagonal covariance matrix with an explicitly selected volatility is an illustrative assumption, **not** estimated from uploaded portfolio or return data.

## Historical factor replay

Upload a CSV with one column per portfolio factor (exactly matching names), and at least two chronological observations. Each cell is a decimal factor shock. Columns may be reordered: the loader explicitly aligns them to portfolio factor names. The importer rejects malformed, nonfinite, oversized, or mismatched files. The dashboard computes fixed-exposure linear P&L for each observation, charts the series, and reports the worst observed replay P&L. This is **not** a reconstruction of historical crises unless the user supplies independently verified factor observations and provenance. It does not automatically source market data.

## Scenario comparison

The Research Lab evaluates the custom scenario alongside three explicitly **illustrative** presets: broad risk-off, rates up, and credit widening. Presets are not historical crisis replays. Factors not recognized by a preset receive zero shock. The table reports USD P&L and, when net marked portfolio value is nonzero, P&L divided by its absolute value. Factor and position P&L must reconcile or the page stops with an error. The comparison is included in exported reports.

## Important limitations

- The portfolio's marked value and the historical risk notional are separate inputs. The return series is not automatically reconciled to imported holdings.
- No claim of live prices, empirical portfolio calibration, executable hedge instruments, or production-grade risk estimates.
- The historical risk engine currently accepts aggregate return series, not multi-asset price history.
- Uploaded CSVs are processed by the Streamlit server in the active session; do not upload confidential information to an untrusted deployment.
- The Research Lab is a **development preview**, not evidence that the v1.0 release criteria are complete.

## Historical visualizations and exports

Compounded wealth starts at observation zero with wealth 1. Drawdown is wealth divided by its running maximum minus one. Peak and trough indices are observation numbers, not dates. Rolling VaR charts compare realized dollar losses with forecasts computed exclusively from preceding observations. The exceedance table uses a strict realized loss > forecast rule.

JSON and CSV retain the full observation arrays. The PDF uses the research-summary-v2 format: executive summary, scenario table and chart, and detailed provenance, omitting observation-level backtest and replay arrays. The interface and report metadata expose the installed package version and report format; neither identifies the exact deployed Git commit. Input SHA-256 fingerprints establish byte-level identity, not authenticity.

## Staging acceptance

Verify the package version and report format in the Research Lab caption. Change the synthetic equities shock from -5% to -10% with other shocks zero: P&L should change from -26,100 USD to -52,200 USD. Verify navigation, drawdown and VaR charts, and all three downloads. Open the PDF and confirm the executive summary and scenario chart are present. Check desktop and narrow viewport layouts before approving release. Do not confuse local Chromium CI with a verified cloud deployment.
