import streamlit as st

from api_client import create_workout, delete_workout, list_workouts

st.title("Log træning")

if not st.session_state.get("user_id"):
    st.warning("Gå til Forsiden og vælg/opret en bruger først.")
    st.stop()

user_id = st.session_state.user_id

with st.container(border=True):
    with st.form("workout_form", clear_on_submit=True):
        workout_type = st.selectbox(
            "Type",
            ["Løb", "Cykling", "Styrketræning", "Svømning", "Gang", "Andet"],
        )
        duration = st.number_input(
            "Varighed (minutter)", min_value=1.0, max_value=600.0, value=30.0, step=5.0
        )
        submitted = st.form_submit_button("Log træning", type="primary")

        if submitted:
            workout = create_workout(user_id, workout_type, duration)
            if workout:
                st.success(
                    f"Logget {workout_type} i {duration:.0f} min — "
                    f"**{workout['calories_burned']:.0f} kcal** forbrændt "
                    "(beregnet automatisk ud fra din vægt)"
                )

st.divider()
st.subheader("Dine seneste træningspas")

workouts = list_workouts(user_id)

if not workouts:
    st.caption("Ingen træningspas logget endnu.")
else:
    for workout in workouts[:20]:
        with st.container(border=True):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.write(
                    f"**{workout['workout_type']}** — {workout['duration_minutes']:.0f} min, "
                    f"{workout['calories_burned']:.0f} kcal forbrændt"
                )
                st.caption(workout["logged_at"][:16].replace("T", " "))
            with col2:
                if st.button("Slet", key=f"del_workout_{workout['id']}"):
                    delete_workout(workout["id"])
                    st.rerun()
