import os
import sqlite3
import json
import requests
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

PORT = int(os.environ.get("PORT", 5001))
DB_PATH = os.path.join(os.path.dirname(__file__), "hotspots.db")

AQICN_TOKEN = "demo"


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


@app.route("/data/air-quality")
def air_quality():
    lat = request.args.get("lat")
    lng = request.args.get("lng")

    if not lat or not lng:
        return jsonify({"error": "Missing lat/lng parameters"}), 400

    try:
        url = f"https://api.waqi.info/feed/geo:{lat};{lng}/?token={AQICN_TOKEN}"
        response = requests.get(url, timeout=10)
        data = response.json()

        if data.get("status") != "ok":
            return jsonify({"error": "Could not fetch data for this location", "raw": data}), 404

        iaqi = data["data"].get("iaqi", {})
        result = {
            "station": data["data"].get("city", {}).get("name", "Unknown Station"),
            "aqi": data["data"].get("aqi", "N/A"),
            "time": data["data"].get("time", {}).get("s", "N/A"),
            "co": iaqi.get("co", {}).get("v", "N/A"),
            "pm25": iaqi.get("pm25", {}).get("v", "N/A"),
            "pm10": iaqi.get("pm10", {}).get("v", "N/A"),
            "no2": iaqi.get("no2", {}).get("v", "N/A"),
            "o3": iaqi.get("o3", {}).get("v", "N/A"),
            "so2": iaqi.get("so2", {}).get("v", "N/A"),
            "dominentpol": data["data"].get("dominentpol", "N/A"),
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


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=PORT, debug=False)
