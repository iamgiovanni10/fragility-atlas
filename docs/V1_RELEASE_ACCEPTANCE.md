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


## CI and integration evidence (2026-11-24)

- GitHub Actions run 45482696899 completed successfully for Python 3.10 and 3.12, including unit tests and import checks (commit 10fde6aca449fe7322ca94fb210083979b78203b).
- Later integration tests include Streamlit AppTest and workbench input guardrails; final result of the newer runs must be checked before release.
- Research Lab now includes JSON, CSV and PDF exports and a UTC generation timestamp; downloaded-file behavior and deployed navigation still require user-journey verification.
- No independent market calibration or globally certified hedge optimization has been performed.

## Latest acceptance evidence (2026-11-24)

- CI run [45489211860](https://github.com/iamgiovanni10/fragility-atlas/actions/runs/45489211860) passed both Python 3.10 and 3.12 for commit `515b99b`, including pytest, Streamlit AppTest, Ruff, build, wheel installation, dependency check and CLI smoke test.
- Later changes include documentation-only README replacement; CI for the exact eventual release commit still must be checked.
- Generated PDFs are now parsed with pypdf in tests, and CSV Unicode/quoting round-trip is covered. Browser-level downloads and a staging deployment have **not** been independently verified.
- SHA-256 input fingerprints are tested for byte-level provenance; they do not prove data authenticity.
- Release blockers remain: staged end-to-end user journey, responsive and keyboard checks, public deployment smoke test, final release version/tag and review of the exact merge commit.

## Release candidate checkpoint (2026-11-24)

The functional scope is frozen pending final acceptance. CI [45503604131](https://github.com/iamgiovanni10/fragility-atlas/actions/runs/45503604131) and Chromium [45503604136](https://github.com/iamgiovanni10/fragility-atlas/actions/runs/45503604136) passed at commit `ba013f1`, including the redesigned report download and backtest visualization. This supersedes the earlier absence of browser-level evidence, but does not establish cloud deployment acceptance.

Subsequent drawdown, report identity, documentation and regression-test changes require fresh CI on the final candidate. Cloud acceptance remains open: verify the actual deployed report format, responsive layout, keyboard navigation, uploads and downloads. Retain the prerelease version until these checks pass. No independent scientific validation is claimed.

## Final automated candidate checkpoint (2026-11-26)

- Exact tested commit: `cb40acc23397470e214c118f79919b62fd4571eb`.
- [CI 45912642976](https://github.com/iamgiovanni10/fragility-atlas/actions/runs/45912642976): success.
- [Browser acceptance 45912642907](https://github.com/iamgiovanni10/fragility-atlas/actions/runs/45912642907): success. The test covers navigation, shock recalculation, actual JSON/CSV/PDF downloads, three viewport sizes and selected keyboard interactions.
- The candidate includes explicit zero-baseline signed charts and compact PDF tables. Automated PDF parsing is not visual pagination certification.
- Prior staging user checks confirmed navigation and exports; the updated visual layout and uploaded-data journey still require final staging confirmation. Responsive smoke checks are not comprehensive accessibility certification.
- An earlier PDF download cancellation was observed; successful subsequent runs do not prove intermittent failures are eliminated.
- Keep version 1.0.0rc1 and do not merge until final staging acceptance and release authorization. Re-run CI on the exact versioned release commit. Public deployment smoke test follows merge.

## Final import and export acceptance checkpoint

Commit `834a23804717dad431edd3b63ce90b3dff7ba201` passed [CI](https://github.com/iamgiovanni10/fragility-atlas/actions/runs/45914611160) and [Browser acceptance](https://github.com/iamgiovanni10/fragility-atlas/actions/runs/45914611202). Browser acceptance now verifies actual CSV upload, processed source label, byte-level SHA-256 provenance, unchanged portfolio and stress P&L, report downloads, viewport and keyboard smoke checks. The prior upload test failed before the processed source was confirmed; the new test retains all assertions and waits for the processed source label.

Staging screenshots and reports supplied by the owner confirmed earlier chart and report changes. Subsequent full-width scenario comparison and PDF pagination changes passed automated checks but still require visual staging confirmation. No independent market calibration or accessibility certification is claimed. Release authorization and exact final version CI remain required.

## Staging visual acceptance — 2026-11-27 UTC

Owner-supplied staging screenshot after reboot confirms explicit zero tick, full-width scenario chart and complete three-column table below it. Owner-supplied PDF generated at 2026-11-27T02:06:57.547224+00:00 confirms seven pages rather than eight, stress and coverage sections sharing pages with other sections, normalized signed zero in inspected stress and attribution rows, and unchanged executive summary and scenario results. Final page is partially filled; accepted as nonblocking. Visual acceptance is limited to the supplied synthetic example. Final version checks and merge authorization remain pending.
