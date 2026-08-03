"""
Unittests for app/services/calories.py
"""

from app.services.calories import calculate_calories_burned


def test_running_calories_for_75kg_30min():
    # 9.8 MET * 3.5 * 75 / 200 * 30 = 385.875 -> afrundet 385.9
    result = calculate_calories_burned("løb", 30, 75)
    assert result == 385.9


def test_heavier_person_burns_more_calories():
    light = calculate_calories_burned("løb", 30, 60)
    heavy = calculate_calories_burned("løb", 30, 100)
    assert heavy > light


def test_longer_duration_burns_more_calories():
    short = calculate_calories_burned("cykling", 15, 75)
    long = calculate_calories_burned("cykling", 60, 75)
    assert long > short
    assert round(long / short) == 4


def test_higher_intensity_activity_burns_more_calories():
    walking = calculate_calories_burned("gang", 30, 75)
    running = calculate_calories_burned("løb", 30, 75)
    assert running > walking


def test_unknown_workout_type_uses_default_met():
    result = calculate_calories_burned("parkour", 30, 75)
    expected = calculate_calories_burned("andet", 30, 75)
    assert result == expected


def test_workout_type_is_case_insensitive():
    assert calculate_calories_burned("LØB", 30, 75) == calculate_calories_burned("løb", 30, 75)
