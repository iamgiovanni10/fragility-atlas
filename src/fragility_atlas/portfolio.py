"""Validated, deterministic linear-factor portfolio aggregation.

CSV schema: position_id,quantity,price_usd,<factor names as columns>.
Factor values are USD P&L per unit decimal factor move, per position unit.
"""
import csv
import io
import math
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class Portfolio:
    factors: tuple[str, ...]
    position_ids: tuple[str, ...]
    market_values: np.ndarray
    sensitivities: np.ndarray

    @property
    def value(self):
        return float(np.sum(self.market_values))

    @property
    def exposure(self):
        return np.sum(self.sensitivities, axis=0)

    def scenario(self, shocks):
        x = np.asarray(shocks, dtype=float)
        if x.shape != (len(self.factors),) or not np.all(np.isfinite(x)):
            raise ValueError("invalid factor shock vector")
        position_pnl = self.sensitivities @ x
        factor_pnl = self.exposure * x
        return {
            "total_pnl": float(np.sum(position_pnl)),
            "position_pnl": dict(zip(self.position_ids, map(float, position_pnl))),
            "factor_pnl": dict(zip(self.factors, map(float, factor_pnl))),
        }


def read_portfolio_csv(content, max_rows=10000, max_bytes=2_000_000):
    """Read trusted-format CSV text; fail closed on missing, duplicate, nonfinite data."""
    if not isinstance(content, str) or len(content.encode("utf-8")) > max_bytes:
        raise ValueError("CSV must be UTF-8 text within the size limit")
    if not isinstance(max_rows, int) or max_rows < 1:
        raise ValueError("max_rows must be positive")
    reader = csv.DictReader(io.StringIO(content, newline=""))
    columns = reader.fieldnames
    required = ("position_id", "quantity", "price_usd")
    if not columns or len(columns) != len(set(columns)) or not all(k in columns for k in required):
        raise ValueError("CSV requires unique headers and position_id,quantity,price_usd")
    if len(columns) > 53:
        raise ValueError("CSV supports at most 50 factor columns")
    factors = tuple(k for k in columns if k not in required)
    if not factors or any(not k.strip() for k in columns):
        raise ValueError("at least one named factor column is required")
    ids, values, exposures = [], [], []
    for row in reader:
        if len(ids) >= max_rows:
            raise ValueError("CSV row limit exceeded")
        if None in row or any(v is None for v in row.values()):
            raise ValueError("malformed CSV row")
        pid = row["position_id"].strip()
        if not pid or pid in ids:
            raise ValueError("position IDs must be nonempty and unique")
        try:
            qty = float(row["quantity"])
            price = float(row["price_usd"])
            factor_values = [float(row[f]) for f in factors]
        except (ValueError, TypeError) as exc:
            raise ValueError("invalid numeric value") from exc
        if not all(math.isfinite(v) for v in [qty, price, *factor_values]) or price < 0:
            raise ValueError("nonfinite values or negative price")
        market_value = qty * price
        row_exposure = [qty * v for v in factor_values]
        if not all(math.isfinite(v) for v in [market_value, *row_exposure]):
            raise ValueError("numeric overflow in position valuation or exposure")
        ids.append(pid)
        values.append(market_value)
        exposures.append(row_exposure)
    if not ids:
        raise ValueError("CSV contains no positions")
    values_array = np.asarray(values)
    exposures_array = np.asarray(exposures)
    if not math.isfinite(float(np.sum(values_array))) or not np.all(np.isfinite(np.sum(exposures_array, axis=0))):
        raise ValueError("numeric overflow in aggregate portfolio")
    return Portfolio(factors, tuple(ids), values_array, exposures_array)
