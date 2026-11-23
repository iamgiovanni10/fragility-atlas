# Fragility Atlas

**Explainable Reverse Stress Testing & Portfolio Fragility Analysis**

Fragility Atlas is an open-source **quantitative finance research prototype** for identifying the smallest covariance-adjusted combination of market-factor shocks that breaches a portfolio loss threshold, explaining the resulting factor P&L, and exploring cost-aware hedges under an ellipsoidal uncertainty set.

> **Research question:** What is the nearest adverse market scenario that makes a portfolio exceed its loss tolerance—and what exposures drive that vulnerability?

**Status:** v0.1.0 research prototype · Python 3.10+ · synthetic examples · MIT license

## What it does today

| Capability | Status | Method |
| --- | --- | --- |
| Reverse stress testing | Implemented | Closed-form constrained Mahalanobis minimization |
| Factor-level P&L attribution | Implemented | Linear exposure × factor shock |
| Ellipsoidal hedge search | Implemented | L1-cost minimization using SciPy SLSQP |
| Input validation | Implemented | Dimension, finiteness, symmetry, positive-definiteness checks |
| Automated unit tests | Implemented | Pytest and GitHub Actions |
| Historical data calibration | Planned | Not included in v0.1.0 |
| Nonlinear instrument repricing | Planned | Not included in v0.1.0 |
| Institutional model validation | Not performed | Required before any financial deployment |

## Why reverse stress testing?

Conventional stress tests start with a scenario and estimate its impact. **Reverse stress testing** starts with an adverse outcome (for example, a loss exceeding $1 million) and searches for a scenario that produces it. The technique is established in financial risk research; Fragility Atlas does **not** claim to invent it.

This prototype combines the scenario search with interpretable factor-level contributions and a constrained hedge exploration workflow.

## Quick start

```bash
python -m pip install -e '.[dev]'
pytest -q
fragility-atlas examples/demo.json --loss 1000000
fragility-atlas examples/demo.json --loss 1000000 --hedge --radius 2
```

The demonstration uses **synthetic inputs and illustrative costs**. Do not interpret output as observed market conditions or investment advice.

## Interactive dashboard (optional)

Run the Streamlit dashboard locally:

```bash
python -m pip install -e '.[dashboard]'
streamlit run dashboard.py
```

The dashboard shows the synthetic minimum-distance scenario, factor-level P&L attribution, optional illustrative hedge optimization, and a downloadable JSON report. It does **not** provide live market prices, probability calibration, backtesting, or investment recommendations.

## Mathematical approach

Let `b` be portfolio factor sensitivities, `Σ` a symmetric positive-definite covariance matrix, `x` a vector of factor shocks, and `L > 0` the loss threshold.

```text
minimize     xᵀ Σ⁻¹ x
subject to   bᵀ x ≤ −L

solution     x* = −L Σb / (bᵀΣb)
distance     d* = L / sqrt(bᵀΣb)
```

For hedge matrix `H`, hedge positions `h`, and uncertainty radius `r`, the model constrains the worst-case linear loss to:

```text
r × sqrt((b + Hh)ᵀ Σ (b + Hh)) ≤ L
```

The optimizer minimizes illustrative linear absolute hedge expenditure `sum(cᵢ |hᵢ|)`. See [Mathematical methodology](docs/METHODOLOGY.md) for assumptions, derivation, interpretation, and validation considerations.

**Important:** Mahalanobis distance is not a crisis probability; a feasible numerical solution is not proof of global optimality, and a modeled hedge is not necessarily tradeable.

## Repository structure

```text
.github/workflows/ci.yml       Continuous integration
src/fragility_atlas/core.py    Reverse stress and hedge calculations
src/fragility_atlas/cli.py     Command-line interface
tests/test_core.py             Unit tests
examples/demo.json            Synthetic portfolio example
docs/METHODOLOGY.md           Mathematical methodology
pyproject.toml                Packaging and dependencies
```

## Research roadmap

1. Reproducible, legally sourced historical factor datasets and out-of-sample evaluation.
2. Empirical covariance estimation, regime sensitivity, and heavy-tail stress calibration.
3. Convex optimization formulations with independently verifiable certificates.
4. Nonlinear fixed-income and derivatives repricing with liquidity and transaction costs.
5. Financial-network contagion models and transparent counterfactual explanations.
6. Audit logs, data lineage, model governance, and independent validation.

These are **future research directions**, not implemented features.

## Limitations

- Linear factor valuation; no gamma, defaults, nonlinear liquidity effects, or dynamic hedging.
- Covariance geometry can understate tail dependence and regime shifts.
- Synthetic factors and hedge costs; no live market data or execution integration.
- SLSQP is a numerical method; results require independent verification.
- No backtesting, regulatory approval, or independent production validation.

## Development & AI assistance

The initial prototype was created through an **AI-assisted development workflow**. AI tools were used substantially to generate the initial Python implementation, tests, documentation, and mathematical presentation. The project owner initiated the project and coordinated its publication and subsequent development. Code and numerical outputs should be independently reviewed before relying on them.

This disclosure describes the development process; it does not imply that the project has been peer reviewed or independently validated.

## Related research

- Crépey et al., *Quantitative reverse stress testing, bottom up* (2023): https://doi.org/10.1080/14697688.2023.2187315
- *Reverse stress testing: Scenario design for macroprudential stress tests*: https://doi.org/10.1111/mafi.12373

## License

MIT — see [LICENSE](LICENSE).
