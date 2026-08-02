from datetime import datetime

from pydantic import BaseModel, Field


# ---------- User ----------

class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    weight_kg: float = Field(75.0, gt=0, le=400)


class UserOut(BaseModel):
    id: int
    name: str
    weight_kg: float
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Meal ----------

class MealCreate(BaseModel):
    user_id: int
    food_name: str = Field(..., min_length=1)
    grams: float = Field(..., gt=0)


class MealOut(BaseModel):
    id: int
    user_id: int
    food_name: str
    grams: float
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    source: str
    logged_at: datetime

    class Config:
        from_attributes = True


# ---------- Workout ----------

class WorkoutCreate(BaseModel):
    user_id: int
    workout_type: str = Field(..., min_length=1)
    duration_minutes: float = Field(..., gt=0)


class WorkoutOut(BaseModel):
    id: int
    user_id: int
    workout_type: str
    duration_minutes: float
    calories_burned: float
    logged_at: datetime

    class Config:
        from_attributes = True


# ---------- Dashboard ----------

class DailySummary(BaseModel):
    date: str
    calories_in: float
    calories_out: float
    protein_g: float
    carbs_g: float
    fat_g: float


class RecommendationOut(BaseModel):
    recommendation: str
