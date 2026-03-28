import io
import re
import time
from loguru import logger

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

def hx(c) -> str:
    """Return a 6-char lowercase hex string (no #) from a ReportLab color."""
    r = int(c.red * 255)
    g = int(c.green * 255)
    b = int(c.blue * 255)
    return f"{r:02x}{g:02x}{b:02x}"

# ─── Brand Palette (matches DeepScan dark UI) ─────────────────────────────────
DS_BG       = colors.HexColor("#0a0a0f")      # near-black bg
DS_PANEL    = colors.HexColor("#12121a")      # card bg
DS_CYAN     = colors.HexColor("#00f5ff")      # ds-cyan  
DS_BLUE     = colors.HexColor("#0f172a")      # dark text
DS_ACCENT   = colors.HexColor("#1e3a5f")      # blue accent
DS_SILVER   = colors.HexColor("#c8d0dc")      # body text
DS_DIM      = colors.HexColor("#6b7280")      # dim text
DS_RED      = colors.HexColor("#ef4444")
DS_ORANGE   = colors.HexColor("#f97316")
DS_YELLOW   = colors.HexColor("#eab308")
DS_GREEN    = colors.HexColor("#22c55e")
DS_WHITE    = colors.HexColor("#f8fafc")
DS_BORDER   = colors.HexColor("#1e293b")

VERDICT_COLORS = {
    "AUTHENTIC":       DS_GREEN,
    "UNCERTAIN":       DS_YELLOW,
    "LIKELY_FAKE":     DS_ORANGE,
    "DEFINITELY_FAKE": DS_RED,
    "POSSIBLY MANIPULATED": DS_YELLOW,
    "LIKELY AI":       DS_ORANGE,
    "CONFIRMED AI":    DS_RED,
}

ENGINE_NAMES = {
    "visual forensics": "Visual Forensics (MAS)",
    "facial proportion": "Facial Geometry & Proportions",
    "frequency fingerprint": "Frequency & Spectrum Analysis",
    "context validity": "Metadata & Contextual Integrity",
    "diffusion noise": "Generative Diffusion Noise",
}

def _parse_finding(f: dict):
    """Parse a backend finding dict into (engine_name, anomaly_score, detail)."""
    engine = f.get("engine", "Unknown Indicator")
    raw_detail = f.get("detail", "")
    final_detail = raw_detail

    try:
        f_score = float(f.get("score", 0) or 0)
    except (ValueError, TypeError):
        f_score = 0.0

    match = re.search(
        r'^([\w\s]+?)\s*score:\s*([\d.]+)/100\.?\s*(.*)$',
        raw_detail, re.IGNORECASE | re.DOTALL
    )
    if match:
        raw_name = match.group(1).strip().lower()
        for key, label in ENGINE_NAMES.items():
            if key in raw_name:
                engine = label
                break
        else:
            engine = match.group(1).strip().title()

        auth_score = float(match.group(2))
        f_score = max(0.0, min(100.0, 100.0 - round(auth_score)))
        final_detail = match.group(3).strip() or "No specific description provided."
    else:
        val_match = re.search(r'([\d.]+)/100', raw_detail)
        if val_match:
            f_score = max(0.0, min(100.0, 100.0 - round(float(val_match.group(1)))))

    return engine, f_score, final_detail


def _score_color(score: float) -> colors.HexColor:
    if score >= 75: return DS_RED
    if score >= 50: return DS_ORANGE
    if score >= 35: return DS_YELLOW
    return DS_GREEN


def _add_page_header(canvas, doc):
    """Draw a professional clean header on every page."""
    w, h = letter
    canvas.saveState()
    # Top thin accent line
    canvas.setFillColor(DS_ACCENT)
    canvas.rect(0, h - 3, w, 3, fill=1, stroke=0)
    
    # Brand label (Blue / Black)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.setFillColor(DS_BLUE)
    canvas.drawString(0.75 * inch, h - 36, "DEEPSCAN")
    canvas.setFont("Helvetica", 11)
    canvas.setFillColor(colors.HexColor("#334155"))
    canvas.drawString(0.75 * inch + 75, h - 36, "| Forensic Intelligence Report")
    
    # Page number right
    canvas.setFont("Helvetica", 10)
    canvas.setFillColor(colors.HexColor("#64748b"))
    canvas.drawRightString(w - 0.75 * inch, h - 36, f"PAGE {doc.page}")
    
    # Bottom footer line
    canvas.setFillColor(colors.HexColor("#e2e8f0"))
    canvas.rect(0.75 * inch, 0.5 * inch, w - 1.5 * inch, 1, fill=1, stroke=0)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#94a3b8"))
    canvas.drawString(0.75 * inch, 0.35 * inch, "CONFIDENTIAL — DEEPSCAN AI ENGINE — SYSTEM GENERATED FORENSICS")
    canvas.drawRightString(w - 0.75 * inch, 0.35 * inch, time.strftime('%Y-%m-%d %H:%M UTC'))
    canvas.restoreState()


class PdfGenerator:
    """Generates a multi-page, dark-themed forensic PDF report for DeepScan."""

    def create_report(self, data: dict) -> io.BytesIO:
        buf = io.BytesIO()

        doc = SimpleDocTemplate(
            buf,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.85 * inch,
            bottomMargin=0.65 * inch,
        )

        styles = getSampleStyleSheet()

        # ─ Style definitions ─
        def mk(name, base="Normal", **kw):
            return ParagraphStyle(name=name, parent=styles[base], **kw)

        BLACK       = colors.HexColor("#000000")
        DARK_GRAY   = colors.HexColor("#222222")
        MID_GRAY    = colors.HexColor("#444444")
        ACCENT_BLUE = colors.HexColor("#1e40af") # Professional Navy Blue
        DS_LT_BLUE  = colors.HexColor("#eff6ff")

        title_style   = mk("Title",    "Normal", fontSize=34, textColor=BLACK,       fontName="Helvetica-Bold", spaceAfter=6,  leading=40)
        subtitle_style= mk("Sub",      "Normal", fontSize=14, textColor=MID_GRAY,    spaceAfter=6)
        label_style   = mk("Label",    "Normal", fontSize=12, textColor=MID_GRAY,    fontName="Helvetica-Bold", spaceBefore=10)
        score_style   = mk("Score",    "Normal", fontSize=50, textColor=ACCENT_BLUE, fontName="Helvetica-Bold", leading=58)
        body_style    = mk("Body",     "Normal", fontSize=13, textColor=BLACK,       leading=20)
        section_style = mk("Section",  "Normal", fontSize=18, textColor=ACCENT_BLUE, fontName="Helvetica-Bold", spaceBefore=22, spaceAfter=10)
        finding_h     = mk("FindH",    "Normal", fontSize=15, textColor=BLACK,       fontName="Helvetica-Bold", spaceAfter=6,  spaceBefore=14)
        finding_body  = mk("FindBody", "Normal", fontSize=12, textColor=DARK_GRAY,   leading=18)
        warn_style    = mk("Warn",     "Normal", fontSize=12, textColor=colors.HexColor("#b91c1c"), fontName="Helvetica-Bold")
        caption_style = mk("Caption",  "Normal", fontSize=10, textColor=MID_GRAY,    leading=14)

        # ─ Parse data ─
        raw_score   = data.get("aacs_score", data.get("score", 0))
        score_val   = float(raw_score) if raw_score is not None else 0.0
        verdict     = data.get("verdict", "UNKNOWN").replace("_", " ").upper()
        v_color     = VERDICT_COLORS.get(verdict, DS_DIM)
        scan_id     = data.get("id", "N/A")
        file_type   = data.get("file_type", "Unknown")
        file_type_clean = file_type.replace("image/", "").replace("video/", "").upper() or file_type.upper()
        findings    = data.get("findings", [])
        narrative   = data.get("narrative", {})
        sub_scores  = data.get("sub_scores", {})
        ltca        = data.get("ltca_data", {})

        # Dynamic Summary (Mirrored from Frontend logic)
        if score_val > 70:
            summary_text = "The analysis reveals strong evidence of AI generation or deep manipulation. Multiple forensic layers triggered high-confidence warnings across structural, frequency, and pixel-level domains. These elements strongly suggest a sophisticated composite image likely created or enhanced with generative AI techniques."
        elif score_val > 35:
            summary_text = "The analysis reveals partial anomalies consistent with localized manipulation or light AI filtering. While some regions remain authentic, conflicting signals in compression or error levels warrant moderate caution."
        else:
            summary_text = "The analysis confirms the integrity of the image. Key indicators such as natural noise distribution, consistent physical lighting, and correct pixel-level error characteristics align perfectly with a genuine photograph. No significant AI artifacts were detected."

        technical_text = narrative.get("technical", "")

        date_str = time.strftime('%d %B %Y, %H:%M UTC')

        # ═══════════════════════════════════════════════════════════════════════
        # PAGE 1 — CLEAN COVER + SUMMARY
        # ═══════════════════════════════════════════════════════════════════════
        story = []

        # ─ Top spacer (header strip already drawn by _add_page_header) ─
        story.append(Spacer(1, 10))

        # ─ Report title (clean, left-aligned) ─
        story.append(Paragraph("Detection Report", title_style))
        story.append(HRFlowable(width="100%", color=ACCENT_BLUE, thickness=2, spaceAfter=10))

        # ─ Meta row: Image Type | Scan ID | Date ─
        meta_rows = [[
            Paragraph(f"<b>Image Type:</b>  {file_type_clean}", mk("M1","Normal",fontSize=12,textColor=BLACK,fontName="Helvetica")),
            Paragraph(f"<b>Scan ID:</b>  {scan_id}", mk("M2","Normal",fontSize=12,textColor=BLACK,fontName="Helvetica")),
            Paragraph(f"<b>Date:</b>  {date_str}", mk("M3","Normal",fontSize=12,textColor=BLACK,fontName="Helvetica")),
        ]]
        meta_table = Table(meta_rows, colWidths=["33%", "34%", "33%"])
        meta_table.setStyle(TableStyle([
            ("ALIGN",  (0,0), (-1,-1), "LEFT"),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("TOPPADDING",    (0,0), (-1,-1), 0),
            ("BOTTOMPADDING", (0,0), (-1,-1), 0),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 18))

        # ─ Score + Verdict side by side ─
        score_color_val = _score_color(score_val)
        verdict_para = Paragraph(
            f"<font color='#{hx(v_color)}'><b>{verdict}</b></font>",
            mk("VerdictBig","Normal",fontSize=20,fontName="Helvetica-Bold",leading=24)
        )

        score_block = Table(
            [[
                Paragraph(f"<font color='#{hx(v_color)}'><b>{score_val:.0f}%</b></font>",
                          mk("ScoreBig","Normal",fontSize=64,fontName="Helvetica-Bold",leading=72,textColor=ACCENT_BLUE)),
                Paragraph(
                    f"<font color='#000000' size=18><b>Overall Forgery Score</b></font><br/><br/>"
                    f"<font color='#{hx(v_color)}' size=22><b>{verdict}</b></font>",
                    mk("ScoreSide","Normal",fontSize=16,fontName="Helvetica-Bold",leading=26,textColor=BLACK)
                )
            ]],
            colWidths=[2.2*inch, 4.0*inch]
        )
        score_block.setStyle(TableStyle([
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("TOPPADDING",    (0,0), (-1,-1), 24),
            ("BOTTOMPADDING", (0,0), (-1,-1), 24),
            ("LEFTPADDING",   (0,0), (-1,-1), 24),
            ("BACKGROUND",    (0,0), (-1,-1), colors.HexColor("#f8fafc")),
            ("LINEBELOW",     (0,0), (-1,-1), 4, ACCENT_BLUE),
        ]))
        story.append(score_block)
        story.append(Spacer(1, 24))

        # ─ Analysis Summary ─
        story.append(Paragraph("Analysis Summary", section_style))
        story.append(HRFlowable(width="100%", color=ACCENT_BLUE, thickness=1, spaceAfter=10))
        story.append(Paragraph(summary_text.replace('\n', '<br/>'), body_style))
        story.append(Spacer(1, 24))

        # ─ Detailed Breakdown (Page 1 continues) ─
        story.append(Paragraph("Detailed Breakdown", section_style))
        story.append(HRFlowable(width="100%", color=DS_BORDER, thickness=1, spaceAfter=8))

        parsed_findings = [_parse_finding(f) for f in findings]

        for engine, f_score, detail in parsed_findings:
            warning = ""
            if f_score >= 50:
                warning = f"  <font color='#{hx(colors.HexColor('#b91c1c'))}'>(WARNING)</font>"
            fc = _score_color(f_score)
            block = KeepTogether([
                Paragraph(
                    f"<font color='#{hx(fc)}'><b>{engine} | {f_score:.0f}%</b></font>{warning}",
                    finding_h
                ),
                Spacer(1, 2),
                Paragraph(detail, finding_body),
                HRFlowable(width="100%", color=colors.HexColor("#e2e8f0"), thickness=1, spaceAfter=8),
            ])
            story.append(block)

        # ─ Footer disclaimer on page 1 ─
        story.append(Spacer(1, 20))
        story.append(HRFlowable(width="100%", color=ACCENT_BLUE, thickness=0.5, spaceAfter=8))
        story.append(Paragraph(
            "This report is generated algorithmically by the DeepScan AI Engine. Scores represent model confidence "
            "based on pixel-level, geometric, frequency, and medieval analysis. Results should be interpreted by a qualified forensic analyst.",
            caption_style
        ))

        # ══════════════════════════════════════
        # SECTION 2 — SENSOR & COMPONENT SCORES
        # ══════════════════════════════════════
        story.append(Spacer(1, 30))
        story.append(Paragraph("Forensic Sensor Deep-Dive", title_style))
        story.append(HRFlowable(width="100%", color=ACCENT_BLUE, thickness=2, spaceAfter=14))

        # ─ Score table ─
        if parsed_findings:
            story.append(Paragraph("Risk Score Matrix", section_style))
            story.append(HRFlowable(width="100%", color=DS_BORDER, thickness=1, spaceAfter=8))

            table_data = [
                [
                    Paragraph("<b>SENSOR / INDICATOR</b>", mk("TH","Normal",fontSize=10,textColor=BLACK,fontName="Helvetica-Bold")),
                    Paragraph("<b>ANOMALY RISK</b>", mk("TH2","Normal",fontSize=10,textColor=BLACK,fontName="Helvetica-Bold",alignment=TA_CENTER)),
                    Paragraph("<b>STATUS</b>", mk("TH3","Normal",fontSize=10,textColor=BLACK,fontName="Helvetica-Bold",alignment=TA_CENTER)),
                    Paragraph("<b>OBSERVATION</b>", mk("TH4","Normal",fontSize=10,textColor=BLACK,fontName="Helvetica-Bold")),
                ]
            ]

            row_styles = [
                ("BACKGROUND",    (0, 0), (-1, 0), DS_LT_BLUE),
                ("GRID",          (0, 0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
                ("ALIGN",         (1, 1), (2, -1), "CENTER"),
                ("VALIGN",        (0, 0), (-1,-1), "MIDDLE"),
                ("TOPPADDING",    (0, 0), (-1,-1), 10),
                ("BOTTOMPADDING", (0, 0), (-1,-1), 10),
                ("LEFTPADDING",    (0, 0), (-1,-1), 8),
            ]

            for i, (engine, f_score, detail) in enumerate(parsed_findings):
                fc = _score_color(f_score)
                status = "⚠ WARNING" if f_score >= 50 else "✓ CLEAR"
                status_color = colors.HexColor("#b91c1c") if f_score >= 50 else colors.HexColor("#15803d")
                bg = colors.HexColor("#fff1f2") if f_score >= 50 else colors.white
                row_styles.append(("BACKGROUND", (0, i+1), (-1, i+1), bg))

                table_data.append([
                    Paragraph(f"<b>{engine}</b>", mk(f"EN{i}","Normal",fontSize=10,textColor=BLACK,fontName="Helvetica-Bold")),
                    Paragraph(
                        f"<font color='#{hx(fc)}'><b>{f_score:.0f}%</b></font>",
                        mk(f"SC{i}","Normal",fontSize=13,fontName="Helvetica-Bold",alignment=TA_CENTER)
                    ),
                    Paragraph(
                        f"<font color='#{hx(status_color)}'><b>{status}</b></font>",
                        mk(f"ST{i}","Normal",fontSize=10,fontName="Helvetica-Bold",alignment=TA_CENTER)
                    ),
                    Paragraph(detail, mk(f"DT{i}","Normal",fontSize=10,textColor=BLACK,leading=14)),
                ])

            risk_table = Table(table_data, colWidths=[2.1*inch, 1.1*inch, 1.1*inch, 2.7*inch])
            risk_table.setStyle(TableStyle(row_styles))
            story.append(risk_table)
            story.append(Spacer(1, 22))

        # ─ Sub-scores grid (if available) ─
        if sub_scores:
            story.append(Paragraph("Component Confidence Grid", section_style))
            story.append(HRFlowable(width="100%", color=DS_BORDER, thickness=1, spaceAfter=8))

            items = list(sub_scores.items())
            grid_data = []
            for i in range(0, len(items), 3):
                chunk = items[i:i+3]
                row = []
                for k, v in chunk:
                    label = k.replace("_", " ").title()
                    try:
                        pct = float(v)
                    except (ValueError, TypeError):
                        pct = 0.0
                    fc = _score_color(100 - pct) if pct > 0 else DS_DIM
                    row.append(Paragraph(
                        f"<font color='#{hx(DS_DIM)}'>{label}</font><br/>"
                         f"<font color='#{hx(fc)}'><b>{pct:.1f}%</b></font>",
                        mk(f"GS{k}","Normal",fontSize=9,leading=14,alignment=TA_CENTER)
                    ))
                while len(row) < 3:
                    row.append(Paragraph("", body_style))
                grid_data.append(row)

            grid = Table(grid_data, colWidths=["33%","34%","33%"])
            grid.setStyle(TableStyle([
                ("BOX",           (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
                ("INNERGRID",     (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
                ("BACKGROUND",    (0,0), (-1,-1), colors.HexColor("#f8fafc")),
                ("ALIGN",         (0,0), (-1,-1), "CENTER"),
                ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
                ("TOPPADDING",    (0,0), (-1,-1), 12),
                ("BOTTOMPADDING", (0,0), (-1,-1), 12),
            ]))
            story.append(grid)
            story.append(Spacer(1, 22))

        # ─ Technical Notes ─
        if technical_text:
            story.append(Paragraph("Technical Analysis Notes", section_style))
            story.append(HRFlowable(width="100%", color=DS_BORDER, thickness=1, spaceAfter=8))
            story.append(Paragraph(technical_text.replace('\n', '<br/>'), body_style))
            story.append(Spacer(1, 16))

        # ══════════════════════════════════════
        # SECTION 3 — VERDICT STAMP
        # ══════════════════════════════════════
        story.append(Spacer(1, 30))
 
        story.append(Paragraph("Final Verdict", title_style))
        story.append(HRFlowable(width="100%", color=ACCENT_BLUE, thickness=2, spaceAfter=20))

        # Large verdict card
        verdict_card_data = [[
            Paragraph(
                f"<font color='#{hx(v_color)}'><b>{verdict}</b></font>",
                mk("VFinal","Normal",fontSize=32,fontName="Helvetica-Bold",leading=38,alignment=TA_CENTER)
            )
        ]]
        verdict_card = Table(verdict_card_data, colWidths=["100%"])
        verdict_card.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), colors.HexColor("#f8fafc")),
            ("ALIGN",         (0,0), (-1,-1), "CENTER"),
            ("TOPPADDING",    (0,0), (-1,-1), 32),
            ("BOTTOMPADDING", (0,0), (-1,-1), 32),
            ("BOX",           (0,0), (-1,-1), 2, v_color),
        ]))
        story.append(verdict_card)
        story.append(Spacer(1, 20))

        # Verdict explanation grid
        verdict_explanation = {
            "AUTHENTIC": "No significant AI generation or manipulation artifacts detected. The image exhibits characteristics consistent with real-world camera capture including natural noise patterns, lens artifacts, and consistent physical lighting.",
            "UNCERTAIN": "The image presents an ambiguous forensic profile. Some anomalies were detected but are not conclusive. Manual review is recommended before drawing definitive conclusions.",
            "POSSIBLE MANIPULATION": "Partial anomalies consistent with localized editing or light AI filtering were detected. While some regions appear authentic, conflicting signals in compression and pixel-level error levels suggest selective manipulation.",
            "LIKELY AI": "Multiple AI generation indicators detected across several forensic domains. The image likely originates from a generative model such as a diffusion model or GAN.",
            "LIKELY FAKE": "Multiple AI generation indicators detected across several forensic domains. The image likely originates from a generative model such as a diffusion model or GAN.",
            "CONFIRMED AI": "Strong and conclusive evidence of AI generation. Multiple sensor layers—frequency, geometry, texture, and statistical—all concur that this content was produced by a generative AI system.",
            "DEFINITELY FAKE": "Strong and conclusive evidence of AI generation. Multiple sensor layers—frequency, geometry, texture, and statistical—all concur that this content was produced by a generative AI system.",
        }
        exp_text = verdict_explanation.get(verdict, summary_text)
        story.append(Paragraph(exp_text, body_style))
        story.append(Spacer(1, 28))

        # Summary stats row  
        stats_data = [[
            Paragraph(
                f"<font color='#64748b'>OVERALL RISK</font><br/><font color='#{hx(v_color)}'><b>{score_val:.0f}%</b></font>",
                mk("Stat1","Normal",fontSize=14,fontName="Helvetica-Bold",leading=20,alignment=TA_CENTER)
            ),
            Paragraph(
                f"<font color='#64748b'>SENSORS FIRED</font><br/><font color='#b91c1c'><b>{len([x for x in parsed_findings if x[1] >= 50])}/{len(parsed_findings)}</b></font>",
                mk("Stat2","Normal",fontSize=14,fontName="Helvetica-Bold",leading=20,alignment=TA_CENTER)
            ),
            Paragraph(
                f"<font color='#64748b'>SCAN ID</font><br/><font color='#1e293b'><b>#{str(scan_id)[:8]}</b></font>",
                mk("Stat3","Normal",fontSize=14,fontName="Helvetica-Bold",leading=20,alignment=TA_CENTER)
            ),
        ]]
        stats_table = Table(stats_data, colWidths=["33%","34%","33%"])
        stats_table.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), colors.HexColor("#f1f5f9")),
            ("ALIGN",         (0,0), (-1,-1), "CENTER"),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
            ("TOPPADDING",    (0,0), (-1,-1), 16),
            ("BOTTOMPADDING", (0,0), (-1,-1), 16),
            ("BOX",           (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
        ]))
        story.append(stats_table)
        story.append(Spacer(1, 30))

        story.append(HRFlowable(width="100%", color=DS_CYAN, thickness=0.5, spaceAfter=8))
        story.append(Paragraph(
            "DeepScan Forensic Intelligence Platform — Automated Forensic Report\n"
            "This document is system-generated and should be reviewed by a qualified forensic analyst. "
            "DeepScan takes no legal liability for actions taken based solely on this report.",
            caption_style
        ))

        # Build with branded header on every page
        try:
            doc.build(story, onFirstPage=_add_page_header, onLaterPages=_add_page_header)
        except Exception as e:
            logger.error(f"Failed to build PDF: {e}")

        buf.seek(0)
        return buf
