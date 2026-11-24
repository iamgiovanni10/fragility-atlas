# Release deployment and acceptance checklist

**Status: release candidate, not yet approved.** The public Streamlit app must remain unchanged until the release is reviewed.

## Before merging

1. Check the most recent CI workflow on `release/v1-comprehensive` for **both** Python 3.10 and 3.12. Confirm unit tests, Streamlit AppTest, Ruff, wheel build, isolated wheel installation, and CLI help all succeed.
2. Confirm `pyproject.toml` version matches the intended release. `1.0.0rc1` is a pre-release; change to `1.0.0` only after acceptance.
3. Review the PR diff for credentials, personal data, unexpected binaries, and dependencies. Do not put secrets in examples or reports.
4. Confirm the synthetic demonstration runs without uploaded files and the original Risk Workbench still works.
5. Verify the research claims: linear factors, synthetic covariance assumptions, non-calibrated hedge costs, and SLSQP's lack of a global-optimality certificate.

## Streamlit staging acceptance

Run the branch locally or in a **separate staging deployment**. Do not change the public deployment's branch until checks pass.

```bash
python -m pip install -e '.[dev,dashboard]'
streamlit run dashboard.py
```

- Navigate between Risk Workbench and Research Lab without exceptions.
- Import the sample portfolio; verify factor and position attribution reconcile.
- Modify the equities shock and confirm the P&L and comparison chart update.
- Upload a valid chronological factor-history CSV; confirm the replay chart and minimum P&L.
- Upload a valid one-column return-history CSV; confirm VaR, ES, drawdown, and rolling backtest.
- Try empty, malformed, oversized, nonfinite, and mismatched CSV files; confirm clear errors and no server crash.
- Download JSON, CSV, PDF. Confirm JSON parses, CSV opens without executing formulas, and PDF opens with all required fields. Confirm the three exports refer to the same scenario and source data.
- Confirm hashes match the exact uploaded bytes (or documented canonical synthetic representation) and that timestamps are UTC.
- Check narrow-screen layout, contrast, tab order, and keyboard operation.
- Restart the staging app and confirm the synthetic default demo still works.

## Post-merge checks

- Verify the Streamlit public app uses the intended branch and entrypoint, loads all pages, and has no startup error.
- Re-run one representative scenario and export all three formats on the deployed app.
- Create a GitHub release only after the merged commit passes CI and public deployment checks.
- If any release-blocking error appears, do not publish a 1.0 tag; fix it on a new PR.

## Unresolved scientific boundaries

- No independently verified market dataset or independently validated calibration.
- Historical factor replay depends on user-provided shock observations and their provenance.
- Hedge costs are illustrative; SLSQP solutions are feasibility-checked but not certified globally optimal.
- Portfolio historical-return risk and position-factor stress are separate inputs; no automatic holdings-to-return reconciliation.
- The statistical VaR coverage diagnostic is not proof of forecast validity, especially with few expected breaches.

These boundaries must remain prominent in the interface and documentation. Do not market this as a production trading or institutional risk engine.
