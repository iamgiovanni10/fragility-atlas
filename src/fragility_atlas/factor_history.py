"""Strict chronological factor-shock CSV loader for historical replay.

Rows represent consecutive observations. Columns are factor names; shocks are
decimal returns. No dates, asset prices, or missing factor columns are inferred.
"""
import csv
import io
import math
import numpy as np


def read_factor_history_csv(content, factor_names, max_rows=10000, max_bytes=2_000_000):
    if not isinstance(content, str) or len(content.encode("utf-8")) > max_bytes:
        raise ValueError("history CSV must be UTF-8 text within size limit")
    names = tuple(factor_names)
    if not names or len(set(names)) != len(names):
        raise ValueError("factor names must be nonempty and unique")
    reader = csv.DictReader(io.StringIO(content, newline=""))
    if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValueError("missing or duplicate factor headers")
    if set(reader.fieldnames) != set(names):
        raise ValueError("factor history headers must match portfolio factors exactly")
    rows = []
    for row in reader:
        if len(rows) >= max_rows:
            raise ValueError("factor history row limit exceeded")
        if None in row or any(value is None for value in row.values()):
            raise ValueError("malformed factor history row")
        try:
            values = [float(row[name]) for name in names]
        except (ValueError, TypeError) as exc:
            raise ValueError("invalid factor history number") from exc
        if not all(math.isfinite(x) for x in values):
            raise ValueError("nonfinite factor history number")
        rows.append(values)
    if len(rows) < 2:
        raise ValueError("factor history requires at least two observations")
    return np.asarray(rows, dtype=float)
