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


def test_csv_spreadsheet_formula_injection_is_escaped():
    report = {**REPORT, "metadata": {"source": "=HYPERLINK(\"https://example.invalid\")"},
              "historical": {"=dangerous": "+SUM(1,1)"}}
    exported = report_csv(report)
    rows = list(csv.reader(io.StringIO(exported)))
    assert any(row[0] == "historical.=dangerous" for row in rows)
    assert any(row[2].startswith(chr(9)) and "SUM" in row[2] for row in rows)
    assert any(row[2].startswith(chr(9)) and "HYPERLINK" in row[2] for row in rows)


def test_export_formats_share_input_provenance():
    report = {
        **REPORT,
        "metadata": {
            "source": "synthetic",
            "portfolio_input_sha256": "a" * 64,
            "returns_input_sha256": "b" * 64,
            "generated_at_utc": "2026-11-24T18:00:00+00:00",
            "limitations": "linear exposures",
        },
    }
    json_data = json.loads(report_json(report))
    csv_rows = list(csv.reader(io.StringIO(report_csv(report))))
    assert json_data["metadata"]["portfolio_input_sha256"] == "a" * 64
    assert ["metadata.portfolio_input_sha256", "value", "a" * 64] in csv_rows
    assert ["metadata.returns_input_sha256", "value", "b" * 64] in csv_rows
    assert ["metadata.generated_at_utc", "value", "2026-11-24T18:00:00+00:00"] in csv_rows
    assert report_pdf(report).startswith(b"%PDF")


def test_pdf_escapes_untrusted_markup_in_fields():
    report = {**REPORT, "metadata": {"source": "<b>untrusted</b> & research"}}
    pdf = report_pdf(report)
    assert pdf.startswith(b"%PDF")


def test_pdf_rejects_oversized_report():
    report = {**REPORT, "metadata": {"many": list(range(1501))}}
    with pytest.raises(ValueError, match="too large"):
        report_pdf(report)


def test_downloadable_pdf_is_parseable_and_contains_research_fields():
    from pypdf import PdfReader

    payload = report_pdf({
        **REPORT,
        "metadata": {
            "source": "fixture",
            "portfolio_input_sha256": "a" * 64,
            "generated_at_utc": "2026-11-24T18:00:00+00:00",
        },
    })
    reader = PdfReader(io.BytesIO(payload), strict=True)
    assert len(reader.pages) >= 1
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert "Fragility Atlas" in text
    assert "metadata.portfolio_input_sha256" in text
    assert "historical.expected_shortfall" in text
    assert "2026-11-24T18:00:00+00:00" in text


def test_downloadable_csv_roundtrips_unicode_and_quoted_fields():
    report = {**REPORT, "metadata": {"source": 'Échantillon, "research"'}}
    rows = list(csv.reader(io.StringIO(report_csv(report))))
    assert ["metadata.source", "value", 'Échantillon, "research"'] in rows
