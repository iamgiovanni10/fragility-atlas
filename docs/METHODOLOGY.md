# Mathematical Methodology — Fragility Atlas v0.1.0

## Scope and conventions

This document describes the **implemented** linear-factor prototype, not a production risk model. Factor shocks `x` are decimal returns; exposure vector `b` is dollar P&L per unit factor return; `Σ` is a positive-definite covariance matrix of factor returns. Portfolio P&L is `bᵀx`.

## 1. Reverse stress testing

For a chosen loss threshold `L > 0`, solve

```text
minimize_x  xᵀ Σ⁻¹ x
subject to  bᵀx ≤ −L
```

The objective is squared Mahalanobis distance, a geometry based on the assumed covariance matrix. For nonzero `b`, the optimizer lies on the boundary `bᵀx = −L`.

The Lagrangian for the equality-constrained problem is

```text
ℒ(x, λ) = xᵀΣ⁻¹x + λ(bᵀx + L).
```

Setting its gradient to zero yields `2Σ⁻¹x + λb = 0`, so `x = −(λ/2)Σb`. Enforcing the loss equality gives

```text
x* = −L Σb / (bᵀΣb)
d* = sqrt(x*ᵀΣ⁻¹x*) = L / sqrt(bᵀΣb).
```

The factor-level P&L contribution is `bᵢx*ᵢ`; contributions sum to `−L` up to floating-point precision. A positive contribution offsets losses elsewhere. These are **linear scenario contributions**, not causal attributions.

## 2. Ellipsoidal hedge search

Let `H` be a matrix whose columns are sensitivities per unit of hedge instrument, `h` the hedge-unit vector, and `c` strictly positive illustrative per-unit costs. The post-hedge exposure is `b + Hh`.

For the uncertainty set

```text
U(r) = { x : xᵀΣ⁻¹x ≤ r² },
```

the worst linear loss is

```text
max_{x∈U(r)} −(b+Hh)ᵀx
  = r sqrt((b+Hh)ᵀΣ(b+Hh)).
```

The implemented numerical problem is

```text
minimize_h   Σᵢ cᵢ |hᵢ|
subject to   r sqrt((b+Hh)ᵀΣ(b+Hh)) ≤ L
             |hᵢ| ≤ max_units.
```

The code represents `h = h⁺ − h⁻` with nonnegative split variables and solves the nonlinear constraint using SciPy SLSQP. This is a convex mathematical problem when `Σ` is positive definite, but **SLSQP output alone is not a global optimality certificate**. A future implementation could use a dedicated second-order cone solver with residual and duality-gap checks.

## 3. Interpretation and failure modes

- **Distance is not probability.** No empirical tail likelihood is calibrated by this prototype. The `r` radius is a modeling choice, not automatically a confidence interval.
- **Linear P&L.** Gamma, convexity, defaults, spread jumps, liquidity feedback, market impact, basis risk, and changing hedge sensitivities are absent.
- **Covariance estimation.** A historical covariance may be unstable, regime-dependent, and inappropriate during crises.
- **Costs and feasibility.** The demo cost model is illustrative; actual hedges can have bid/ask spreads, funding, margin, minimum lot sizes, constraints, and nonlinear costs.
- **Numerical validation.** Recalculate loss and constraint residuals independently; test sensitivity to scaling, perturbations, starting values, and solver tolerances.
- **Governance.** Production deployment requires independent model validation, versioned market data, audit logs, backtesting, and appropriate supervision.

## 4. Verification and reproducibility

From the repository root:

```bash
python -m pip install -e '.[dev]'
pytest -q
fragility-atlas examples/demo.json --loss 1000000
fragility-atlas examples/demo.json --loss 1000000 --hedge --radius 2
```

The tests check the exact reverse-stress loss boundary, the minimum-distance property for selected loss-preserving perturbations, covariance validation, zero-exposure handling, and a hedge feasibility example. They do not constitute exhaustive numerical, statistical, or independent model validation.

## 5. Research opportunities

Promising extensions include calibrated tail-risk uncertainty sets, regime-aware dependence models, nonlinear instrument repricing, distributionally robust optimization, certified convex solvers, counterparty-network spillovers, and explainability methods that separate mathematical attribution from causal claims. Novelty must be established by a systematic literature review and empirical benchmarking.
