CUSTOM_CSS = """
<style>
/* Runde hjørner og let skygge på "cards" (st.container(border=True)) */
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 16px !important;
}

/* Pænere, større metric-tal på dashboardet */
div[data-testid="stMetric"] {
    background-color: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 1rem 1rem 0.75rem 1rem;
}

div[data-testid="stMetricValue"] {
    font-size: 1.6rem;
}

/* Bløde, runde knapper */
.stButton > button, .stFormSubmitButton > button {
    border-radius: 10px;
    font-weight: 600;
    padding: 0.5rem 1.25rem;
}

/* Input-felter med lidt mere luft */
div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input {
    border-radius: 10px;
}

/* Overskrifter med lidt luft under sig */
h1 {
    padding-bottom: 0.25rem;
}

/* Sidebar-titel */
section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p {
    font-size: 0.95rem;
}

/* Små farvede "pille"-badges, bruges bl.a. til at vise hvor
   næringsdata for et måltid kommer fra (se SOURCE_BADGE_HTML). */
.fitlog-badge {
    display: inline-block;
    padding: 0.15rem 0.65rem;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    margin-top: 0.15rem;
}
.fitlog-badge-local {
    background: rgba(16, 185, 129, 0.15);
    color: #10B981;
    border: 1px solid rgba(16, 185, 129, 0.35);
}
.fitlog-badge-openfoodfacts {
    background: rgba(59, 130, 246, 0.15);
    color: #60A5FA;
    border: 1px solid rgba(59, 130, 246, 0.35);
}
.fitlog-badge-fallback {
    background: rgba(251, 191, 36, 0.15);
    color: #FBBF24;
    border: 1px solid rgba(251, 191, 36, 0.35);
}
</style>
"""

SOURCE_BADGE_HTML = {
    "local": '<span class="fitlog-badge fitlog-badge-local">Præcis værdi</span>',
    "openfoodfacts": '<span class="fitlog-badge fitlog-badge-openfoodfacts">Open Food Facts</span>',
    "fallback": '<span class="fitlog-badge fitlog-badge-fallback">Estimeret værdi</span>',
}


def source_badge(source: str) -> str:
    """Returnerer HTML for en farvet badge, der viser hvor et måltids
    næringsdata stammer fra. Bruges med st.markdown(..., unsafe_allow_html=True)."""
    return SOURCE_BADGE_HTML.get(source, "")
