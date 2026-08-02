import streamlit as st

from styling import CUSTOM_CSS

st.set_page_config(page_title="FitLog", page_icon=":material/fitness_center:", layout="wide")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

if "user_id" not in st.session_state:
    st.session_state.user_id = None
    st.session_state.user_name = None

pages = [
    st.Page("views/forside.py", title="Forside", icon=":material/home:", default=True),
    st.Page("views/log_maaltid.py", title="Log Måltid", icon=":material/restaurant:"),
    st.Page("views/log_traening.py", title="Log Træning", icon=":material/directions_run:"),
    st.Page("views/dashboard.py", title="Dashboard", icon=":material/monitoring:"),
]

with st.sidebar:
    st.markdown("### FitLog")
    if st.session_state.user_name:
        st.caption(f"Logget ind som **{st.session_state.user_name}**")
    st.divider()

navigation = st.navigation(pages)
navigation.run()
