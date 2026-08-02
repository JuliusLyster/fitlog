import numpy as np
import pandas as pd


def meals_to_dataframe(meals: list[dict]) -> pd.DataFrame:
   
    if not meals:
        return pd.DataFrame(
            columns=["date", "calories", "protein_g", "carbs_g", "fat_g"]
        )

    df = pd.DataFrame(meals)
    df["date"] = pd.to_datetime(df["logged_at"]).dt.date
    return df


def workouts_to_dataframe(workouts: list[dict]) -> pd.DataFrame:
 
    if not workouts:
        return pd.DataFrame(columns=["date", "duration_minutes", "calories_burned"])

    df = pd.DataFrame(workouts)
    df["date"] = pd.to_datetime(df["logged_at"]).dt.date
    return df


def daily_calorie_summary(meals: list[dict], workouts: list[dict]) -> pd.DataFrame:
   
    meals_df = meals_to_dataframe(meals)
    workouts_df = workouts_to_dataframe(workouts)

    if meals_df.empty:
        calories_in = pd.DataFrame(columns=["date", "calories", "protein_g", "carbs_g", "fat_g"])
    else:
        calories_in = (
            meals_df.groupby("date")[["calories", "protein_g", "carbs_g", "fat_g"]]
            .sum()
            .reset_index()
        )

    if workouts_df.empty:
        calories_out = pd.DataFrame(columns=["date", "calories_burned"])
    else:
        calories_out = (
            workouts_df.groupby("date")[["calories_burned"]].sum().reset_index()
        )

    merged = pd.merge(calories_in, calories_out, on="date", how="outer")
    numeric_cols = [c for c in merged.columns if c != "date"]
    merged[numeric_cols] = merged[numeric_cols].fillna(0.0).astype(float)
    merged = merged.rename(columns={"calories": "calories_in", "calories_burned": "calories_out"})
    merged = merged.sort_values("date").reset_index(drop=True)

    # Sikrer at alle forventede kolonner findes, selv hvis en af DataFrames var tom
    for col in ["calories_in", "calories_out", "protein_g", "carbs_g", "fat_g"]:
        if col not in merged.columns:
            merged[col] = 0.0

    return merged[["date", "calories_in", "calories_out", "protein_g", "carbs_g", "fat_g"]]


def weekly_averages(daily_summary: pd.DataFrame) -> dict:
   
    if daily_summary.empty:
        return {
            "avg_calories_in": 0.0,
            "avg_calories_out": 0.0,
            "avg_protein_g": 0.0,
            "avg_carbs_g": 0.0,
            "avg_fat_g": 0.0,
        }

    return {
        "avg_calories_in": round(float(np.mean(daily_summary["calories_in"])), 1),
        "avg_calories_out": round(float(np.mean(daily_summary["calories_out"])), 1),
        "avg_protein_g": round(float(np.mean(daily_summary["protein_g"])), 1),
        "avg_carbs_g": round(float(np.mean(daily_summary["carbs_g"])), 1),
        "avg_fat_g": round(float(np.mean(daily_summary["fat_g"])), 1),
    }


def macro_distribution(daily_summary: pd.DataFrame) -> dict:
 
    if daily_summary.empty:
        return {"protein_pct": 0.0, "carbs_pct": 0.0, "fat_pct": 0.0}

    total_protein = float(daily_summary["protein_g"].sum())
    total_carbs = float(daily_summary["carbs_g"].sum())
    total_fat = float(daily_summary["fat_g"].sum())
    total = total_protein + total_carbs + total_fat

    if total == 0:
        return {"protein_pct": 0.0, "carbs_pct": 0.0, "fat_pct": 0.0}

    return {
        "protein_pct": round(total_protein / total * 100, 1),
        "carbs_pct": round(total_carbs / total * 100, 1),
        "fat_pct": round(total_fat / total * 100, 1),
    }


def build_summary_text(daily_summary: pd.DataFrame) -> str:
  
    if daily_summary.empty:
        return "Ingen loggede måltider eller træningspas de seneste 7 dage."

    lines = []
    for _, row in daily_summary.iterrows():
        lines.append(
            f"{row['date']}: {row['calories_in']:.0f} kcal indtaget "
            f"(protein {row['protein_g']:.0f}g, kulhydrat {row['carbs_g']:.0f}g, "
            f"fedt {row['fat_g']:.0f}g), {row['calories_out']:.0f} kcal forbrændt ved træning."
        )

    return "\n".join(lines)
