import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from api_client import (
    get_daily_summary,
    get_macro_distribution,
    get_recommendation,
    get_today_summary,
    get_weekly_averages,
)

# Farver og stil der matcher appens mørke tema (se .streamlit/config.toml)
TEXT_COLOR = "#E5E7EB"
GRID_COLOR = "#2A3245"
ACCENT_IN = "#10B981"
ACCENT_OUT = "#F87171"
MACRO_COLORS = ["#10B981", "#FBBF24", "#F87171"]


def _style_dark_axes(ax):
    ax.set_facecolor("none")
    ax.tick_params(colors=TEXT_COLOR, labelsize=8)
    ax.xaxis.label.set_color(TEXT_COLOR)
    ax.yaxis.label.set_color(TEXT_COLOR)
    for spine in ax.spines.values():
        spine.set_color(GRID_COLOR)
    ax.grid(alpha=0.25, color=GRID_COLOR)


def _bound_date_axis(ax, dates: pd.Series) -> None:
    
    min_date, max_date = dates.min(), dates.max()
    span_days = max(int((max_date - min_date).days), 1)
    padding = pd.Timedelta(days=max(1, round(span_days * 0.1)))
    ax.set_xlim(min_date - padding, max_date + padding)
    ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=3, maxticks=7))
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax.xaxis.get_major_locator()))


def _fill_missing_days(df: pd.DataFrame, days: int) -> pd.DataFrame:
   
    end = pd.Timestamp.now().normalize()
    start = end - pd.Timedelta(days=days - 1)
    full_range = pd.date_range(start, end, freq="D")

    df = df.set_index("date").reindex(full_range, fill_value=0.0)
    df.index.name = "date"
    return df.reset_index()


st.title("Dashboard")

if not st.session_state.get("user_id"):
    st.warning("Gå til Forsiden og vælg/opret en bruger først.")
    st.stop()

user_id = st.session_state.user_id

# ---------- Dagens overblik ----------

st.subheader("Dagens overblik")

today = get_today_summary(user_id)

t1, t2, t3, t4, t5, t6 = st.columns(6)
t1.metric("Kalorier ind", f"{today.get('calories_in', 0):.0f} kcal")
t2.metric("Kalorier ud", f"{today.get('calories_out', 0):.0f} kcal")
t3.metric("Protein", f"{today.get('protein_g', 0):.0f} g")
t4.metric("Kulhydrat", f"{today.get('carbs_g', 0):.0f} g")
t5.metric("Fedt", f"{today.get('fat_g', 0):.0f} g")
t6.metric("Træningspas", f"{today.get('workout_count', 0):.0f}")

st.divider()

# ---------- Ugentlige gennemsnit ----------

st.subheader("Ugentligt gennemsnit (seneste 7 dage)")

averages = get_weekly_averages(user_id)

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Kalorier ind", f"{averages.get('avg_calories_in', 0):.0f} kcal")
col2.metric("Kalorier ud", f"{averages.get('avg_calories_out', 0):.0f} kcal")
col3.metric("Protein", f"{averages.get('avg_protein_g', 0):.0f} g")
col4.metric("Kulhydrat", f"{averages.get('avg_carbs_g', 0):.0f} g")
col5.metric("Fedt", f"{averages.get('avg_fat_g', 0):.0f} g")

st.divider()

# ---------- Ugentlig og månedlig tendens side om side ----------

weekly_col, monthly_col = st.columns(2, gap="large")

with weekly_col:
    with st.container(border=True):
        st.markdown("**Ugentlig tendens** · kalorier ind/ud pr. dag, seneste 7 dage")

        weekly_data = get_daily_summary(user_id, days=7)
        df_week = pd.DataFrame(weekly_data) if weekly_data else pd.DataFrame(
            columns=["date", "calories_in", "calories_out"]
        )
        if not df_week.empty:
            df_week["date"] = pd.to_datetime(df_week["date"])
        df_week = _fill_missing_days(df_week[["date", "calories_in", "calories_out"]], days=7)

        fig, ax = plt.subplots(figsize=(5, 3))
        fig.patch.set_alpha(0.0)
        x = np.arange(len(df_week))
        width = 0.35
        ax.bar(x - width / 2, df_week["calories_in"], width, label="Ind", color=ACCENT_IN)
        ax.bar(x + width / 2, df_week["calories_out"], width, label="Ud", color=ACCENT_OUT)
        ax.set_ylabel("kcal")
        ax.set_xticks(x)
        ax.set_xticklabels(df_week["date"].dt.strftime("%d/%m"))
        _style_dark_axes(ax)
        legend = ax.legend(fontsize=8, facecolor="none", edgecolor="none")
        for text in legend.get_texts():
            text.set_color(TEXT_COLOR)
        fig.tight_layout()
        st.pyplot(fig, use_container_width=True)

with monthly_col:
    with st.container(border=True):
        st.markdown("**Månedlig tendens** · kalorier ind/ud, seneste 30 dage")

        daily_data = get_daily_summary(user_id, days=30)

        if daily_data:
            df = pd.DataFrame(daily_data)
            df["date"] = pd.to_datetime(df["date"])

            fig2, ax2 = plt.subplots(figsize=(5, 3))
            fig2.patch.set_alpha(0.0)
            ax2.plot(df["date"], df["calories_in"], marker="o", markersize=4,
                     label="Ind", color=ACCENT_IN, linewidth=2)
            ax2.plot(df["date"], df["calories_out"], marker="o", markersize=4,
                     label="Ud", color=ACCENT_OUT, linewidth=2)
            ax2.set_ylabel("kcal")
            _bound_date_axis(ax2, df["date"])
            _style_dark_axes(ax2)
            legend2 = ax2.legend(fontsize=8, facecolor="none", edgecolor="none")
            for text in legend2.get_texts():
                text.set_color(TEXT_COLOR)
            fig2.autofmt_xdate()
            fig2.tight_layout()
            st.pyplot(fig2, use_container_width=True)
        else:
            st.caption("Ingen data at vise endnu. Log nogle måltider og træningspas først.")

st.divider()

# ---------- Makrofordeling ----------

with st.container(border=True):
    st.markdown("**Makrofordeling** · seneste 7 dage")

    distribution = get_macro_distribution(user_id, days=7)

    if distribution and sum(distribution.values()) > 0:
        labels = ["Protein", "Kulhydrat", "Fedt"]
        values = [
            distribution.get("protein_pct", 0),
            distribution.get("carbs_pct", 0),
            distribution.get("fat_pct", 0),
        ]

        fig3, ax3 = plt.subplots(figsize=(8, 2.5))
        fig3.patch.set_alpha(0.0)
        bars = ax3.barh(labels, values, color=MACRO_COLORS, height=0.6)
        ax3.set_xlabel("%")
        ax3.set_xlim(0, max(values) + 15)
        _style_dark_axes(ax3)
        for bar, value in zip(bars, values):
            ax3.text(
                bar.get_width() + 1.5,
                bar.get_y() + bar.get_height() / 2,
                f"{value:.0f}%",
                va="center",
                color=TEXT_COLOR,
                fontsize=8,
            )
        fig3.tight_layout()
        st.pyplot(fig3, use_container_width=True)
    else:
        st.caption("Ingen måltider logget de seneste 7 dage.")

st.divider()

# ---------- LLM-anbefaling ----------

with st.container(border=True):
    st.subheader("AI-anbefaling")
    st.caption("Genereret ud fra dine seneste 7 dages måltider og træning.")

    if st.button("Hent anbefaling"):
        with st.spinner("Spørger AI-modellen..."):
            recommendation = get_recommendation(user_id)
        st.markdown(recommendation)
