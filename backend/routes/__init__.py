from routes.clients import clients_bp
from routes.programs import programs_bp
from routes.workouts import workouts_bp
from routes.progress import progress_bp
from routes.auth import auth_bp, seed_admin
from routes.exercises import exercises_bp
from routes.metrics import metrics_bp
from routes.report import report_bp

__all__ = [
    "clients_bp", "programs_bp", "workouts_bp", "progress_bp",
    "auth_bp", "exercises_bp", "metrics_bp", "report_bp", "seed_admin"
]


def register_routes(app):
    app.register_blueprint(clients_bp)
    app.register_blueprint(programs_bp)
    app.register_blueprint(workouts_bp)
    app.register_blueprint(progress_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(exercises_bp)
    app.register_blueprint(metrics_bp)
    app.register_blueprint(report_bp)

    with app.app_context():
        from models import init_db
        init_db()
        seed_admin()
