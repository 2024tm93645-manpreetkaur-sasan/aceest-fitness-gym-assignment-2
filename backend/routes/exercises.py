from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from models import get_db


exercises_bp = Blueprint("exercises", __name__)


@exercises_bp.route("/clients/<string:name>/workouts/<int:workout_id>/exercises", methods=["GET"])
@jwt_required()
def get_exercises(name, workout_id):
    conn = get_db()
    client = conn.execute("SELECT name FROM clients WHERE name = ?", (name,)).fetchone()
    if not client:
        conn.close()
        return jsonify({"error": f"Client '{name}' not found"}), 404

    workout = conn.execute(
        "SELECT id FROM workouts WHERE id = ? AND client_name = ?", (workout_id, name)
    ).fetchone()
    if not workout:
        conn.close()
        return jsonify({"error": f"Workout {workout_id} not found for client '{name}'"}), 404

    rows = conn.execute(
        "SELECT * FROM exercises WHERE workout_id = ?", (workout_id,)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows]), 200


@exercises_bp.route("/clients/<string:name>/workouts/<int:workout_id>/exercises", methods=["POST"])
@jwt_required()
def add_exercise(name, workout_id):
    conn = get_db()
    client = conn.execute("SELECT name FROM clients WHERE name = ?", (name,)).fetchone()
    if not client:
        conn.close()
        return jsonify({"error": f"Client '{name}' not found"}), 404

    workout = conn.execute(
        "SELECT id FROM workouts WHERE id = ? AND client_name = ?", (workout_id, name)
    ).fetchone()
    if not workout:
        conn.close()
        return jsonify({"error": f"Workout {workout_id} not found for client '{name}'"}), 404

    data = request.get_json() or {}
    exercise_name = (data.get("name") or "").strip()
    if not exercise_name:
        conn.close()
        return jsonify({"error": "Exercise name is required"}), 400

    sets = data.get("sets")
    reps = data.get("reps")
    weight_kg = data.get("weight_kg")

    conn.execute(
        "INSERT INTO exercises (workout_id, name, sets, reps, weight_kg) VALUES (?, ?, ?, ?, ?)",
        (workout_id, exercise_name, sets, reps, weight_kg)
    )
    conn.commit()
    conn.close()
    return jsonify({"message": f"Exercise '{exercise_name}' added to workout {workout_id}"}), 201
