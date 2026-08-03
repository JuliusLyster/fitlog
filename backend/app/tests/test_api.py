"""
Integrationstests for FastAPI-endpoints.

Bruger en separat in-memory SQLite-database (via DATABASE_URL-miljøvariabel,
sat FØR app importeres) så testene ikke rører den rigtige fitlog.db,
og kan køre helt isoleret og hurtigt.
"""

import os
import uuid
from unittest.mock import Mock, patch

import requests

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


@pytest.fixture
def user_id():
    # Unikt navn pr. test, så tests der deler samme in-memory database
    # ikke ved et uheld genbruger hinandens data (create_user returnerer
    # den eksisterende bruger, hvis navnet allerede findes).
    unique_name = f"testbruger_{uuid.uuid4().hex[:8]}"
    response = client.post("/users/", json={"name": unique_name})
    assert response.status_code == 200
    return response.json()["id"]


def test_root_returns_ok():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_and_get_user(user_id):
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    assert response.json()["name"].startswith("testbruger_")


def test_get_nonexistent_user_returns_404():
    response = client.get("/users/999999")
    assert response.status_code == 404


def test_create_meal_calculates_macros(user_id):
    response = client.post(
        "/meals/", json={"user_id": user_id, "food_name": "kylling", "grams": 200}
    )

    assert response.status_code == 200
    data = response.json()
    # Kylling ligger i den lokale fødevaredatabase: 165 kcal / 31g protein pr. 100g
    assert data["calories"] == 330.0
    assert data["protein_g"] == 62.0
    assert data["source"] == "local"


def test_create_meal_for_unknown_food_uses_openfoodfacts(user_id):
    from app.services.openfoodfacts import OFF_SEARCH_A_LICIOUS_URL

    fake_response = Mock()
    fake_response.ok = True
    fake_response.json.return_value = {
        "products": [
            {
                "nutriments": {
                    "energy-kcal_100g": 300,
                    "proteins_100g": 15,
                    "carbohydrates_100g": 20,
                    "fat_100g": 10,
                }
            }
        ]
    }

    def fake_get(url, *args, **kwargs):
        if url == OFF_SEARCH_A_LICIOUS_URL:
            raise requests.RequestException("search-a-licious er nede")
        return fake_response

    with patch("app.services.openfoodfacts.requests.get", side_effect=fake_get):
        response = client.post(
            "/meals/",
            json={"user_id": user_id, "food_name": "et helt ukendt produkt", "grams": 100},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["calories"] == 300.0
    assert data["source"] == "openfoodfacts"


def test_create_meal_for_unknown_user_returns_404():
    response = client.post(
        "/meals/", json={"user_id": 999999, "food_name": "kylling", "grams": 100}
    )
    assert response.status_code == 404


def test_create_and_list_workout(user_id):
    payload = {"user_id": user_id, "workout_type": "løb", "duration_minutes": 30}
    response = client.post("/workouts/", json=payload)
    assert response.status_code == 200
    # Standardbruger vejer 75kg (default): 9.8 MET * 3.5 * 75 / 200 * 30 = 385.9 kcal
    assert response.json()["calories_burned"] == 385.9

    list_response = client.get(f"/workouts/{user_id}")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["workout_type"] == "løb"


def test_workout_calories_scale_with_user_weight():
    unique_name = f"testbruger_{uuid.uuid4().hex[:8]}"
    user_response = client.post("/users/", json={"name": unique_name, "weight_kg": 100})
    heavy_user_id = user_response.json()["id"]

    payload = {"user_id": heavy_user_id, "workout_type": "løb", "duration_minutes": 30}
    response = client.post("/workouts/", json=payload)

    # 9.8 MET * 3.5 * 100 / 200 * 30 = 514.5 kcal
    assert response.json()["calories_burned"] == 514.5


def test_delete_workout(user_id):
    payload = {"user_id": user_id, "workout_type": "cykling", "duration_minutes": 45}
    create_response = client.post("/workouts/", json=payload)
    workout_id = create_response.json()["id"]

    delete_response = client.delete(f"/workouts/{workout_id}")
    assert delete_response.status_code == 200

    second_delete = client.delete(f"/workouts/{workout_id}")
    assert second_delete.status_code == 404


def test_dashboard_weekly_averages_with_no_data(user_id):
    response = client.get(f"/dashboard/{user_id}/weekly-averages")
    assert response.status_code == 200
    assert response.json()["avg_calories_in"] == 0.0


def test_dashboard_today_with_no_data(user_id):
    response = client.get(f"/dashboard/{user_id}/today")
    assert response.status_code == 200
    data = response.json()
    assert data["calories_in"] == 0.0
    assert data["workout_count"] == 0


def test_dashboard_today_reflects_logged_meal_and_workout(user_id):
    client.post("/meals/", json={"user_id": user_id, "food_name": "kylling", "grams": 100})
    client.post(
        "/workouts/",
        json={"user_id": user_id, "workout_type": "løb", "duration_minutes": 30},
    )

    response = client.get(f"/dashboard/{user_id}/today")
    data = response.json()

    assert data["calories_in"] == 165.0
    assert data["workout_count"] == 1
    assert data["calories_out"] > 0


def test_dashboard_recommendation_falls_back_gracefully(user_id):
    import requests

    error = requests.RequestException("no ollama")
    with patch("app.services.llm.requests.post", side_effect=error):
        response = client.get(f"/dashboard/{user_id}/recommendation")

    assert response.status_code == 200
    assert "recommendation" in response.json()
