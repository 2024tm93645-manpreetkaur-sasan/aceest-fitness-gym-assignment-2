from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from datetime import date
from models import get_db


progress_bp = Blueprint("progress", __name__)


def client_exists(conn, name):
    return conn.execute("SELECT 1 FROM clients WHERE name=?", (name,)).fetchone()


@progress_bp.route("/clients/<string:name>/progress", methods=["GET"])
@jwt_required()
def get_progress(name):
    conn = get_db()
    if not client_exists(conn, name):
        conn.close()
        return jsonify({"error": f"Client '{name}' not found"}), 404
    progress = conn.execute(
        "SELECT week, adherence FROM progress WHERE client_name=? ORDER BY id", (name,)
    ).fetchall()
    conn.close()
    return jsonify([dict(p) for p in progress]), 200


@progress_bp.route("/clients/<string:name>/progress", methods=["POST"])
@jwt_required()
def add_progress(name):
    data = request.get_json() or {}
    adherence = data.get("adherence")
    if adherence is None:
        return jsonify({"error": "adherence (0-100) is required"}), 400
    if not isinstance(adherence, int) or not (0 <= adherence <= 100):
        return jsonify({"error": "adherence must be an integer between 0 and 100"}), 400
    conn = get_db()
    if not client_exists(conn, name):
        conn.close()
        return jsonify({"error": f"Client '{name}' not found"}), 404
    week = data.get("week") or f"Week {date.today().isocalendar()[1]}"
    conn.execute(
        "INSERT INTO progress (client_name, week, adherence) VALUES (?,?,?)", (name, week, adherence)
    )
    conn.commit()
    conn.close()
    return jsonify({"message": f"Progress recorded for {name}", "week": week, "adherence": adherence}), 201
