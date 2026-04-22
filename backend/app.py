from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from config import Config
from models import init_db
from routes import register_routes


def create_app():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = Config.JWT_SECRET_KEY
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = Config.JWT_ACCESS_TOKEN_EXPIRES

    JWTManager(app)
    register_routes(app)

    @app.route("/health")
    def health():
        return jsonify({"status": "healthy"}), 200

    @app.route("/")
    def index():
        return jsonify({"app": "ACEest Fitness & Gym", "version": "2.0.1", "status": "running"}), 200

    return app


if __name__ == "__main__":
    app = create_app()
    init_db()
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
