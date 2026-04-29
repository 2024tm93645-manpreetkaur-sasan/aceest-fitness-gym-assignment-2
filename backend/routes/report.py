from flask import Blueprint, send_file, jsonify
from flask_jwt_extended import jwt_required
from models import get_db
from utils.pdf import generate_client_report
import io


report_bp = Blueprint("report", __name__)


@report_bp.route("/clients/<string:name>/report", methods=["GET"])
@jwt_required()
def download_report(name):
    conn = get_db()
    client = conn.execute("SELECT * FROM clients WHERE name = ?", (name,)).fetchone()
    if not client:
        conn.close()
        return jsonify({"error": f"Client '{name}' not found"}), 404

    workouts = conn.execute(
        "SELECT * FROM workouts WHERE client_name = ? ORDER BY date DESC", (name,)
    ).fetchall()
    progress = conn.execute(
        "SELECT * FROM progress WHERE client_name = ? ORDER BY id ASC", (name,)
    ).fetchall()
    metrics = conn.execute(
        "SELECT * FROM metrics WHERE client_name = ? ORDER BY date ASC", (name,)
    ).fetchall()
    conn.close()

    pdf_bytes = generate_client_report(
        dict(client),
        [dict(w) for w in workouts],
        [dict(p) for p in progress],
        [dict(m) for m in metrics]
    )

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{name}_report.pdf"
    )
