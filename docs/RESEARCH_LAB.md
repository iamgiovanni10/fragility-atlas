# Research Lab — v1.0 development preview

Run from repository root:

```bash
python -m pip install -e '.[dashboard,dev]'
streamlit run dashboard.py
```

Use the **Research Lab** page in Streamlit navigation. The original v0.3 dashboard remains available.

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
