MET_VALUES: dict[str, float] = {
    "løb": 9.8,
    "cykling": 7.5,
    "styrketræning": 6.0,
    "svømning": 8.3,
    "gang": 3.5,
    "andet": 5.0,
}

DEFAULT_MET = 5.0


def calculate_calories_burned(
    workout_type: str, duration_minutes: float, weight_kg: float
) -> float:

    met = MET_VALUES.get(workout_type.strip().lower(), DEFAULT_MET)
    calories = met * 3.5 * weight_kg / 200 * duration_minutes
    return round(calories, 1)
