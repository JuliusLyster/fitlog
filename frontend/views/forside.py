import streamlit as st

from api_client import create_or_get_user, list_users

st.title("FitLog")
st.caption("Personlig fitness- og ernæringslogger")

if "user_id" not in st.session_state:
    st.session_state.user_id = None
    st.session_state.user_name = None

if st.session_state.user_id:
    st.success(
        f"Aktiv bruger: **{st.session_state.user_name}**. "
        "Brug menuen i venstre side til at logge måltider, "
        "træning og se dit dashboard."
    )

col1, col2 = st.columns(2, gap="large")

with col1:
    with st.container(border=True):
        st.subheader("Vælg eksisterende bruger")

        existing_users = list_users()

        if not existing_users:
            st.caption("Ingen brugere oprettet endnu.")
        else:
            names = [u["name"] for u in existing_users]
            selected = st.selectbox("Bruger", options=["— vælg —"] + names)
            if selected != "— vælg —":
                user = next(u for u in existing_users if u["name"] == selected)
                if st.button("Log ind som denne bruger", type="primary"):
                    st.session_state.user_id = user["id"]
                    st.session_state.user_name = user["name"]
                    st.rerun()

with col2:
    with st.container(border=True):
        st.subheader("Opret en ny bruger")

        new_name = st.text_input("Brugernavn")
        new_weight = st.number_input(
            "Vægt (kg)",
            min_value=30.0,
            max_value=300.0,
            value=75.0,
            step=1.0,
            help="Bruges til automatisk at beregne forbrændte kalorier ved træning.",
        )

        if st.button("Opret / vælg bruger", type="primary"):
            if not new_name.strip():
                st.warning("Skriv et brugernavn først.")
            else:
                user = create_or_get_user(new_name.strip(), new_weight)
                if user:
                    st.session_state.user_id = user["id"]
                    st.session_state.user_name = user["name"]
                    st.rerun()

if not st.session_state.user_id:
    st.info("Vælg eller opret en bruger for at komme i gang.")
