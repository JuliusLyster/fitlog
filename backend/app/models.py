"""
SQLAlchemy-modeller (databasetabeller) for FitLog.

Der er tre tabeller:
- User:      en simpel bruger (uden login/auth - kun til at adskille data)
- Meal:      et logget måltid med beregnede makroer
- Workout:   et logget træningspas
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    weight_kg = Column(Float, nullable=False, default=75.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    meals = relationship("Meal", back_populates="owner", cascade="all, delete-orphan")
    workouts = relationship("Workout", back_populates="owner", cascade="all, delete-orphan")


class Meal(Base):
    __tablename__ = "meals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    food_name = Column(String, nullable=False)
    grams = Column(Float, nullable=False)

    calories = Column(Float, nullable=False)
    protein_g = Column(Float, nullable=False)
    carbs_g = Column(Float, nullable=False)
    fat_g = Column(Float, nullable=False)
 
    source = Column(String, nullable=False, default="local")

    logged_at = Column(DateTime, default=datetime.utcnow, index=True)

    owner = relationship("User", back_populates="meals")


class Workout(Base):
    __tablename__ = "workouts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    workout_type = Column(String, nullable=False)
    duration_minutes = Column(Float, nullable=False)
    calories_burned = Column(Float, nullable=False)

    logged_at = Column(DateTime, default=datetime.utcnow, index=True)

    owner = relationship("User", back_populates="workouts")
