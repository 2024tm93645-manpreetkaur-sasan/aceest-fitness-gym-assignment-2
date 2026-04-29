import pytest
import requests
import os

BASE_URL = os.environ.get("APP_URL", "http://localhost:5005")
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
TEST_CLIENT = "Acceptance Test Client"


@pytest.fixture(scope="session")
def auth_token():
    """Get JWT token for authenticated requests."""
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "username": ADMIN_USERNAME,
        "password": ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json().get("access_token")
    assert token, "No access_token returned from login"
    return token


@pytest.fixture(scope="session")
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(scope="session")
def test_client(auth_headers):
    """Create a test client to use across tests."""
    requests.post(f"{BASE_URL}/clients", headers=auth_headers, json={
        "name": TEST_CLIENT,
        "age": 30,
        "weight": 70,
        "program": "Weight Loss",
        "membership_status": "Active"
    })
    return TEST_CLIENT


@pytest.fixture(scope="session")
def test_workout_id(auth_headers, test_client):
    """Create a test workout and return its id."""
    response = requests.post(
        f"{BASE_URL}/clients/{test_client}/workouts",
        headers=auth_headers,
        json={"workout_type": "Strength", "duration_min": 45}
    )
    workouts = requests.get(
        f"{BASE_URL}/clients/{test_client}/workouts",
        headers=auth_headers
    ).json()
    return workouts[0]["id"] if workouts else None


# ── Health ─────────────────────────────────────────────────────────────────────

class TestHealth:

    def test_health_endpoint_returns_200(self):
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200

    def test_health_response_contains_status(self):
        response = requests.get(f"{BASE_URL}/health")
        assert "status" in response.json()


# ── Auth ───────────────────────────────────────────────────────────────────────

class TestAuth:

    def test_login_with_valid_credentials(self):
        response = requests.post(f"{BASE_URL}/auth/login", json={
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_login_with_invalid_credentials(self):
        response = requests.post(f"{BASE_URL}/auth/login", json={
            "username": "wronguser",
            "password": "wrongpass"
        })
        assert response.status_code == 401

    def test_login_with_missing_fields(self):
        response = requests.post(f"{BASE_URL}/auth/login", json={})
        assert response.status_code == 400

    def test_access_protected_route_without_token(self):
        response = requests.get(f"{BASE_URL}/clients")
        assert response.status_code == 401

    def test_access_protected_route_with_invalid_token(self):
        response = requests.get(f"{BASE_URL}/clients", headers={
            "Authorization": "Bearer invalidtoken"
        })
        assert response.status_code == 422

    def test_get_current_user(self, auth_headers):
        response = requests.get(f"{BASE_URL}/auth/me", headers=auth_headers)
        assert response.status_code == 200
        assert "username" in response.json()


# ── Clients ────────────────────────────────────────────────────────────────────

class TestClients:

    def test_get_clients_returns_list(self, auth_headers):
        response = requests.get(f"{BASE_URL}/clients", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_client(self, auth_headers):
        response = requests.post(f"{BASE_URL}/clients", headers=auth_headers, json={
            "name": "Acceptance Test Client",
            "age": 30,
            "weight": 70,
            "program": "Weight Loss",
            "membership_status": "Active"
        })
        assert response.status_code in [201, 409]

    def test_create_client_missing_required_fields(self, auth_headers):
        response = requests.post(f"{BASE_URL}/clients", headers=auth_headers, json={})
        assert response.status_code == 400

    def test_get_client_by_name(self, auth_headers, test_client):
        response = requests.get(f"{BASE_URL}/clients/{test_client}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["name"] == test_client

    def test_get_nonexistent_client_returns_404(self, auth_headers):
        response = requests.get(f"{BASE_URL}/clients/NonExistentClient999", headers=auth_headers)
        assert response.status_code == 404


# ── Programs ───────────────────────────────────────────────────────────────────

class TestPrograms:

    def test_get_programs_returns_list(self, auth_headers):
        response = requests.get(f"{BASE_URL}/programs", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_assign_program_to_client(self, auth_headers, test_client):
        programs = requests.get(f"{BASE_URL}/programs", headers=auth_headers).json()
        response = requests.post(
            f"{BASE_URL}/clients/{test_client}/program",
            headers=auth_headers,
            json={"program": programs[0]}
        )
        assert response.status_code == 200


# ── Workouts ───────────────────────────────────────────────────────────────────

class TestWorkouts:

    def test_add_workout(self, auth_headers, test_client):
        response = requests.post(
            f"{BASE_URL}/clients/{test_client}/workouts",
            headers=auth_headers,
            json={"workout_type": "Cardio", "duration_min": 30}
        )
        assert response.status_code == 201

    def test_get_workouts_returns_list(self, auth_headers, test_client):
        response = requests.get(
            f"{BASE_URL}/clients/{test_client}/workouts",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_add_workout_invalid_type(self, auth_headers, test_client):
        response = requests.post(
            f"{BASE_URL}/clients/{test_client}/workouts",
            headers=auth_headers,
            json={"workout_type": "InvalidType", "duration_min": 30}
        )
        assert response.status_code == 400


# ── Exercises ──────────────────────────────────────────────────────────────────

class TestExercises:

    def test_add_exercise_to_workout(self, auth_headers, test_client, test_workout_id):
        if not test_workout_id:
            pytest.skip("No workout available")
        response = requests.post(
            f"{BASE_URL}/clients/{test_client}/workouts/{test_workout_id}/exercises",
            headers=auth_headers,
            json={"name": "Squat", "sets": 3, "reps": 10, "weight_kg": 60}
        )
        assert response.status_code == 201

    def test_get_exercises_returns_list(self, auth_headers, test_client, test_workout_id):
        if not test_workout_id:
            pytest.skip("No workout available")
        response = requests.get(
            f"{BASE_URL}/clients/{test_client}/workouts/{test_workout_id}/exercises",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)


# ── Metrics ────────────────────────────────────────────────────────────────────

class TestMetrics:

    def test_add_metrics(self, auth_headers, test_client):
        response = requests.post(
            f"{BASE_URL}/clients/{test_client}/metrics",
            headers=auth_headers,
            json={"weight_kg": 70.5, "body_fat_pct": 18.0}
        )
        assert response.status_code == 201

    def test_get_metrics_returns_list(self, auth_headers, test_client):
        response = requests.get(
            f"{BASE_URL}/clients/{test_client}/metrics",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)


# ── Progress ───────────────────────────────────────────────────────────────────

class TestProgress:

    def test_add_progress(self, auth_headers, test_client):
        response = requests.post(
            f"{BASE_URL}/clients/{test_client}/progress",
            headers=auth_headers,
            json={"adherence": 85}
        )
        assert response.status_code == 201

    def test_get_progress_returns_list(self, auth_headers, test_client):
        response = requests.get(
            f"{BASE_URL}/clients/{test_client}/progress",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)