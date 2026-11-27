# Portfolio & stress engine (synthetic demonstration)

The portfolio CSV requires `position_id,quantity,price_usd` plus at least one factor column. Each factor column is the **USD P&L sensitivity per position unit for a factor shock of 1.0 decimal units**. Position sensitivity equals quantity multiplied by factor sensitivity. Market value equals quantity multiplied by price. Negative quantities represent short positions; prices must be nonnegative. Factor shocks are decimal changes, e.g. -0.05 for -5%.

`read_portfolio_csv` rejects duplicate IDs/headers, malformed rows, nonfinite values, oversized input, and missing factors. It does not accept Excel files or discover financial instruments automatically.

`Portfolio.scenario` computes position and factor attribution for one shock vector. `evaluate_scenarios` evaluates named scenarios, requiring all factor names to match. `replay_factor_history` applies a chronological matrix of factor shocks to fixed linear exposures.

All computations are **linear** and do not capture convexity, options Greeks, funding, slippage, or changing positions. Historical replay is only meaningful when the supplied factor history is trustworthy, comparable, and correctly mapped. The bundled portfolio is synthetic and is not a recommendation or a calibrated portfolio.
