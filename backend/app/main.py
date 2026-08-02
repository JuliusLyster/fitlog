from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.database import Base, engine, get_db, run_light_migrations
from app.services import aggregation, llm
from app.services.calories import calculate_calories_burned
from app.services.openfoodfacts import calculate_macros

Base.metadata.create_all(bind=engine)

run_light_migrations()

app = FastAPI(
    title="FitLog API",
    description="Personlig fitness- og ernæringslogger",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok", "service": "FitLog API"}


# ---------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------

@app.post("/users/", response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = crud.get_user_by_name(db, user.name)
    if existing:
        return existing
    return crud.create_user(db, user)


@app.get("/users/", response_model=list[schemas.UserOut])
def list_users(db: Session = Depends(get_db)):
    return crud.get_users(db)


@app.get("/users/{user_id}", response_model=schemas.UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Bruger ikke fundet")
    return user


# ---------------------------------------------------------------------
# Meals
# ---------------------------------------------------------------------

@app.post("/meals/", response_model=schemas.MealOut)
def create_meal(meal: schemas.MealCreate, db: Session = Depends(get_db)):
    user = crud.get_user(db, meal.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Bruger ikke fundet")

    macros = calculate_macros(meal.food_name, meal.grams)

    db_meal = models.Meal(
        user_id=meal.user_id,
        food_name=meal.food_name,
        grams=meal.grams,
        calories=macros.calories,
        protein_g=macros.protein_g,
        carbs_g=macros.carbs_g,
        fat_g=macros.fat_g,
        source=macros.source,
    )
    return crud.create_meal(db, db_meal)


@app.get("/meals/{user_id}", response_model=list[schemas.MealOut])
def list_meals(user_id: int, db: Session = Depends(get_db)):
    return crud.get_meals(db, user_id)


@app.delete("/meals/{meal_id}")
def delete_meal(meal_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_meal(db, meal_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Måltid ikke fundet")
    return {"status": "deleted", "id": meal_id}


# ---------------------------------------------------------------------
# Workouts
# ---------------------------------------------------------------------

@app.post("/workouts/", response_model=schemas.WorkoutOut)
def create_workout(workout: schemas.WorkoutCreate, db: Session = Depends(get_db)):
    user = crud.get_user(db, workout.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Bruger ikke fundet")

    calories_burned = calculate_calories_burned(
        workout.workout_type, workout.duration_minutes, float(user.weight_kg)
    )

    db_workout = models.Workout(
        user_id=workout.user_id,
        workout_type=workout.workout_type,
        duration_minutes=workout.duration_minutes,
        calories_burned=calories_burned,
    )
    return crud.create_workout(db, db_workout)


@app.get("/workouts/{user_id}", response_model=list[schemas.WorkoutOut])
def list_workouts(user_id: int, db: Session = Depends(get_db)):
    return crud.get_workouts(db, user_id)


@app.delete("/workouts/{workout_id}")
def delete_workout(workout_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_workout(db, workout_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Træningspas ikke fundet")
    return {"status": "deleted", "id": workout_id}


# ---------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------

def _meals_to_dicts(meals: list[models.Meal]) -> list[dict]:
    return [
        {
            "logged_at": m.logged_at,
            "calories": m.calories,
            "protein_g": m.protein_g,
            "carbs_g": m.carbs_g,
            "fat_g": m.fat_g,
        }
        for m in meals
    ]


def _workouts_to_dicts(workouts: list[models.Workout]) -> list[dict]:
    return [
        {"logged_at": w.logged_at, "calories_burned": w.calories_burned}
        for w in workouts
    ]


@app.get("/dashboard/{user_id}/daily-summary")
def daily_summary(user_id: int, days: int = 30, db: Session = Depends(get_db)):
    """Dags-for-dags kalorier ind/ud + makrofordeling for de seneste `days` dage."""
    meals = crud.get_last_n_days_meals(db, user_id, days)
    workouts = crud.get_last_n_days_workouts(db, user_id, days)

    summary_df = aggregation.daily_calorie_summary(
        _meals_to_dicts(meals), _workouts_to_dicts(workouts)
    )
    # date-objekter skal konverteres til str for at kunne JSON-serialiseres
    summary_df["date"] = summary_df["date"].astype(str)
    return summary_df.to_dict(orient="records")


@app.get("/dashboard/{user_id}/today")
def today_summary(user_id: int, db: Session = Depends(get_db)):
    """
    Dagens overblik: kalorier ind/ud, makroer og antal træningspas logget
    på indeværende kalenderdag (UTC) - i modsætning til daily-summary/
    weekly-averages, som ser på et rullende antal dage bagud.
    """
    meals = crud.get_today_meals(db, user_id)
    workouts = crud.get_today_workouts(db, user_id)

    summary_df = aggregation.daily_calorie_summary(
        _meals_to_dicts(meals), _workouts_to_dicts(workouts)
    )

    if summary_df.empty:
        return {
            "calories_in": 0.0,
            "calories_out": 0.0,
            "protein_g": 0.0,
            "carbs_g": 0.0,
            "fat_g": 0.0,
            "workout_count": len(workouts),
        }

    row = summary_df.iloc[0]
    return {
        "calories_in": float(row["calories_in"]),
        "calories_out": float(row["calories_out"]),
        "protein_g": float(row["protein_g"]),
        "carbs_g": float(row["carbs_g"]),
        "fat_g": float(row["fat_g"]),
        "workout_count": len(workouts),
    }


@app.get("/dashboard/{user_id}/weekly-averages")
def weekly_averages(user_id: int, db: Session = Depends(get_db)):
    """Ugentlige gennemsnit (seneste 7 dage) for kalorier og makroer."""
    meals = crud.get_last_n_days_meals(db, user_id, 7)
    workouts = crud.get_last_n_days_workouts(db, user_id, 7)

    summary_df = aggregation.daily_calorie_summary(
        _meals_to_dicts(meals), _workouts_to_dicts(workouts)
    )
    return aggregation.weekly_averages(summary_df)


@app.get("/dashboard/{user_id}/macro-distribution")
def macro_distribution(user_id: int, days: int = 7, db: Session = Depends(get_db)):
    """Samlet makrofordeling (protein/kulhydrat/fedt i %) for de seneste `days` dage."""
    meals = crud.get_last_n_days_meals(db, user_id, days)
    workouts = crud.get_last_n_days_workouts(db, user_id, days)

    summary_df = aggregation.daily_calorie_summary(
        _meals_to_dicts(meals), _workouts_to_dicts(workouts)
    )
    return aggregation.macro_distribution(summary_df)


@app.get("/dashboard/{user_id}/recommendation", response_model=schemas.RecommendationOut)
def recommendation(user_id: int, db: Session = Depends(get_db)):
    """AI-genereret kost-/træningsanbefaling baseret på de seneste 7 dage."""
    meals = crud.get_last_n_days_meals(db, user_id, 7)
    workouts = crud.get_last_n_days_workouts(db, user_id, 7)

    summary_df = aggregation.daily_calorie_summary(
        _meals_to_dicts(meals), _workouts_to_dicts(workouts)
    )
    summary_text = aggregation.build_summary_text(summary_df)
    text = llm.generate_recommendation(summary_text)

    return schemas.RecommendationOut(recommendation=text)
