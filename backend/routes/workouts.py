from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from datetime import date
from models import get_db


workouts_bp = Blueprint("workouts", __name__)

VALID_WORKOUT_TYPES = ["Strength", "Hypertrophy", "Cardio", "Mobility", "HIIT", "Circuit"]


def client_exists(conn, name):
    return conn.execute("SELECT 1 FROM clients WHERE name=?", (name,)).fetchone()


@workouts_bp.route("/clients/<string:name>/workouts", methods=["GET"])
@jwt_required()
def get_workouts(name):
    conn = get_db()
    if not client_exists(conn, name):
        conn.close()
        return jsonify({"error": f"Client '{name}' not found"}), 404
    workouts = conn.execute(
        "SELECT * FROM workouts WHERE client_name=? ORDER BY date DESC", (name,)
    ).fetchall()
    conn.close()
    return jsonify([dict(w) for w in workouts]), 200


@workouts_bp.route("/clients/<string:name>/workouts", methods=["POST"])
@jwt_required()
def add_workout(name):
    data = request.get_json() or {}
    workout_type = data.get("workout_type")
    if not workout_type:
        return jsonify({"error": "workout_type is required"}), 400
    if workout_type not in VALID_WORKOUT_TYPES:
        return jsonify({"error": f"Invalid workout_type. Choose from: {VALID_WORKOUT_TYPES}"}), 400
    duration = data.get("duration_min", 60)
    if not isinstance(duration, int) or duration <= 0:
        return jsonify({"error": "duration_min must be a positive integer"}), 400
    conn = get_db()
    if not client_exists(conn, name):
        conn.close()
        return jsonify({"error": f"Client '{name}' not found"}), 404
    conn.execute(
        "INSERT INTO workouts (client_name, date, workout_type, duration_min, notes) VALUES (?,?,?,?,?)",
        (name, data.get("date", date.today().isoformat()), workout_type, duration, data.get("notes", ""))
    )
    conn.commit()
    conn.close()
    return jsonify({"message": f"Workout logged for {name}"}), 201
