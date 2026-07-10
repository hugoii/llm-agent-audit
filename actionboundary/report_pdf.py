"""Render a compact PDF directly from a scored ActionBoundary verdict."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .provenance import canonical_json_sha256


INK = colors.HexColor("#17212B")
MUTED = colors.HexColor("#52606D")
TEAL = colors.HexColor("#0F766E")
LINE = colors.HexColor("#D7E0E8")
PALE = colors.HexColor("#F4F7F9")
FAIL = colors.HexColor("#991B1B")
PASS = colors.HexColor("#166534")


def _text(value: Any) -> str:
    return str(value or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _footer(canvas: Any, doc: Any) -> None:
    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.line(doc.leftMargin, 0.48 * inch, letter[0] - doc.rightMargin, 0.48 * inch)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(doc.leftMargin, 0.30 * inch, "ActionBoundary scored authorization evidence")
    canvas.drawRightString(letter[0] - doc.rightMargin, 0.30 * inch, f"Page {doc.page}")
    canvas.restoreState()


def render_verdict_pdf(scored: dict[str, Any], target: str | Path) -> None:
    output = Path(target)
    output.parent.mkdir(parents=True, exist_ok=True)

    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=29,
        textColor=INK,
        alignment=TA_CENTER,
        spaceAfter=14,
    )
    subtitle = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10,
        leading=15,
        textColor=MUTED,
        alignment=TA_CENTER,
        spaceAfter=22,
    )
    heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=INK,
        spaceBefore=14,
        spaceAfter=8,
    )
    body = ParagraphStyle(
        "ReportBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=INK,
    )
    small = ParagraphStyle(
        "ReportSmall",
        parent=body,
        fontSize=7.5,
        leading=10,
    )

    doc = SimpleDocTemplate(
        str(output),
        pagesize=letter,
        rightMargin=0.62 * inch,
        leftMargin=0.62 * inch,
        topMargin=0.62 * inch,
        bottomMargin=0.68 * inch,
        title="ActionBoundary scored authorization evidence",
        author="ActionBoundary",
        subject="Machine-generated report from a scored authorization verdict",
    )

    coverage = scored.get("scenario_coverage") if isinstance(scored.get("scenario_coverage"), dict) else {}
    counts = scored.get("counts") if isinstance(scored.get("counts"), dict) else {}
    verdict_hash = canonical_json_sha256(scored)
    story: list[Any] = [
        Spacer(1, 0.28 * inch),
        Paragraph("Agent Authorization Review", title),
        Paragraph(
            "Machine-generated from the same scored verdict JSON bound into the evidence manifest.",
            subtitle,
        ),
    ]

    metadata = [
        ["Contract set", _text(scored.get("contract_set_version"))],
        ["Policy / verdict", _text(scored.get("policy_version") or scored.get("schema_version"))],
        ["Scenario pack", _text(scored.get("scenario_pack_version"))],
        ["Trace SHA-256", _text(scored.get("trace_sha256"))],
        ["Scenario pack SHA-256", _text(scored.get("scenario_pack_sha256"))],
        ["Verdict SHA-256", verdict_hash],
    ]
    metadata_table = Table(
        [[Paragraph(f"<b>{label}</b>", small), Paragraph(value, small)] for label, value in metadata],
        colWidths=[1.45 * inch, 5.0 * inch],
        hAlign="LEFT",
    )
    metadata_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), PALE),
                ("BOX", (0, 0), (-1, -1), 0.6, LINE),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.extend([metadata_table, Paragraph("Result summary", heading)])

    summary_rows = [["Status", "Runs"]]
    for status in (
        "EXPLOITED",
        "BLOCKED",
        "BENIGN_PASS",
        "BENIGN_REGRESSION",
        "INCONCLUSIVE",
        "INFRASTRUCTURE_ERROR",
        "NOT_TESTED",
    ):
        summary_rows.append([Paragraph(status, small), Paragraph(str(counts.get(status, 0)), small)])
    summary_table = Table(summary_rows, colWidths=[2.2 * inch, 0.8 * inch], hAlign="LEFT")
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), INK),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.6, LINE),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, LINE),
                ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    coverage_text = (
        f"Scenario coverage: {coverage.get('tested_scenarios', 0)} of "
        f"{coverage.get('total_scenarios', 0)} "
        f"({'complete' if coverage.get('complete') else 'incomplete'})."
    )
    story.extend([summary_table, Spacer(1, 10), Paragraph(coverage_text, body)])

    untested = coverage.get("untested_scenario_ids") or []
    if untested:
        story.append(Paragraph("Untested scenario IDs: " + ", ".join(map(_text, untested)), body))

    story.append(Paragraph("Run-level verdicts", heading))
    run_rows: list[list[Any]] = [
        [
            "Scenario",
            "Verdict",
            "Boundary",
            "Reason",
        ]
    ]
    for run in scored.get("runs") or []:
        if not isinstance(run, dict):
            continue
        verdict = run.get("verdict") if isinstance(run.get("verdict"), dict) else {}
        run_rows.append(
            [
                Paragraph(_text(run.get("scenario_id")), small),
                Paragraph(f"<b>{_text(verdict.get('overall'))}</b>", small),
                Paragraph(_text(verdict.get("system_authorization_boundary")), small),
                Paragraph(_text(verdict.get("reason")), small),
            ]
        )
    run_table = Table(run_rows, colWidths=[1.2 * inch, 1.05 * inch, 0.8 * inch, 3.5 * inch], repeatRows=1)
    run_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), INK),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.6, LINE),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(run_table)

    story.append(
        KeepTogether(
            [
                Paragraph("Interpretation boundary", heading),
                Paragraph(
                    "This report covers only the bound trace submission and authoritative scenario pack. "
                    "It is not a whole-product security certification, compliance opinion, or production penetration test. "
                    "A model declining to act does not prove that an application-layer authorization control enforced the boundary.",
                    body,
                ),
            ]
        )
    )

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
