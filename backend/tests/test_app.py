import pytest
import os
import json
import tempfile
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from models import init_db
import config.config as cfg


@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    cfg.Config.DB_NAME = db_path
    flask_app = create_app()
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        init_db()
        yield c
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def auth_client(client):
    """Returns (test_client, admin_token) tuple."""
    resp = client.post("/auth/login",
        data=json.dumps({"username": "admin", "password": "admin123"}),
        content_type="application/json")
    token = resp.get_json()["access_token"]
    return client, token


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


# --- Health & Index ---

def test_index(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "running"

def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "healthy"


# --- Clients ---

def test_get_clients_empty(auth_client):
    c, token = auth_client
    assert c.get("/clients", headers=auth_header(token)).get_json() == []

def test_add_client(auth_client):
    c, token = auth_client
    resp = c.post("/clients", data=json.dumps({"name": "Arjun Sharma", "age": 28, "weight": 75.0}),
        content_type="application/json", headers=auth_header(token))
    assert resp.status_code == 201
    assert resp.get_json()["name"] == "Arjun Sharma"
    assert resp.get_json()["membership_status"] == "Active"

def test_add_client_missing_name(auth_client):
    c, token = auth_client
    resp = c.post("/clients", data=json.dumps({"age": 25}),
        content_type="application/json", headers=auth_header(token))
    assert resp.status_code == 400

def test_add_client_blank_name(auth_client):
    c, token = auth_client
    resp = c.post("/clients", data=json.dumps({"name": "   "}),
        content_type="application/json", headers=auth_header(token))
    assert resp.status_code == 400

def test_add_duplicate_client(auth_client):
    c, token = auth_client
    payload = json.dumps({"name": "Duplicate"})
    c.post("/clients", data=payload, content_type="application/json", headers=auth_header(token))
    assert c.post("/clients", data=payload, content_type="application/json", headers=auth_header(token)).status_code == 409

def test_get_client(auth_client):
    c, token = auth_client
    c.post("/clients", data=json.dumps({"name": "Priya"}),
        content_type="application/json", headers=auth_header(token))
    resp = c.get("/clients/Priya", headers=auth_header(token))
    assert resp.status_code == 200
    assert resp.get_json()["name"] == "Priya"

def test_get_client_not_found(auth_client):
    c, token = auth_client
    assert c.get("/clients/Nobody", headers=auth_header(token)).status_code == 404

def test_update_client(auth_client):
    c, token = auth_client
    c.post("/clients", data=json.dumps({"name": "Rahul"}),
        content_type="application/json", headers=auth_header(token))
    resp = c.put("/clients/Rahul", data=json.dumps({"age": 30, "weight": 80.0}),
        content_type="application/json", headers=auth_header(token))
    assert resp.status_code == 200
    assert resp.get_json()["age"] == 30

def test_update_client_not_found(auth_client):
    c, token = auth_client
    assert c.put("/clients/Nobody", data=json.dumps({"age": 25}),
        content_type="application/json", headers=auth_header(token)).status_code == 404

def test_delete_client(auth_client):
    c, token = auth_client
    c.post("/clients", data=json.dumps({"name": "ToDelete"}),
        content_type="application/json", headers=auth_header(token))
    assert c.delete("/clients/ToDelete", headers=auth_header(token)).status_code == 200
    assert c.get("/clients/ToDelete", headers=auth_header(token)).status_code == 404

def test_delete_client_not_found(auth_client):
    c, token = auth_client
    assert c.delete("/clients/Nobody", headers=auth_header(token)).status_code == 404

def test_list_multiple_clients(auth_client):
    c, token = auth_client
    c.post("/clients", data=json.dumps({"name": "A"}),
        content_type="application/json", headers=auth_header(token))
    c.post("/clients", data=json.dumps({"name": "B"}),
        content_type="application/json", headers=auth_header(token))
    names = [cl["name"] for cl in c.get("/clients", headers=auth_header(token)).get_json()]
    assert "A" in names and "B" in names


# --- Programs ---

def test_get_programs(auth_client):
    c, token = auth_client
    programs = c.get("/programs", headers=auth_header(token)).get_json()
    assert "Fat Loss" in programs
    assert "Muscle Gain" in programs
    assert "Beginner" in programs

def test_assign_program(auth_client):
    c, token = auth_client
    c.post("/clients", data=json.dumps({"name": "Kiran"}),
        content_type="application/json", headers=auth_header(token))
    resp = c.post("/clients/Kiran/program", data=json.dumps({"program": "Fat Loss"}),
        content_type="application/json", headers=auth_header(token))
    assert resp.status_code == 200
    assert "Fat Loss" in resp.get_json()["message"]

def test_assign_invalid_program(auth_client):
    c, token = auth_client
    c.post("/clients", data=json.dumps({"name": "Kiran2"}),
        content_type="application/json", headers=auth_header(token))
    resp = c.post("/clients/Kiran2/program", data=json.dumps({"program": "Yoga"}),
        content_type="application/json", headers=auth_header(token))
    assert resp.status_code == 400

def test_assign_program_client_not_found(auth_client):
    c, token = auth_client
    assert c.post("/clients/Nobody/program", data=json.dumps({"program": "Beginner"}),
        content_type="application/json", headers=auth_header(token)).status_code == 404

def test_get_client_program(auth_client):
    c, token = auth_client
    c.post("/clients", data=json.dumps({"name": "Meera"}),
        content_type="application/json", headers=auth_header(token))
    c.post("/clients/Meera/program", data=json.dumps({"program": "Muscle Gain"}),
        content_type="application/json", headers=auth_header(token))
    resp = c.get("/clients/Meera/program", headers=auth_header(token))
    assert resp.status_code == 200
    assert resp.get_json()["program"] == "Muscle Gain"

def test_get_client_program_not_assigned(auth_client):
    c, token = auth_client
    c.post("/clients", data=json.dumps({"name": "Unassigned"}),
        content_type="application/json", headers=auth_header(token))
    resp = c.get("/clients/Unassigned/program", headers=auth_header(token))
    assert resp.status_code == 404
    assert "No program assigned" in resp.get_json()["error"]


# --- Workouts ---

def test_add_workout(auth_client):
    c, token = auth_client
    c.post("/clients", data=json.dumps({"name": "Suresh"}),
        content_type="application/json", headers=auth_header(token))
    resp = c.post("/clients/Suresh/workouts",
        data=json.dumps({"workout_type": "Strength", "duration_min": 45}),
        content_type="application/json", headers=auth_header(token))
    assert resp.status_code == 201

def test_add_workout_missing_type(auth_client):
    c, token = auth_client
    c.post("/clients", data=json.dumps({"name": "Suresh2"}),
        content_type="application/json", headers=auth_header(token))
    assert c.post("/clients/Suresh2/workouts", data=json.dumps({"duration_min": 30}),
        content_type="application/json", headers=auth_header(token)).status_code == 400

def test_add_workout_invalid_type(auth_client):
    c, token = auth_client
    c.post("/clients", data=json.dumps({"name": "Suresh3"}),
        content_type="application/json", headers=auth_header(token))
    assert c.post("/clients/Suresh3/workouts", data=json.dumps({"workout_type": "Dancing"}),
        content_type="application/json", headers=auth_header(token)).status_code == 400

def test_add_workout_invalid_duration(auth_client):
    c, token = auth_client
    c.post("/clients", data=json.dumps({"name": "Suresh4"}),
        content_type="application/json", headers=auth_header(token))
    assert c.post("/clients/Suresh4/workouts",
        data=json.dumps({"workout_type": "Cardio", "duration_min": -10}),
        content_type="application/json", headers=auth_header(token)).status_code == 400

def test_add_workout_client_not_found(auth_client):
    c, token = auth_client
    resp = c.post("/clients/Nobody/workouts",
        data=json.dumps({"workout_type": "Cardio", "duration_min": 30}),
        content_type="application/json", headers=auth_header(token))
    assert resp.status_code == 404

def test_get_workouts(auth_client):
    c, token = auth_client
    c.post("/clients", data=json.dumps({"name": "Deepa"}),
        content_type="application/json", headers=auth_header(token))
    c.post("/clients/Deepa/workouts",
        data=json.dumps({"workout_type": "Cardio", "duration_min": 30}),
        content_type="application/json", headers=auth_header(token))
    resp = c.get("/clients/Deepa/workouts", headers=auth_header(token))
    assert resp.status_code == 200
    assert len(resp.get_json()) == 1
    assert resp.get_json()[0]["workout_type"] == "Cardio"

def test_get_workouts_client_not_found(auth_client):
    c, token = auth_client
    assert c.get("/clients/Nobody/workouts", headers=auth_header(token)).status_code == 404


# --- Progress ---

def test_add_progress(auth_client):
    c, token = auth_client
    c.post("/clients", data=json.dumps({"name": "Nair"}),
        content_type="application/json", headers=auth_header(token))
    resp = c.post("/clients/Nair/progress",
        data=json.dumps({"week": "Week 1", "adherence": 85}),
        content_type="application/json", headers=auth_header(token))
    assert resp.status_code == 201

def test_progress_boundary_values(auth_client):
    c, token = auth_client
    c.post("/clients", data=json.dumps({"name": "Nair2"}),
        content_type="application/json", headers=auth_header(token))
    assert c.post("/clients/Nair2/progress", data=json.dumps({"adherence": 0}),
        content_type="application/json", headers=auth_header(token)).status_code == 201
    assert c.post("/clients/Nair2/progress", data=json.dumps({"adherence": 100}),
        content_type="application/json", headers=auth_header(token)).status_code == 201

def test_progress_invalid_adherence(auth_client):
    c, token = auth_client
    c.post("/clients", data=json.dumps({"name": "Nair3"}),
        content_type="application/json", headers=auth_header(token))
    assert c.post("/clients/Nair3/progress", data=json.dumps({"adherence": 150}),
        content_type="application/json", headers=auth_header(token)).status_code == 400

def test_progress_missing_adherence(auth_client):
    c, token = auth_client
    c.post("/clients", data=json.dumps({"name": "Nair4"}),
        content_type="application/json", headers=auth_header(token))
    assert c.post("/clients/Nair4/progress", data=json.dumps({"week": "Week 1"}),
        content_type="application/json", headers=auth_header(token)).status_code == 400

def test_add_progress_client_not_found(auth_client):
    c, token = auth_client
    resp = c.post("/clients/Nobody/progress",
        data=json.dumps({"week": "Week 1", "adherence": 75}),
        content_type="application/json", headers=auth_header(token))
    assert resp.status_code == 404

def test_get_progress(auth_client):
    c, token = auth_client
    c.post("/clients", data=json.dumps({"name": "Sharma"}),
        content_type="application/json", headers=auth_header(token))
    c.post("/clients/Sharma/progress",
        data=json.dumps({"week": "Week 1", "adherence": 70}),
        content_type="application/json", headers=auth_header(token))
    c.post("/clients/Sharma/progress",
        data=json.dumps({"week": "Week 2", "adherence": 80}),
        content_type="application/json", headers=auth_header(token))
    data = c.get("/clients/Sharma/progress", headers=auth_header(token)).get_json()
    assert len(data) == 2
    assert data[0]["adherence"] == 70
    assert data[1]["adherence"] == 80

def test_get_progress_client_not_found(auth_client):
    c, token = auth_client
    assert c.get("/clients/Nobody/progress", headers=auth_header(token)).status_code == 404


# --- Auth ---

def test_admin_seeded_on_startup(client):
    resp = client.post("/auth/login",
        data=json.dumps({"username": "admin", "password": "admin123"}),
        content_type="application/json")
    assert resp.status_code == 200
    assert "access_token" in resp.get_json()
    assert resp.get_json()["role"] == "Admin"

def test_login_invalid_credentials(client):
    resp = client.post("/auth/login",
        data=json.dumps({"username": "admin", "password": "wrongpassword"}),
        content_type="application/json")
    assert resp.status_code == 401

def test_login_missing_fields(client):
    resp = client.post("/auth/login",
        data=json.dumps({"username": "admin"}),
        content_type="application/json")
    assert resp.status_code == 400

def test_me_endpoint(auth_client):
    c, token = auth_client
    resp = c.get("/auth/me", headers=auth_header(token))
    assert resp.status_code == 200
    assert resp.get_json()["username"] == "admin"
    assert resp.get_json()["role"] == "Admin"

def test_me_no_token(client):
    assert client.get("/auth/me").status_code == 401

def test_register_user(auth_client):
    c, token = auth_client
    resp = c.post("/auth/register",
        data=json.dumps({"username": "trainer1", "password": "pass123", "role": "Trainer"}),
        content_type="application/json",
        headers=auth_header(token))
    assert resp.status_code == 201
    assert "trainer1" in resp.get_json()["message"]

def test_register_duplicate_user(auth_client):
    c, token = auth_client
    payload = json.dumps({"username": "trainer2", "password": "pass123", "role": "Trainer"})
    c.post("/auth/register", data=payload, content_type="application/json", headers=auth_header(token))
    resp = c.post("/auth/register", data=payload, content_type="application/json", headers=auth_header(token))
    assert resp.status_code == 409

def test_register_invalid_role(auth_client):
    c, token = auth_client
    resp = c.post("/auth/register",
        data=json.dumps({"username": "user1", "password": "pass123", "role": "SuperUser"}),
        content_type="application/json",
        headers=auth_header(token))
    assert resp.status_code == 400

def test_register_requires_admin(client):
    resp = client.post("/auth/login",
        data=json.dumps({"username": "admin", "password": "admin123"}),
        content_type="application/json")
    admin_token = resp.get_json()["access_token"]
    client.post("/auth/register",
        data=json.dumps({"username": "trainer3", "password": "pass", "role": "Trainer"}),
        content_type="application/json",
        headers=auth_header(admin_token))
    resp2 = client.post("/auth/login",
        data=json.dumps({"username": "trainer3", "password": "pass"}),
        content_type="application/json")
    trainer_token = resp2.get_json()["access_token"]
    resp3 = client.post("/auth/register",
        data=json.dumps({"username": "newuser", "password": "pass", "role": "Trainer"}),
        content_type="application/json",
        headers=auth_header(trainer_token))
    assert resp3.status_code == 403


# --- Exercises ---

def test_add_exercise(auth_client):
    c, token = auth_client
    c.post("/clients", data=json.dumps({"name": "ExClient"}),
        content_type="application/json", headers=auth_header(token))
    c.post("/clients/ExClient/workouts",
        data=json.dumps({"workout_type": "Strength", "duration_min": 45}),
        content_type="application/json", headers=auth_header(token))
    # get the actual workout id
    workouts = c.get("/clients/ExClient/workouts", headers=auth_header(token)).get_json()
    workout_id = workouts[0]["id"]
    resp = c.post(f"/clients/ExClient/workouts/{workout_id}/exercises",
        data=json.dumps({"name": "Bench Press", "sets": 3, "reps": 10, "weight_kg": 60}),
        content_type="application/json",
        headers=auth_header(token))
    assert resp.status_code == 201
    assert "Bench Press" in resp.get_json()["message"]

def test_add_exercise_missing_name(auth_client):
    c, token = auth_client
    c.post("/clients", data=json.dumps({"name": "ExClient2"}),
        content_type="application/json", headers=auth_header(token))
    c.post("/clients/ExClient2/workouts",
        data=json.dumps({"workout_type": "Cardio", "duration_min": 30}),
        content_type="application/json", headers=auth_header(token))
    workouts = c.get("/clients/ExClient2/workouts", headers=auth_header(token)).get_json()
    workout_id = workouts[0]["id"]
    resp = c.post(f"/clients/ExClient2/workouts/{workout_id}/exercises",
        data=json.dumps({"sets": 3}),
        content_type="application/json",
        headers=auth_header(token))
    assert resp.status_code == 400

def test_add_exercise_client_not_found(auth_client):
    c, token = auth_client
    resp = c.post("/clients/Nobody/workouts/1/exercises",
        data=json.dumps({"name": "Squat"}),
        content_type="application/json",
        headers=auth_header(token))
    assert resp.status_code == 404

def test_add_exercise_workout_not_found(auth_client):
    c, token = auth_client
    c.post("/clients", data=json.dumps({"name": "ExClient3"}),
        content_type="application/json", headers=auth_header(token))
    resp = c.post("/clients/ExClient3/workouts/999/exercises",
        data=json.dumps({"name": "Squat"}),
        content_type="application/json",
        headers=auth_header(token))
    assert resp.status_code == 404

def test_get_exercises(auth_client):
    c, token = auth_client
    c.post("/clients", data=json.dumps({"name": "ExClient4"}),
        content_type="application/json", headers=auth_header(token))
    c.post("/clients/ExClient4/workouts",
        data=json.dumps({"workout_type": "Strength", "duration_min": 60}),
        content_type="application/json", headers=auth_header(token))
    workouts = c.get("/clients/ExClient4/workouts", headers=auth_header(token)).get_json()
    workout_id = workouts[0]["id"]
    c.post(f"/clients/ExClient4/workouts/{workout_id}/exercises",
        data=json.dumps({"name": "Deadlift", "sets": 4, "reps": 6}),
        content_type="application/json",
        headers=auth_header(token))
    resp = c.get(f"/clients/ExClient4/workouts/{workout_id}/exercises", headers=auth_header(token))
    assert resp.status_code == 200
    assert len(resp.get_json()) == 1
    assert resp.get_json()[0]["name"] == "Deadlift"

def test_get_exercises_no_token(client):
    assert client.get("/clients/Anyone/workouts/1/exercises").status_code == 401


# --- Metrics ---

def test_add_metrics(auth_client):
    c, token = auth_client
    c.post("/clients", data=json.dumps({"name": "MetClient"}),
        content_type="application/json", headers=auth_header(token))
    resp = c.post("/clients/MetClient/metrics",
        data=json.dumps({"weight_kg": 75.0, "body_fat_pct": 18.5, "date": "2026-03-09"}),
        content_type="application/json",
        headers=auth_header(token))
    assert resp.status_code == 201

def test_add_metrics_client_not_found(auth_client):
    c, token = auth_client
    resp = c.post("/clients/Nobody/metrics",
        data=json.dumps({"weight_kg": 70.0}),
        content_type="application/json",
        headers=auth_header(token))
    assert resp.status_code == 404

def test_add_metrics_missing_fields(auth_client):
    c, token = auth_client
    c.post("/clients", data=json.dumps({"name": "MetClient2"}),
        content_type="application/json", headers=auth_header(token))
    resp = c.post("/clients/MetClient2/metrics",
        data=json.dumps({"date": "2026-03-09"}),
        content_type="application/json",
        headers=auth_header(token))
    assert resp.status_code == 400

def test_add_metrics_invalid_body_fat(auth_client):
    c, token = auth_client
    c.post("/clients", data=json.dumps({"name": "MetClient3"}),
        content_type="application/json", headers=auth_header(token))
    resp = c.post("/clients/MetClient3/metrics",
        data=json.dumps({"weight_kg": 70.0, "body_fat_pct": 150}),
        content_type="application/json",
        headers=auth_header(token))
    assert resp.status_code == 400

def test_get_metrics(auth_client):
    c, token = auth_client
    c.post("/clients", data=json.dumps({"name": "MetClient4"}),
        content_type="application/json", headers=auth_header(token))
    c.post("/clients/MetClient4/metrics",
        data=json.dumps({"weight_kg": 80.0, "date": "2026-03-01"}),
        content_type="application/json",
        headers=auth_header(token))
    c.post("/clients/MetClient4/metrics",
        data=json.dumps({"weight_kg": 79.0, "date": "2026-03-08"}),
        content_type="application/json",
        headers=auth_header(token))
    resp = c.get("/clients/MetClient4/metrics", headers=auth_header(token))
    assert resp.status_code == 200
    assert len(resp.get_json()) == 2

def test_get_metrics_no_token(client):
    assert client.get("/clients/Anyone/metrics").status_code == 401


# --- PDF Report ---

def test_download_report(auth_client):
    c, token = auth_client
    c.post("/clients", data=json.dumps({"name": "ReportClient"}),
        content_type="application/json", headers=auth_header(token))
    resp = c.get("/clients/ReportClient/report", headers=auth_header(token))
    assert resp.status_code == 200
    assert resp.content_type == "application/pdf"

def test_download_report_client_not_found(auth_client):
    c, token = auth_client
    resp = c.get("/clients/Nobody/report", headers=auth_header(token))
    assert resp.status_code == 404

def test_download_report_no_token(client):
    assert client.get("/clients/Anyone/report").status_code == 401