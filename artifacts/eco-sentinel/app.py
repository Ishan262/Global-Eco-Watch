import os
import sqlite3
import json
import requests
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from datetime import datetime
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

app = Flask(__name__)
CORS(app)

PORT = int(os.environ.get("PORT", 5001))
DB_PATH = os.path.join(os.path.dirname(__file__), "hotspots.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hotspots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            pollution_type TEXT NOT NULL,
            description TEXT NOT NULL,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/get_air_data")
def get_air_data():
    lat = request.args.get("lat")
    lng = request.args.get("lng")

    if not lat or not lng:
        return jsonify({"error": "Missing lat/lng parameters"}), 400

    try:
        url = (
            "https://air-quality-api.open-meteo.com/v1/air-quality"
            f"?latitude={lat}&longitude={lng}"
            "&current=pm2_5,carbon_monoxide,nitrogen_dioxide,ozone,sulphur_dioxide,pm10,us_aqi"
            "&timezone=auto"
        )
        response = requests.get(url, timeout=10)
        data = response.json()

        if "current" not in data:
            return jsonify({"error": "No air quality data available for this location"}), 404

        current = data["current"]

        def fmt(val, decimals=1):
            return round(val, decimals) if val is not None else "N/A"

        result = {
            "station": f"{float(lat):.4f}°, {float(lng):.4f}°",
            "aqi": fmt(current.get("us_aqi"), 0),
            "time": current.get("time", "N/A"),
            "co": fmt(current.get("carbon_monoxide")),
            "pm25": fmt(current.get("pm2_5")),
            "pm10": fmt(current.get("pm10")),
            "no2": fmt(current.get("nitrogen_dioxide")),
            "o3": fmt(current.get("ozone")),
            "so2": fmt(current.get("sulphur_dioxide")),
            "lat": lat,
            "lng": lng,
        }
        return jsonify(result)

    except requests.Timeout:
        return jsonify({"error": "Request timed out. Try again."}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/data/reports", methods=["GET"])
def get_reports():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM hotspots ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@app.route("/data/reports", methods=["POST"])
def create_report():
    data = request.get_json()

    name = (data.get("name") or "").strip()
    pollution_type = (data.get("pollution_type") or "").strip()
    description = (data.get("description") or "").strip()
    lat = data.get("lat")
    lng = data.get("lng")

    if not all([name, pollution_type, description, lat, lng]):
        return jsonify({"error": "All fields are required"}), 400

    created_at = datetime.utcnow().isoformat() + "Z"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO hotspots (name, pollution_type, description, lat, lng, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (name, pollution_type, description, float(lat), float(lng), created_at),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return jsonify({
        "id": new_id,
        "name": name,
        "pollution_type": pollution_type,
        "description": description,
        "lat": lat,
        "lng": lng,
        "created_at": created_at,
    }), 201


@app.route("/data/reports/<int:report_id>", methods=["DELETE"])
def delete_report(report_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM hotspots WHERE id = ?", (report_id,))
    conn.commit()
    affected = cursor.rowcount
    conn.close()

    if affected == 0:
        return jsonify({"error": "Report not found"}), 404

    return jsonify({"success": True})


@app.route("/export_pdf", methods=["GET"])
def export_pdf():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM hotspots ORDER BY created_at DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    buffer = BytesIO()
    page_w, page_h = A4

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2.2 * cm,
        bottomMargin=2.2 * cm,
    )

    # ── Colour palette ──────────────────────────────────────
    DARK   = colors.HexColor("#0f172a")
    MID    = colors.HexColor("#1e293b")
    ACCENT = colors.HexColor("#10b981")
    MUTED  = colors.HexColor("#475569")
    RED    = colors.HexColor("#dc2626")
    WHITE  = colors.white
    LIGHT  = colors.HexColor("#f1f5f9")
    ROW_A  = colors.HexColor("#f8fafc")
    ROW_B  = colors.white

    styles = getSampleStyleSheet()

    def style(name, **kw):
        return ParagraphStyle(name, **kw)

    title_style = style("Title",
        fontName="Helvetica-Bold", fontSize=15, textColor=DARK,
        leading=20, alignment=TA_CENTER, spaceAfter=4)

    subtitle_style = style("Sub",
        fontName="Helvetica", fontSize=9, textColor=MUTED,
        alignment=TA_CENTER, spaceAfter=2)

    section_style = style("Section",
        fontName="Helvetica-Bold", fontSize=9, textColor=ACCENT,
        spaceBefore=14, spaceAfter=4, leading=12)

    body_style = style("Body",
        fontName="Helvetica", fontSize=8.5, textColor=DARK,
        leading=12)

    footer_style = style("Footer",
        fontName="Helvetica", fontSize=7.5, textColor=MUTED,
        alignment=TA_CENTER)

    cell_style = style("Cell",
        fontName="Helvetica", fontSize=8, textColor=DARK, leading=11)

    cell_wrap = style("CellWrap",
        fontName="Helvetica", fontSize=7.5, textColor=DARK, leading=11, wordWrap="CJK")

    generated_on = datetime.utcnow().strftime("%d %B %Y, %H:%M UTC")

    story = []

    # ── Header block ───────────────────────────────────────
    story.append(Paragraph("ECOSENTINEL", style("logo",
        fontName="Helvetica-Bold", fontSize=9, textColor=ACCENT,
        alignment=TA_CENTER, spaceAfter=6, letterSpacing=3)))

    story.append(Paragraph(
        "MUNICIPAL ENVIRONMENTAL ACCOUNTABILITY REPORT",
        title_style))

    story.append(HRFlowable(
        width="100%", thickness=2, color=ACCENT, spaceAfter=6))

    story.append(Paragraph(
        f"Prepared by EcoSentinel Monitoring System &nbsp;·&nbsp; Generated: {generated_on}",
        subtitle_style))
    story.append(Paragraph(
        "CONFIDENTIAL — For authorized municipal and government use only.",
        style("Conf", fontName="Helvetica-Oblique", fontSize=8,
              textColor=RED, alignment=TA_CENTER, spaceAfter=10)))

    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0"), spaceAfter=12))

    # ── Summary section ────────────────────────────────────
    story.append(Paragraph("EXECUTIVE SUMMARY", section_style))
    story.append(Paragraph(
        f"This report compiles <b>{len(rows)}</b> citizen-submitted pollution hotspot report(s) "
        "recorded via the EcoSentinel environmental monitoring platform. Each entry has been "
        "timestamped and geolocated at the time of submission. Municipal officers are requested "
        "to investigate flagged locations and take corrective action in accordance with "
        "applicable environmental regulations.",
        body_style))
    story.append(Spacer(1, 10))

    # ── Data table ─────────────────────────────────────────
    story.append(Paragraph("REPORTED POLLUTION HOTSPOTS", section_style))

    if not rows:
        story.append(Paragraph(
            "No pollution hotspots have been reported at this time.", body_style))
    else:
        header = [
            Paragraph("<b>#</b>", cell_style),
            Paragraph("<b>Date (UTC)</b>", cell_style),
            Paragraph("<b>Coordinates</b>", cell_style),
            Paragraph("<b>Pollution Type</b>", cell_style),
            Paragraph("<b>Citizen / Description</b>", cell_style),
        ]
        table_data = [header]

        for i, row in enumerate(rows):
            ts = row["created_at"][:10] if row["created_at"] else "—"
            coord = f"{float(row['lat']):.4f}°\n{float(row['lng']):.4f}°"
            citizen = f"{row['name']}\n{row['description']}"
            bg = ROW_A if i % 2 == 0 else ROW_B
            table_data.append([
                Paragraph(str(row["id"]), cell_style),
                Paragraph(ts, cell_style),
                Paragraph(coord, cell_wrap),
                Paragraph(row["pollution_type"], cell_wrap),
                Paragraph(citizen, cell_wrap),
            ])

        col_widths = [1 * cm, 2.4 * cm, 2.6 * cm, 3.8 * cm, 7.5 * cm]

        tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
        tbl.setStyle(TableStyle([
            # Header row
            ("BACKGROUND",  (0, 0), (-1, 0), DARK),
            ("TEXTCOLOR",   (0, 0), (-1, 0), WHITE),
            ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",    (0, 0), (-1, 0), 8),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 7),
            ("TOPPADDING",    (0, 0), (-1, 0), 7),
            # Accent left border on header
            ("LINEAFTER",   (0, 0), (0, 0), 2, ACCENT),
            # Body rows
            ("FONTSIZE",    (0, 1), (-1, -1), 8),
            ("TOPPADDING",  (0, 1), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("GRID",        (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [ROW_A, ROW_B]),
            ("VALIGN",      (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(tbl)

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0"), spaceAfter=8))

    # ── Footer ─────────────────────────────────────────────
    story.append(Paragraph(
        f"EcoSentinel Environmental Monitoring Platform &nbsp;·&nbsp; "
        f"Report generated {generated_on} &nbsp;·&nbsp; "
        f"Total records: {len(rows)}",
        footer_style))
    story.append(Paragraph(
        "This document is intended solely for municipal and governmental use. "
        "Unauthorised distribution is prohibited.",
        style("FootSub", fontName="Helvetica-Oblique", fontSize=7,
              textColor=colors.HexColor("#94a3b8"), alignment=TA_CENTER)))

    doc.build(story)
    buffer.seek(0)

    filename = f"EcoSentinel_Municipal_Report_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.pdf"
    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=PORT, debug=False)
