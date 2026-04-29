from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from datetime import date
from models import get_db


metrics_bp = Blueprint("metrics", __name__)


@metrics_bp.route("/clients/<string:name>/metrics", methods=["GET"])
@jwt_required()
def get_metrics(name):
    conn = get_db()
    client = conn.execute("SELECT name FROM clients WHERE name = ?", (name,)).fetchone()
    if not client:
        conn.close()
        return jsonify({"error": f"Client '{name}' not found"}), 404

    rows = conn.execute(
        "SELECT * FROM metrics WHERE client_name = ? ORDER BY date ASC", (name,)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows]), 200


@metrics_bp.route("/clients/<string:name>/metrics", methods=["POST"])
@jwt_required()
def add_metrics(name):
    conn = get_db()
    client = conn.execute("SELECT name FROM clients WHERE name = ?", (name,)).fetchone()
    if not client:
        conn.close()
        return jsonify({"error": f"Client '{name}' not found"}), 404

    data = request.get_json() or {}
    weight_kg = data.get("weight_kg")
    body_fat_pct = data.get("body_fat_pct")
    notes = data.get("notes", "")
    entry_date = data.get("date", str(date.today()))

    if weight_kg is None and body_fat_pct is None:
        conn.close()
        return jsonify({"error": "At least one of weight_kg or body_fat_pct is required"}), 400

    if body_fat_pct is not None and not (0 <= body_fat_pct <= 100):
        conn.close()
        return jsonify({"error": "body_fat_pct must be between 0 and 100"}), 400

    conn.execute(
        "INSERT INTO metrics (client_name, date, weight_kg, body_fat_pct, notes) VALUES (?, ?, ?, ?, ?)",
        (name, entry_date, weight_kg, body_fat_pct, notes)
    )
    conn.commit()
    conn.close()
    return jsonify({"message": f"Metrics recorded for '{name}'"}), 201
