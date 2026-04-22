import os


class Config:
    DB_NAME = os.environ.get("DB_NAME", "aceest_fitness.db")
    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = int(os.environ.get("PORT", 5005))
    DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "aceest-secret-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES", 3600))
    PROGRAMS = {
        "Fat Loss": {"workouts": ["Full Body HIIT", "Circuit Training"], "calories": 2000},
        "Muscle Gain": {"workouts": ["Push/Pull/Legs", "Upper/Lower Split"], "calories": 3200},
        "Beginner": {"workouts": ["Full Body 3x/week", "Mobility"], "calories": 2500},
    }
