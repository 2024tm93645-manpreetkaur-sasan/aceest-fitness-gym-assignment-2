from flask import Blueprint, jsonify, request
import sqlite3
from models import get_db
from flask_jwt_extended import jwt_required


clients_bp = Blueprint("clients", __name__)


@clients_bp.route("/clients", methods=["GET"])
@jwt_required()
def get_clients():
    conn = get_db()
    clients = conn.execute("SELECT * FROM clients ORDER BY name").fetchall()
    conn.close()
    return jsonify([dict(c) for c in clients]), 200


@clients_bp.route("/clients", methods=["POST"])
@jwt_required()
def add_client():
    data = request.get_json()
    name = (data or {}).get("name", "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO clients (name, age, weight, program, membership_status) VALUES (?,?,?,?,?)",
            (name, data.get("age"), data.get("weight"), data.get("program"), data.get("membership_status", "Active"))
        )
        conn.commit()
        return jsonify(dict(conn.execute("SELECT * FROM clients WHERE name=?", (name,)).fetchone())), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": f"Client '{name}' already exists"}), 409
    finally:
        conn.close()


@clients_bp.route("/clients/<string:name>", methods=["GET"])
@jwt_required()
def get_client(name):
    conn = get_db()
    client = conn.execute("SELECT * FROM clients WHERE name=?", (name,)).fetchone()
    conn.close()
    return (jsonify(dict(client)), 200) if client else (jsonify({"error": f"Client '{name}' not found"}), 404)


@clients_bp.route("/clients/<string:name>", methods=["PUT"])
@jwt_required()
def update_client(name):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    conn = get_db()
    client = conn.execute("SELECT * FROM clients WHERE name=?", (name,)).fetchone()
    if not client:
        conn.close()
        return jsonify({"error": f"Client '{name}' not found"}), 404
    updated = {
        **dict(client),
        **{k: data[k] for k in ["age", "weight", "program", "membership_status"] if k in data}
    }
    conn.execute(
        "UPDATE clients SET age=?, weight=?, program=?, membership_status=? WHERE name=?",
        (updated["age"], updated["weight"], updated["program"], updated["membership_status"], name)
    )
    conn.commit()
    result = conn.execute("SELECT * FROM clients WHERE name=?", (name,)).fetchone()
    conn.close()
    return jsonify(dict(result)), 200


@clients_bp.route("/clients/<string:name>", methods=["DELETE"])
@jwt_required()
def delete_client(name):
    conn = get_db()
    result = conn.execute("DELETE FROM clients WHERE name=?", (name,))
    conn.commit()
    conn.close()
    return (
        (jsonify({"message": f"Client '{name}' deleted"}), 200)
        if result.rowcount
        else (jsonify({"error": f"Client '{name}' not found"}), 404)
    )
