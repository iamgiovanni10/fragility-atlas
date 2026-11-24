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
    def safe_csv(value):
        # Prevent spreadsheet software from interpreting untrusted text as a formula.
        if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@", chr(9), chr(13))):
            return chr(9) + value
        return value

    def walk(section, value):
        if isinstance(value, dict):
            for k, v in value.items():
                walk(f"{section}.{k}" if section else str(k), v)
        elif isinstance(value, (list, tuple)):
            for i, v in enumerate(value):
                walk(f"{section}[{i}]", v)
        elif value is None:
            writer.writerow([safe_csv(section), "value", ""])
        elif isinstance(value, (str, bool, int, float)):
            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError("nonfinite report value")
            writer.writerow([safe_csv(section), "value", safe_csv(value)])
        else:
            raise ValueError(f"unsupported report value at {section}")
    walk("", report)
    return out.getvalue()


def report_pdf(report):
    """Readable research summary; full observation arrays remain in JSON and CSV."""
    _validate_report(report)
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from xml.sax.saxutils import escape

    rows = list(csv.reader(io.StringIO(report_csv(report))))
    omitted = ("coverage.forecast_vars[", "coverage.realized_losses[", "historical_factor_replay[")
    selected = [row for row in rows[1:] if not row[0].startswith(omitted)]
    if len(selected) > 1500:
        raise ValueError("report too large for PDF export")
    buffer = io.BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=(595, 842), leftMargin=45,
                                 rightMargin=45, topMargin=48, bottomMargin=48)
    styles = getSampleStyleSheet()
    navy = colors.HexColor("#142B45")
    styles["Title"].textColor = navy
    styles["Heading2"].textColor = navy
    styles["BodyText"].fontSize = 9
    styles["BodyText"].leading = 12

    def para(value):
        return Paragraph(escape(str(value)), styles["BodyText"])

    def table(data, widths):
        result = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
        result.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), navy),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EFF3F7")]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        return result

    story = [Paragraph("Fragility Atlas — Research Report", styles["Title"]),
             para("Research use only. No investment advice. Synthetic data by default. "
                  "Linear-factor assumptions and model limitations apply."),
             Spacer(1, 12), Paragraph("Executive summary", styles["Heading2"])]
    historical = report["historical"]
    stress = report.get("stress") or {}
    metrics = [
        ("Net marked portfolio value", report["portfolio"].get("value"), "$"),
        ("Custom scenario P&L", stress.get("pnl"), "$"),
        ("Historical VaR", historical.get("var"), "$"),
        ("Expected shortfall", historical.get("expected_shortfall"), "$"),
        ("Historical risk notional", historical.get("portfolio_value"), "$"),
        ("Maximum drawdown", historical.get("maximum_drawdown"), "%"),
        ("Annualized volatility", historical.get("annualized_volatility"), "%"),
    ]
    summary = [["Risk measure", "Result"]]
    for label, value, unit in metrics:
        if isinstance(value, (int, float)):
            formatted = f"{value:.2%}" if unit == "%" else f"{value:,.2f} USD"
            summary.append([para(label), para(formatted)])
    story.append(table(summary, [305, 200]))
    story.append(para("Historical measures use the stated risk notional and return series, "
                      "which may differ from the marked portfolio."))
    comparisons = report.get("scenario_comparison") or {}
    if comparisons:
        story.append(Paragraph("Scenario comparison", styles["Heading2"]))
        scenario_rows = [["Hypothetical scenario", "P&L (USD)"]]
        for name, result in comparisons.items():
            scenario_rows.append([para(name), para(f"{result['pnl']:,.2f}")])
        story.append(table(scenario_rows, [305, 200]))
        # Diverging P&L bars share a zero baseline and a common dollar scale.
        from reportlab.graphics.shapes import Drawing, Rect, Line, String
        items = list(comparisons.items())[:12]
        scale = max((abs(float(result["pnl"])) for _, result in items), default=0.0) or 1.0
        height = 36 + 24 * len(items)
        chart = Drawing(490, height)
        zero = 320
        chart.add(Line(zero, 20, zero, height - 10, strokeColor=navy))
        for index, (name, result) in enumerate(items):
            y = height - 24 - index * 24
            pnl = float(result["pnl"])
            width = abs(pnl) / scale * 150
            chart.add(String(0, y + 3, str(name)[:32], fontSize=8, fillColor=navy))
            chart.add(Rect(zero - width if pnl < 0 else zero, y, width, 12,
                           fillColor=colors.HexColor("#B54747" if pnl < 0 else "#287D68"),
                           strokeColor=None))
        chart.add(String(zero, 5, "0 USD", fontSize=8, textAnchor="middle", fillColor=navy))
        story.append(Spacer(1, 8))
        story.append(chart)
        story.append(para("Common scale: maximum absolute displayed P&L "
                          f"{scale:,.2f} USD. Red = loss; green = gain. "
                          "Chart shows up to 12 scenarios; table contains all scenarios."))

    story.append(Paragraph("Research details and provenance", styles["Heading2"]))
    story.append(para(f"{len(rows)-1-len(selected)} observation-level fields omitted from this "
                      "summary PDF. Complete series are available in JSON and CSV."))
    groups = {}
    for section, _, value in selected:
        if len(section) > 160 or len(value) > 500:
            raise ValueError("report field too long for PDF export")
        groups.setdefault(section.split(".")[0].split("[")[0], []).append([para(section), para(value)])
    for name, entries in groups.items():
        story.append(Paragraph(escape(name.replace("_", " ").title()), styles["Heading2"]))
        story.append(table([["Field", "Value"]] + entries, [245, 260]))

    def footer(canvas, doc):
        canvas.setStrokeColor(colors.HexColor("#CBD5E1"))
        canvas.line(45, 35, 550, 35)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(navy)
        canvas.drawString(45, 23, "FRAGILITY ATLAS  |  RESEARCH ONLY")
        canvas.drawRightString(550, 23, f"Page {doc.page}")

    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()
