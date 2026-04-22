from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from models import get_db
from config import Config


programs_bp = Blueprint("programs", __name__)


@programs_bp.route("/programs", methods=["GET"])
@jwt_required()
def get_programs():
    return jsonify(list(Config.PROGRAMS.keys())), 200


@programs_bp.route("/clients/<string:name>/program", methods=["GET"])
@jwt_required()
def get_client_program(name):
    conn = get_db()
    client = conn.execute("SELECT name, program FROM clients WHERE name=?", (name,)).fetchone()
    conn.close()
    if not client:
        return jsonify({"error": f"Client '{name}' not found"}), 404
    program = client["program"]
    if not program:
        return jsonify({"error": f"No program assigned to {name}"}), 404
    return jsonify({"client": name, "program": program, "details": Config.PROGRAMS.get(program, {})}), 200


@programs_bp.route("/clients/<string:name>/program", methods=["POST"])
@jwt_required()
def assign_program(name):
    data = request.get_json()
    program = (data or {}).get("program")
    if not program:
        return jsonify({"error": "program is required"}), 400
    if program not in Config.PROGRAMS:
        return jsonify({"error": f"Invalid program. Choose from: {list(Config.PROGRAMS.keys())}"}), 400
    conn = get_db()
    result = conn.execute("UPDATE clients SET program=? WHERE name=?", (program, name))
    conn.commit()
    conn.close()
    return (
        (jsonify({"message": f"'{program}' assigned to {name}", "details": Config.PROGRAMS[program]}), 200)
        if result.rowcount
        else (jsonify({"error": f"Client '{name}' not found"}), 404)
    )
