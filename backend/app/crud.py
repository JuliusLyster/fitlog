from datetime import datetime, time, timedelta

from sqlalchemy.orm import Session

from app import models, schemas


# ---------- User ----------

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    db_user = models.User(name=user.name, weight_kg=user.weight_kg)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user(db: Session, user_id: int) -> models.User | None:
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_name(db: Session, name: str) -> models.User | None:
    return db.query(models.User).filter(models.User.name == name).first()


def get_users(db: Session) -> list[models.User]:
    return db.query(models.User).all()


# ---------- Meal ----------

def create_meal(db: Session, meal: models.Meal) -> models.Meal:
    """Tager en allerede-udfyldt Meal-instans (makroer er beregnet i services/openfoodfacts.py)."""
    db.add(meal)
    db.commit()
    db.refresh(meal)
    return meal


def get_meals(db: Session, user_id: int, since: datetime | None = None) -> list[models.Meal]:
    query = db.query(models.Meal).filter(models.Meal.user_id == user_id)
    if since is not None:
        query = query.filter(models.Meal.logged_at >= since)
    return query.order_by(models.Meal.logged_at.desc()).all()


def delete_meal(db: Session, meal_id: int) -> bool:
    meal = db.query(models.Meal).filter(models.Meal.id == meal_id).first()
    if meal is None:
        return False
    db.delete(meal)
    db.commit()
    return True


# ---------- Workout ----------

def create_workout(db: Session, workout: models.Workout) -> models.Workout:
    """Tager en allerede-udfyldt Workout-instans (kalorier er beregnet i services/calories.py)."""
    db.add(workout)
    db.commit()
    db.refresh(workout)
    return workout


def get_workouts(db: Session, user_id: int, since: datetime | None = None) -> list[models.Workout]:
    query = db.query(models.Workout).filter(models.Workout.user_id == user_id)
    if since is not None:
        query = query.filter(models.Workout.logged_at >= since)
    return query.order_by(models.Workout.logged_at.desc()).all()


def delete_workout(db: Session, workout_id: int) -> bool:
    workout = db.query(models.Workout).filter(models.Workout.id == workout_id).first()
    if workout is None:
        return False
    db.delete(workout)
    db.commit()
    return True


# ---------- Dashboard ----------

def get_last_n_days_meals(db: Session, user_id: int, days: int) -> list[models.Meal]:
    since = datetime.utcnow() - timedelta(days=days)
    return get_meals(db, user_id, since=since)


def get_last_n_days_workouts(db: Session, user_id: int, days: int) -> list[models.Workout]:
    since = datetime.utcnow() - timedelta(days=days)
    return get_workouts(db, user_id, since=since)


def get_today_meals(db: Session, user_id: int) -> list[models.Meal]:
    """Måltider logget på indeværende kalenderdag ikke bare 'seneste 24 timer'."""
    start_of_day = datetime.combine(datetime.utcnow().date(), time.min)
    return get_meals(db, user_id, since=start_of_day)


def get_today_workouts(db: Session, user_id: int) -> list[models.Workout]:
    """Træningspas logget på indeværende kalenderdag ikke bare 'seneste 24 timer'."""
    start_of_day = datetime.combine(datetime.utcnow().date(), time.min)
    return get_workouts(db, user_id, since=start_of_day)
