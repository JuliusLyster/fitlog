"""
Lille hjælpe-modul der samler alle kald til FitLog-backenden ét sted.

Alle Streamlit-sider (app.py + pages/) importerer funktioner herfra i
stedet for selv at kalde `requests` direkte. Det gør det nemt at ændre
API-URL'en ét sted, og holder sideskitserne (app.py, pages/*) fri for
gentaget requests-kode.
"""

import os

import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://backend:8000")


def _get(path: str, params: dict | None = None, timeout: int = 10):
    try:
        response = requests.get(f"{API_BASE_URL}{path}", params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        st.error(f"Kunne ikke kontakte backend ({path}): {exc}")
        return None


def _post(path: str, json: dict):
    try:
        response = requests.post(f"{API_BASE_URL}{path}", json=json, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        st.error(f"Kunne ikke kontakte backend ({path}): {exc}")
        return None


def _delete(path: str):
    try:
        response = requests.delete(f"{API_BASE_URL}{path}", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        st.error(f"Kunne ikke kontakte backend ({path}): {exc}")
        return None


# ---------- Users ----------

def create_or_get_user(name: str, weight_kg: float = 75.0):
    return _post("/users/", {"name": name, "weight_kg": weight_kg})


def list_users():
    return _get("/users/") or []


# ---------- Meals ----------

def create_meal(user_id: int, food_name: str, grams: float):
    return _post("/meals/", {"user_id": user_id, "food_name": food_name, "grams": grams})


def list_meals(user_id: int):
    return _get(f"/meals/{user_id}") or []


def delete_meal(meal_id: int):
    return _delete(f"/meals/{meal_id}")


# ---------- Workouts ----------

def create_workout(user_id: int, workout_type: str, duration_minutes: float):
    payload = {
        "user_id": user_id,
        "workout_type": workout_type,
        "duration_minutes": duration_minutes,
    }
    return _post("/workouts/", payload)


def list_workouts(user_id: int):
    return _get(f"/workouts/{user_id}") or []


def delete_workout(workout_id: int):
    return _delete(f"/workouts/{workout_id}")


# ---------- Dashboard ----------

def get_today_summary(user_id: int):
    return _get(f"/dashboard/{user_id}/today") or {}


def get_daily_summary(user_id: int, days: int = 30):
    return _get(f"/dashboard/{user_id}/daily-summary", params={"days": days}) or []


def get_weekly_averages(user_id: int):
    return _get(f"/dashboard/{user_id}/weekly-averages") or {}


def get_macro_distribution(user_id: int, days: int = 7):
    return _get(f"/dashboard/{user_id}/macro-distribution", params={"days": days}) or {}


def get_recommendation(user_id: int):
    # LLM-kald kan tage lang tid, især første gang (Ollama skal loade
    # modellen ind i hukommelsen). Backenden selv venter op til ~110
    # sekunder på Ollama, så frontenden skal vente mindst lige så længe.
    result = _get(f"/dashboard/{user_id}/recommendation", timeout=120)
    if result is None:
        return "Kunne ikke hente en anbefaling lige nu."
    return result.get("recommendation", "")
