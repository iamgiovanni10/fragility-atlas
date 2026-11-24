# Fragility Atlas 1.0 — Release acceptance contract

Status: **IN DEVELOPMENT — NOT RELEASED**. This document is a scope and acceptance gate, not evidence that the capabilities exist.

## Mandatory release gates

1. Portfolio analytics: documented CSV schema, strict validation, holdings/exposures, contribution reconciliation and downloadable sample.
2. Historical risk: reproducible return data, empirical VaR and expected shortfall with explicit confidence level, annualization and conventions, drawdowns, missing-data rules and numerical tests.
3. Stress testing: historical replay and hypothetical shocks, provenance, units, matching factor coverage, scenario-level P&L attribution.
4. Reverse stress: analytic reference, numeric edge cases, covariance conditioning and deterministic reproducibility.
5. Robust hedging: explicit hedge constraints, transaction costs, independent post-solve feasibility checks and infeasible-case behavior; no unsupported global-optimality claim.
6. Scenario intelligence: same-scenario pre/post hedge, ellipsoid membership, correct out-of-set warnings.
7. Validation: out-of-sample methodology, VaR coverage diagnostics, appropriate baselines, limitations and documented sample sizes.
8. Sensitivity: covariance and exposure perturbations, stable/unstable region identification, bounded runtime.
9. Dashboard: coherent navigation, readable mobile/desktop layout, informative failures, accessible controls, test coverage.
10. Reports: reproducible JSON/CSV/PDF where supported, assumptions, timestamps, input provenance, methodology and unambiguous synthetic/real-data labels.

## Cross-cutting acceptance

- CI: unit tests, integration smoke test for dashboard import/start, lint, dependency compatibility.
- Security: no user data committed or logged; upload size and file type constraints; no arbitrary execution.
- Documentation: installation, example inputs, limitations, AI-assisted development disclosure, license, reproducibility commands.
- Deployment: verified Streamlit build, user journey, download integrity, no secrets required for demo.
- Final audit: no unresolved release-blocking defects; independent review encouraged.
- Scientific claims must match validation evidence; **not investment advice**.

## Initial code audit (2026-11-24)

- The package metadata still reports version 0.1.0 despite the dashboard advertising v0.3. Versioning must be synchronized for release.
- Existing CI runs pytest only. It does not lint, install dashboard extras, or smoke-test the UI.
- Core hedge uses SLSQP with a numerical feasibility check, not a global optimality certificate. Preserve that distinction.
- Current demonstration uses synthetic linear factor exposures; there is no verified historical dataset, empirical backtest, or documented market-data provenance.
- The existing workbench ellipsoid_worst_loss validates radius but not all covariance/exposure shape and finiteness conditions; harden input validation.
- The risk dashboard uses synthetic hedge costs, which are not executable market prices.
- The current reporting path is JSON; PDF and CSV deliverables require implementation and tests.

**Release rule:** do not mark 1.0 complete or merge the release branch until every gate has an implementation, reproducible test evidence, and a documented limitation where appropriate.

## Implementation progress (2026-11-24)

- Historical metrics: implementation, unit tests and methodology committed; CI execution pending.
- Portfolio CSV aggregation: implementation, synthetic fixture, unit tests and methodology committed; dashboard integration pending.
- Hypothetical stress and fixed-exposure historical factor replay: implementation and unit tests committed; real-data provenance and historical validation pending.
- All other release gates remain open. This is **not** a release readiness statement.

