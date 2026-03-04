import io
import time
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from loguru import logger


# Brand colors
DS_BG = HexColor("#0a0a0f")
DS_RED = HexColor("#ff3c00")
DS_CYAN = HexColor("#00f5ff")
DS_GREEN = HexColor("#39ff14")
DS_YELLOW = HexColor("#ffd700")
DS_SILVER = HexColor("#e0e0e0")
DS_ORANGE = HexColor("#ff8c00")

VERDICT_COLORS = {
    "AUTHENTIC": DS_GREEN,
    "UNCERTAIN": DS_YELLOW,
    "LIKELY_FAKE": DS_ORANGE,
    "DEFINITELY_FAKE": DS_RED,
}


class PdfGenerator:
    """Generate a comprehensive forensic PDF report for a DeepScan analysis."""

    def create_report(self, data: dict) -> io.BytesIO:
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=letter)
        w, h = letter  # 612 x 792

        try:
            self._draw_page_1(c, data, w, h)
            c.showPage()
            self._draw_page_2(c, data, w, h)
            c.showPage()
            self._draw_page_3(c, data, w, h)
        except Exception as e:
            logger.error(f"PDF generation error: {e}")

        c.save()
        buf.seek(0)
        return buf

    # ───────────────────── Page 1: Header + AACS Score + Verdict ─────────────
    def _draw_page_1(self, c, data, w, h):
        # Dark background
        c.setFillColor(DS_BG)
        c.rect(0, 0, w, h, fill=1)

        # Top bar
        c.setFillColor(DS_RED)
        c.rect(0, h - 60, w, 60, fill=1)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 22)
        c.drawString(30, h - 42, "DEEPSCAN — FORENSIC ANALYSIS REPORT")

        # Report metadata
        y = h - 90
        c.setFont("Helvetica", 10)
        c.setFillColor(DS_SILVER)
        c.drawString(30, y, f"Report ID: {data.get('id', 'N/A')}")
        c.drawString(300, y, f"Generated: {time.strftime('%Y-%m-%d %H:%M UTC')}")
        y -= 16
        c.drawString(30, y, f"File: {data.get('original_filename', data.get('filename', 'N/A'))}")
        c.drawString(300, y, f"Type: {data.get('file_type', 'N/A').upper()}")
        y -= 16
        c.drawString(30, y, f"Analysis Time: {data.get('elapsed_seconds', 0)}s")

        # ─── AACS Score Circle ───
        aacs = data.get("aacs_score", data.get("score", 0))
        verdict = data.get("verdict", "UNKNOWN")
        v_color = VERDICT_COLORS.get(verdict, DS_SILVER)

        # Large score display
        y -= 50
        c.setFillColor(v_color)
        c.setFont("Helvetica-Bold", 72)
        score_text = f"{aacs:.0f}"
        c.drawCentredString(w / 2, y - 20, score_text)
        c.setFont("Helvetica", 14)
        c.drawCentredString(w / 2, y - 40, "AACS SCORE (0-100)")

        # Verdict badge
        y -= 70
        badge_w = 220
        badge_h = 36
        bx = (w - badge_w) / 2
        c.setFillColor(v_color)
        c.roundRect(bx, y, badge_w, badge_h, 6, fill=1)
        c.setFillColor(black)
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(w / 2, y + 10, verdict.replace("_", " "))

        # ─── Sub-Scores ───
        y -= 60
        c.setFillColor(DS_CYAN)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(30, y, "SUB-SCORE BREAKDOWN")
        y -= 5
        c.setStrokeColor(DS_CYAN)
        c.line(30, y, w - 30, y)

        sub_scores = data.get("sub_scores", {})
        labels = [
            ("MAS", "Media Authenticity Score", 0.30),
            ("PPS", "Physiological Plausibility", 0.25),
            ("IRS", "Information Reliability", 0.20),
            ("AAS", "Acoustic Anomaly Score", 0.15),
            ("CVS", "Context Verification", 0.10),
        ]
        y -= 30
        for abbr, name, weight in labels:
            val = sub_scores.get(abbr.lower(), 0)
            # Label
            c.setFillColor(DS_SILVER)
            c.setFont("Helvetica-Bold", 11)
            c.drawString(40, y, f"{abbr} — {name}")
            c.setFont("Helvetica", 10)
            c.drawString(320, y, f"Weight: {weight:.0%}")
            # Bar background
            bar_x, bar_y, bar_w, bar_h = 410, y - 2, 150, 14
            c.setFillColor(HexColor("#1a1a2e"))
            c.rect(bar_x, bar_y, bar_w, bar_h, fill=1)
            # Bar fill
            fill_w = bar_w * (val / 100.0)
            bar_color = DS_GREEN if val < 30 else DS_YELLOW if val < 60 else DS_ORANGE if val < 85 else DS_RED
            c.setFillColor(bar_color)
            c.rect(bar_x, bar_y, fill_w, bar_h, fill=1)
            # Score text
            c.setFillColor(white)
            c.setFont("Helvetica-Bold", 9)
            c.drawCentredString(bar_x + bar_w + 20, y, f"{val:.1f}")
            y -= 28

        # ─── CDCF Fusion ───
        fusion = data.get("fusion", {})
        y -= 20
        c.setFillColor(DS_CYAN)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(30, y, "CDCF FUSION ANALYSIS")
        y -= 5
        c.line(30, y, w - 30, y)
        y -= 20
        c.setFillColor(DS_SILVER)
        c.setFont("Helvetica", 10)
        c.drawString(40, y, f"Multiplier: {fusion.get('multiplier', 1.0):.2f}x")
        y -= 16
        contradictions = fusion.get("contradictions", [])
        c.drawString(40, y, f"Contradictions: {len(contradictions)}")
        if contradictions:
            y -= 16
            c.drawString(60, y, ", ".join(contradictions))
        y -= 16
        c.drawString(40, y, f"Note: {fusion.get('confidence_note', 'N/A')}")

        # Footer
        c.setFillColor(HexColor("#333333"))
        c.rect(0, 0, w, 30, fill=1)
        c.setFillColor(DS_SILVER)
        c.setFont("Helvetica", 8)
        c.drawCentredString(w / 2, 10, "DeepScan AACS v1.0 — Team Bug Bytes — HackHive 2.0 — Datta Meghe College of Engineering, Airoli")

    # ───────────────────── Page 2: Findings + Forensics ──────────────────────
    def _draw_page_2(self, c, data, w, h):
        c.setFillColor(DS_BG)
        c.rect(0, 0, w, h, fill=1)

        # Header
        c.setFillColor(DS_RED)
        c.rect(0, h - 40, w, 40, fill=1)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(30, h - 28, "DETECTION FINDINGS")

        y = h - 70
        findings = data.get("findings", [])
        for i, finding in enumerate(findings[:12]):
            engine = finding.get("engine", "Unknown")
            score = finding.get("score", 0)
            detail = finding.get("detail", "")
            color = DS_GREEN if score < 30 else DS_YELLOW if score < 60 else DS_ORANGE if score < 85 else DS_RED

            c.setFillColor(color)
            c.circle(40, y + 4, 4, fill=1)
            c.setFillColor(DS_SILVER)
            c.setFont("Helvetica-Bold", 10)
            c.drawString(52, y, f"[{engine}] Score: {score:.1f}")
            c.setFont("Helvetica", 9)
            c.setFillColor(HexColor("#aaaaaa"))
            # Truncate long detail
            detail_display = detail[:80] + "..." if len(detail) > 80 else detail
            c.drawString(52, y - 14, detail_display)
            y -= 36
            if y < 80:
                break

        # ─── Forensics Summary ───
        forensics = data.get("forensics", {})
        y -= 20
        c.setFillColor(DS_CYAN)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(30, y, "FORENSIC ANALYSIS")
        y -= 5
        c.setStrokeColor(DS_CYAN)
        c.line(30, y, w - 30, y)
        y -= 25

        forensic_items = [
            ("ELA", forensics.get("ela", {}).get("ela_score", "N/A"),
             forensics.get("ela", {}).get("analysis_note", "")),
            ("FFT", forensics.get("fft", {}).get("fft_score", "N/A") if forensics.get("fft") else "N/A",
             "Frequency-domain manipulation detection"),
            ("Noise", forensics.get("noise", {}).get("noise_score", "N/A") if forensics.get("noise") else "N/A",
             "Noise pattern consistency analysis"),
        ]

        for name, score_val, note in forensic_items:
            c.setFillColor(DS_SILVER)
            c.setFont("Helvetica-Bold", 11)
            c.drawString(40, y, f"{name} Score: {score_val}")
            c.setFont("Helvetica", 9)
            c.setFillColor(HexColor("#999999"))
            c.drawString(200, y, note[:60])
            y -= 22

        # ─── Heartbeat / rPPG ───
        heartbeat = data.get("heartbeat", {})
        if heartbeat and heartbeat.get("heart_rate"):
            y -= 20
            c.setFillColor(DS_RED)
            c.setFont("Helvetica-Bold", 14)
            c.drawString(30, y, "rPPG PHYSIOLOGICAL ANALYSIS")
            y -= 5
            c.setStrokeColor(DS_RED)
            c.line(30, y, w - 30, y)
            y -= 25
            c.setFillColor(DS_SILVER)
            c.setFont("Helvetica", 11)
            c.drawString(40, y, f"Detected Heart Rate: {heartbeat.get('heart_rate', 0):.0f} BPM")
            y -= 18
            c.drawString(40, y, f"Signal Confidence: {heartbeat.get('confidence', 0):.0%}")
            y -= 18
            note = heartbeat.get("analysis_note", "")
            if note:
                c.drawString(40, y, f"Note: {note}")

        # Footer
        c.setFillColor(HexColor("#333333"))
        c.rect(0, 0, w, 30, fill=1)
        c.setFillColor(DS_SILVER)
        c.setFont("Helvetica", 8)
        c.drawCentredString(w / 2, 10, "DeepScan AACS v1.0 — Confidential Forensic Report — Page 2")

    # ───────────────────── Page 3: Narrative + Metadata ──────────────────────
    def _draw_page_3(self, c, data, w, h):
        c.setFillColor(DS_BG)
        c.rect(0, 0, w, h, fill=1)

        # Header
        c.setFillColor(DS_RED)
        c.rect(0, h - 40, w, 40, fill=1)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(30, h - 28, "AI NARRATIVE EXPLANATION")

        y = h - 70
        narrative = data.get("narrative", {})

        sections = [
            ("Summary", narrative.get("summary", "N/A")),
            ("Simple Explanation (ELI5)", narrative.get("eli5", "N/A")),
            ("Technical Analysis", narrative.get("technical", "N/A")),
        ]

        for title, text in sections:
            c.setFillColor(DS_CYAN)
            c.setFont("Helvetica-Bold", 12)
            c.drawString(30, y, title)
            y -= 18

            # Word-wrap the text
            c.setFillColor(DS_SILVER)
            c.setFont("Helvetica", 9)
            words = text.split()
            line = ""
            for word in words:
                test = f"{line} {word}".strip()
                if c.stringWidth(test, "Helvetica", 9) < w - 80:
                    line = test
                else:
                    c.drawString(40, y, line)
                    y -= 13
                    line = word
                if y < 80:
                    break
            if line:
                c.drawString(40, y, line)
                y -= 13
            y -= 15
            if y < 80:
                break

        # ─── Metadata ───
        metadata = data.get("metadata", {})
        if metadata and y > 200:
            y -= 10
            c.setFillColor(DS_CYAN)
            c.setFont("Helvetica-Bold", 14)
            c.drawString(30, y, "FILE METADATA")
            y -= 5
            c.setStrokeColor(DS_CYAN)
            c.line(30, y, w - 30, y)
            y -= 20

            c.setFont("Helvetica", 9)
            c.setFillColor(DS_SILVER)
            important_keys = ["FileType", "ImageSize", "Software", "CreateDate",
                              "ModifyDate", "Model", "GPSLatitude", "GPSLongitude",
                              "Duration", "AudioBitrate", "VideoFrameRate"]
            for key in important_keys:
                if key in metadata and y > 60:
                    val = str(metadata[key])[:60]
                    c.drawString(40, y, f"{key}: {val}")
                    y -= 14

        # ─── AACS Formula ───
        if y > 120:
            y -= 20
            c.setFillColor(DS_YELLOW)
            c.setFont("Helvetica-Bold", 11)
            c.drawString(30, y, "AACS Formula: ((0.30×MAS) + (0.25×PPS) + (0.20×IRS) + (0.15×AAS) + (0.10×CVS)) × CDCF")

        # Footer
        c.setFillColor(HexColor("#333333"))
        c.rect(0, 0, w, 30, fill=1)
        c.setFillColor(DS_SILVER)
        c.setFont("Helvetica", 8)
        c.drawCentredString(w / 2, 10, "DeepScan AACS v1.0 — Team Bug Bytes — Page 3 — END OF REPORT")