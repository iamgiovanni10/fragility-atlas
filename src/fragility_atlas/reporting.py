"""Deterministic research-report exports. No arbitrary HTML or executable templates."""
import csv
import io
import json
import math


def _validate_report(report):
    if not isinstance(report, dict) or not isinstance(report.get("metadata"), dict):
        raise ValueError("report requires metadata")
    if not isinstance(report.get("portfolio"), dict) or not isinstance(report.get("historical"), dict):
        raise ValueError("report requires portfolio and historical sections")
    return report


def report_json(report):
    _validate_report(report)
    return json.dumps(report, indent=2, sort_keys=True, allow_nan=False)


def report_csv(report):
    """Flatten numerical scalar metrics; never silently discard unsupported values."""
    _validate_report(report)
    out = io.StringIO(newline="")
    writer = csv.writer(out)
    writer.writerow(["section", "metric", "value"])
    def walk(section, value):
        if isinstance(value, dict):
            for k, v in value.items():
                walk(f"{section}.{k}" if section else str(k), v)
        elif isinstance(value, (list, tuple)):
            for i, v in enumerate(value):
                walk(f"{section}[{i}]", v)
        elif value is None:
            writer.writerow([section, "value", ""])
        elif isinstance(value, (str, bool, int, float)):
            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError("nonfinite report value")
            writer.writerow([section, "value", value])
        else:
            raise ValueError(f"unsupported report value at {section}")
    walk("", report)
    return out.getvalue()


def report_pdf(report):
    """PDF bytes, requiring optional reportlab dependency; bounded for safe rendering."""
    _validate_report(report)
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from xml.sax.saxutils import escape

    rows = list(csv.reader(io.StringIO(report_csv(report))))
    if len(rows) > 1500:
        raise ValueError("report too large for PDF export")
    buffer = io.BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=(595, 842), leftMargin=45,
                                 rightMargin=45, topMargin=45, bottomMargin=45)
    styles = getSampleStyleSheet()
    story = [Paragraph("Fragility Atlas — Research Report", styles["Title"]),
             Spacer(1, 12),
             Paragraph("Research use only. No investment advice. Synthetic data by default. "
                       "Linear-factor assumptions and model limitations apply.", styles["BodyText"]),
             Spacer(1, 12)]
    for section, _, value in rows[1:]:
        label = escape(section)
        rendered = escape(value)
        if len(label) > 160 or len(rendered) > 500:
            raise ValueError("report field too long for PDF export")
        story.append(Paragraph(f"<b>{label}</b>: {rendered}", styles["BodyText"]))
        story.append(Spacer(1, 4))
    document.build(story)
    return buffer.getvalue()
