import streamlit as st

from api_client import create_meal, delete_meal, list_meals
from styling import source_badge

st.title("Log måltid")

if not st.session_state.get("user_id"):
    st.warning("Gå til Forsiden og vælg/opret en bruger først.")
    st.stop()

user_id = st.session_state.user_id

with st.container(border=True):
    with st.form("meal_form", clear_on_submit=True):
        food_name = st.text_input("Fødevare (fx 'kylling', 'havregryn', 'banan')")
        grams = st.number_input(
            "Mængde (gram)", min_value=1.0, max_value=5000.0, value=100.0, step=10.0
        )
        submitted = st.form_submit_button("Log måltid", type="primary")

        if submitted:
            if not food_name.strip():
                st.warning("Skriv et fødevarenavn.")
            else:
                with st.spinner("Slår næringsindhold op..."):
                    meal = create_meal(user_id, food_name.strip(), grams)
                if meal:
                    st.success(
                        f"Logget {grams:.0f}g {food_name}: {meal['calories']:.0f} kcal, "
                        f"protein {meal['protein_g']:.0f}g, kulhydrat {meal['carbs_g']:.0f}g, "
                        f"fedt {meal['fat_g']:.0f}g"
                    )
                    st.markdown(source_badge(meal.get("source", "")), unsafe_allow_html=True)

st.divider()
st.subheader("Dine seneste måltider")

meals = list_meals(user_id)

if not meals:
    st.caption("Ingen måltider logget endnu.")
else:
    for meal in meals[:20]:
        with st.container(border=True):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.write(
                    f"**{meal['food_name']}** ({meal['grams']:.0f}g) — "
                    f"{meal['calories']:.0f} kcal · P {meal['protein_g']:.0f}g · "
                    f"K {meal['carbs_g']:.0f}g · F {meal['fat_g']:.0f}g"
                )
                badge = source_badge(meal.get("source", ""))
                timestamp = meal["logged_at"][:16].replace("T", " ")
                st.markdown(f"{badge}&nbsp;&nbsp;·&nbsp;&nbsp;{timestamp}", unsafe_allow_html=True)
            with col2:
                if st.button("Slet", key=f"del_meal_{meal['id']}"):
                    delete_meal(meal["id"])
                    st.rerun()
