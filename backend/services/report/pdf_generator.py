import io
import time
from loguru import logger

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# Brand Colors (Clean, Corporate, Minimalist)
DS_BLUE = colors.HexColor("#0f172a")      # Dark slate
DS_ACCENT = colors.HexColor("#3b82f6")    # Royal Blue
DS_GRAY = colors.HexColor("#64748b")      # Slate gray
DS_LIGHT_GRAY = colors.HexColor("#f1f5f9")
DS_GREEN = colors.HexColor("#22c55e")     # Authentic
DS_YELLOW = colors.HexColor("#eab308")    # Uncertain
DS_ORANGE = colors.HexColor("#f97316")    # Likely Fake
DS_RED = colors.HexColor("#ef4444")       # Definitely fake

VERDICT_COLORS = {
    "AUTHENTIC": DS_GREEN,
    "UNCERTAIN": DS_YELLOW,
    "LIKELY_FAKE": DS_ORANGE,
    "DEFINITELY_FAKE": DS_RED,
}

class PdfGenerator:
    """Generates a professional, print-friendly forensic PDF report for DeepScan."""

    def create_report(self, data: dict) -> io.BytesIO:
        buf = io.BytesIO()
        
        # Setup document
        doc = SimpleDocTemplate(
            buf,
            pagesize=letter,
            rightMargin=inch,
            leftMargin=inch,
            topMargin=inch,
            bottomMargin=inch
        )
        
        styles = getSampleStyleSheet()
        
        # Custom Styles
        title_style = ParagraphStyle(
            name="ReportTitle",
            parent=styles["Heading1"],
            fontSize=22,
            textColor=DS_BLUE,
            spaceAfter=6,
            alignment=TA_LEFT,
            fontName="Helvetica-Bold"
        )
        subtitle_style = ParagraphStyle(
            name="ReportSubtitle",
            parent=styles["Normal"],
            fontSize=11,
            textColor=DS_GRAY,
            spaceAfter=20
        )
        section_h_style = ParagraphStyle(
            name="SectionHeader",
            parent=styles["Heading2"],
            fontSize=14,
            textColor=DS_ACCENT,
            spaceBefore=20,
            spaceAfter=10,
            fontName="Helvetica-Bold"
        )
        normal_style = ParagraphStyle(
            name="CustomNormal",
            parent=styles["Normal"],
            fontSize=10,
            textColor=DS_BLUE,
            leading=14
        )
        
        story = []
        
        # ─── HEADER ───
        story.append(Paragraph("DEEPSCAN FORENSIC ANALYSIS", title_style))
        report_id = data.get("id", "N/A")
        date_str = time.strftime('%Y-%m-%d %H:%M UTC')
        story.append(Paragraph(f"Official Report ID: <b>{report_id}</b> | Generated on: {date_str}", subtitle_style))
        story.append(HRFlowable(width="100%", color=DS_LIGHT_GRAY, thickness=2, spaceAfter=20))
        
        # ─── METADATA TABLE ───
        file_name = data.get("original_filename", data.get("filename", "N/A"))
        file_type = data.get("file_type", "N/A").upper()
        
        meta_data = [
            ["File Analyzed:", file_name],
            ["File Type:", file_type],
            ["Analysis Duration:", f"{data.get('elapsed_seconds', 0)} seconds"]
        ]
        
        meta_table = Table(meta_data, colWidths=[1.5*inch, 4.5*inch])
        meta_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0,0), (0,-1), DS_GRAY),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 20))
        
        # ─── SCORE & VERDICT ───
        raw_score = data.get("aacs_score", data.get("score", 0))
        # Ensure we capture exact float or int provided, cleanly formatted to 1 decimal place if needed
        score_val = float(raw_score) if raw_score is not None else 0.0
        
        verdict = data.get("verdict", "UNKNOWN")
        v_color = VERDICT_COLORS.get(verdict, DS_GRAY)
        
        score_data = [
            [Paragraph("<font size=14 color='#64748b'><b>AI Probability Score</b></font>", normal_style), 
             Paragraph("<font size=14 color='#64748b'><b>System Verdict</b></font>", normal_style)],
            [Paragraph(f"<font size=48><b>{score_val:.1f}%</b></font>", normal_style),
             Paragraph(f"<font size=24 color='{v_color.hexval()}'><b>{verdict.replace('_', ' ')}</b></font>", normal_style)]
        ]
        
        score_table = Table(score_data, colWidths=[3*inch, 3*inch])
        score_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ('BACKGROUND', (0,0), (-1,-1), DS_LIGHT_GRAY),
            ('BOX', (0,0), (-1,-1), 1, DS_LIGHT_GRAY)
        ]))
        story.append(score_table)
        story.append(Spacer(1, 25))
        
        # ─── NARRATIVE SUMMARY ───
        story.append(Paragraph("EXECUTIVE SUMMARY", section_h_style))
        narrative = data.get("narrative", {})
        
        eli5_text = narrative.get("eli5", "No summary available.")
        story.append(Paragraph(f"<b>Overview:</b> {eli5_text}", normal_style))
        story.append(Spacer(1, 10))
        
        tech_text = narrative.get("technical", "No technical details available.")
        story.append(Paragraph(f"<b>Technical Detail:</b> {tech_text}", normal_style))
        story.append(Spacer(1, 20))
        
        # ─── KEY FORENSIC FINDINGS ───
        findings = data.get("findings", [])
        if findings:
            story.append(Paragraph("FORENSIC SENSOR BREAKDOWN", section_h_style))
            
            # Table Header
            find_data = [["Sensor Area", "Risk Score", "Detailed Observation"]]
            
            for f in findings:
                engine = f.get("engine", "N/A")
                f_score = float(f.get("score", 0))
                detail = f.get("detail", "N/A")
                find_data.append([
                    Paragraph(f"<b>{engine}</b>", normal_style),
                    Paragraph(f"<b>{f_score:.1f}%</b>", normal_style),
                    Paragraph(detail, normal_style)
                ])
                
            find_table = Table(find_data, colWidths=[1.2*inch, 1*inch, 3.8*inch])
            find_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), DS_BLUE),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 10),
                ('TOPPADDING', (0,0), (-1,0), 10),
                ('GRID', (0,0), (-1,-1), 0.5, DS_LIGHT_GRAY),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('PADDING', (0,1), (-1,-1), 8),
            ]))
            story.append(find_table)
        
        story.append(Spacer(1, 20))
        
        # ─── SUB-SCORES METRICS ───
        sub_scores = data.get("sub_scores", {})
        if sub_scores:
            story.append(Paragraph("COMPONENT CONFIDENCE SCORES", section_h_style))
            subs_data = [["Metric", "Confidence %", "Metric", "Confidence %"]]
            
            # Map sub scores nicely
            items = []
            for k, v in sub_scores.items():
                label = k.upper()
                items.append(f"{label}:")
                items.append(f"{float(v):.1f}%")
                
            # Pad to even
            if len(items) % 4 != 0:
                items.extend(["", ""])
                
            rows = [items[i:i+4] for i in range(0, len(items), 4)]
            subs_data.extend(rows)
            
            sub_table = Table(subs_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            sub_table.setStyle(TableStyle([
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BACKGROUND', (0,0), (-1,0), DS_LIGHT_GRAY),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('GRID', (0,0), (-1,-1), 0.5, colors.whitesmoke)
            ]))
            story.append(sub_table)

        # ─── FOOTER INFO ───
        story.append(Spacer(1, 40))
        story.append(HRFlowable(width="100%", color=DS_LIGHT_GRAY, thickness=1, spaceAfter=10))
        disclaimer = "<font color='#94a3b8' size=8>This report is generated algorithmically by the DeepScan Artificial Intelligence Engine. Probability scores represent model confidence based on pixel-level, geometric, frequency, and temporal analysis. Results should be interpreted by an analyst.</font>"
        story.append(Paragraph(disclaimer, normal_style))

        # Build PDF
        try:
            doc.build(story)
        except Exception as e:
            logger.error(f"Failed to build PDF layout: {e}")
            
        buf.seek(0)
        return buf