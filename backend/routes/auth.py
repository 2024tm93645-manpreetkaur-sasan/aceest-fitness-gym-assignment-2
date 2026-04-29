from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
import bcrypt
from models import get_db


auth_bp = Blueprint("auth", __name__)

VALID_ROLES = {"Admin", "Trainer", "Client"}


def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())


def seed_admin():
    conn = get_db()
    existing = conn.execute("SELECT id FROM users WHERE username = 'admin'").fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ("admin", hash_password("admin123"), "Admin")
        )
        conn.commit()
    conn.close()


@auth_bp.route("/auth/register", methods=["POST"])
@jwt_required()
def register():
    claims = get_jwt()
    if claims.get("role") != "Admin":
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    role = data.get("role") or "Trainer"

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400
    if role not in VALID_ROLES:
        return jsonify({"error": f"Invalid role. Choose from: {list(VALID_ROLES)}"}), 400

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, hash_password(password), role)
        )
        conn.commit()
        return jsonify({"message": f"User '{username}' created with role '{role}'"}), 201
    except Exception:
        return jsonify({"error": f"Username '{username}' already exists"}), 409
    finally:
        conn.close()


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()

    if not user or not check_password(password, user["password"]):
        return jsonify({"error": "Invalid username or password"}), 401

    token = create_access_token(
        identity=username,
        additional_claims={"role": user["role"]}
    )
    return jsonify({"access_token": token, "role": user["role"]}), 200


@auth_bp.route("/auth/me", methods=["GET"])
@jwt_required()
def me():
    username = get_jwt_identity()
    claims = get_jwt()
    return jsonify({"username": username, "role": claims.get("role")}), 200
