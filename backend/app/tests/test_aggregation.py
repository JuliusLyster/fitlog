"""
Unittests for app/services/aggregation.py

Kører rene beregningsfunktioner uden database eller netværk,
så de er hurtige og deterministiske.
"""

from datetime import datetime

from app.services import aggregation


def _meal(date_str: str, calories: float, protein: float, carbs: float, fat: float) -> dict:
    return {
        "logged_at": datetime.fromisoformat(date_str),
        "calories": calories,
        "protein_g": protein,
        "carbs_g": carbs,
        "fat_g": fat,
    }


def _workout(date_str: str, calories_burned: float) -> dict:
    return {
        "logged_at": datetime.fromisoformat(date_str),
        "duration_minutes": 30,
        "calories_burned": calories_burned,
    }


def test_daily_calorie_summary_empty_input():
    df = aggregation.daily_calorie_summary([], [])
    assert df.empty
    expected_cols = ["date", "calories_in", "calories_out", "protein_g", "carbs_g", "fat_g"]
    assert list(df.columns) == expected_cols


def test_daily_calorie_summary_sums_per_day():
    meals = [
        _meal("2026-06-01T08:00:00", 300, 20, 30, 10),
        _meal("2026-06-01T13:00:00", 500, 30, 50, 15),
        _meal("2026-06-02T08:00:00", 400, 25, 40, 12),
    ]
    workouts = [_workout("2026-06-01T18:00:00", 250)]

    df = aggregation.daily_calorie_summary(meals, workouts)

    first_date = df["date"].iloc[0]
    day1 = df[df["date"] == first_date].iloc[0]
    assert day1["calories_in"] == 800
    assert day1["calories_out"] == 250
    assert day1["protein_g"] == 50

    day2 = df.iloc[1]
    assert day2["calories_in"] == 400
    assert day2["calories_out"] == 0


def test_weekly_averages():
    meals = [
        _meal("2026-06-01T08:00:00", 1000, 50, 100, 30),
        _meal("2026-06-02T08:00:00", 2000, 100, 200, 60),
    ]
    df = aggregation.daily_calorie_summary(meals, [])
    averages = aggregation.weekly_averages(df)

    assert averages["avg_calories_in"] == 1500.0
    assert averages["avg_protein_g"] == 75.0


def test_weekly_averages_empty():
    df = aggregation.daily_calorie_summary([], [])
    averages = aggregation.weekly_averages(df)
    assert averages["avg_calories_in"] == 0.0


def test_macro_distribution_percentages_sum_to_100():
    meals = [_meal("2026-06-01T08:00:00", 500, 25, 50, 25)]
    df = aggregation.daily_calorie_summary(meals, [])
    dist = aggregation.macro_distribution(df)

    total_pct = dist["protein_pct"] + dist["carbs_pct"] + dist["fat_pct"]
    assert round(total_pct) == 100


def test_macro_distribution_no_data():
    df = aggregation.daily_calorie_summary([], [])
    dist = aggregation.macro_distribution(df)
    assert dist == {"protein_pct": 0.0, "carbs_pct": 0.0, "fat_pct": 0.0}


def test_build_summary_text_contains_dates_and_calories():
    meals = [_meal("2026-06-01T08:00:00", 500, 25, 50, 25)]
    df = aggregation.daily_calorie_summary(meals, [])
    text = aggregation.build_summary_text(df)

    assert "500 kcal" in text


def test_build_summary_text_empty():
    df = aggregation.daily_calorie_summary([], [])
    text = aggregation.build_summary_text(df)
    assert "Ingen loggede" in text
