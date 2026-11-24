import csv
import io
import json
import pytest
from fragility_atlas.reporting import report_json, report_csv, report_pdf


REPORT = {
    "metadata": {"source": "synthetic", "limitations": "not calibrated"},
    "portfolio": {"value": 1000.0, "exposure": [100.0, -50.0]},
    "historical": {"var": 20.0, "expected_shortfall": 30.0},
    "stress": {"pnl": -25.0},
}


def test_json_is_parseable_and_preserves_values():
    result = json.loads(report_json(REPORT))
    assert result["historical"]["expected_shortfall"] == 30.0


def test_csv_contains_nested_numeric_metrics():
    rows = list(csv.reader(io.StringIO(report_csv(REPORT))))
    assert ["historical.var", "value", "20.0"] in rows
    assert ["portfolio.exposure[1]", "value", "-50.0"] in rows


def test_pdf_is_valid_pdf():
    result = report_pdf(REPORT)
    assert result.startswith(b"%PDF")
    assert len(result) > 100


def test_invalid_reports_rejected():
    for report in ({}, {"metadata": {}}, {"metadata": {}, "portfolio": {}}):
        with pytest.raises(ValueError):
            report_json(report)


def test_nonfinite_numbers_rejected():
    bad = {**REPORT, "historical": {"var": float("nan")}}
    with pytest.raises(ValueError):
        report_csv(bad)
    with pytest.raises(ValueError):
        report_json(bad)
