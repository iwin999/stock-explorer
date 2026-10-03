"""Shared screen pieces: styling, the summary callout and the footer disclaimer."""
import streamlit as st

DISCLAIMER = (
    "This is an educational project and not investment advice. No real money is involved. "
    "The information shown is for learning purposes only, and the creator accepts no "
    "responsibility for any decisions made using it. All investments are subject to market "
    "risk; please understand the consequences before investing. Indicators, simulations and "
    "backtests are based on past data and do not predict future results."
)

# CSS = the styling language of web pages. Sizes are generous for a large screen,
# and the look is deliberately plain: white cards, thin borders, one accent colour.
STYLE_CSS = """
<style>
.stApp, .stApp p, .stApp li, .stApp label { font-size: 1.15rem !important; }
.stApp [data-testid="stCaptionContainer"], .stApp [data-testid="stCaptionContainer"] * { font-size: 1.02rem !important; color: #5b6573; }
input, textarea, [data-baseweb="select"] div { font-size: 1.12rem !important; }

h1 { font-size: 2.6rem !important; font-weight: 700 !important; letter-spacing: -0.5px; }
h2 { font-size: 1.8rem !important; font-weight: 650 !important; margin-top: 0.5rem; }
h3 { font-size: 1.35rem !important; font-weight: 600 !important; }
.stApp a.header-anchor, .stApp [data-testid="stHeaderActionElements"] { display: none !important; }

/* Tabs */
.stApp button[data-baseweb="tab"] p { font-size: 1.2rem !important; font-weight: 600; }

/* Metric cards */
.stApp [data-testid="stMetric"] { background: #ffffff; border: 1px solid #e1e5ec; border-radius: 8px; padding: 0.9rem 1.1rem; }
.stApp [data-testid="stMetricValue"], .stApp [data-testid="stMetricValue"] * { font-size: 2.1rem !important; font-weight: 650; }
.stApp [data-testid="stMetricLabel"], .stApp [data-testid="stMetricLabel"] * { font-size: 1.02rem !important; color: #5b6573; }
.stApp [data-testid="stMetricDelta"], .stApp [data-testid="stMetricDelta"] * { font-size: 1.0rem !important; }

/* Buttons */
.stApp .stButton button p, .stApp .stDownloadButton button p { font-size: 1.1rem !important; font-weight: 600; }
.stApp .stButton button, .stApp .stDownloadButton button { border-radius: 6px; }

/* Plain-English sentence under each signal */
.meaning { font-size: 1.02rem; color: #4a5461; min-height: 5.2em; line-height: 1.45; padding: 0 0.2rem; }

/* Key sentence on a page */
.callout { border-left: 4px solid #1d3557; background: #f3f5f8; padding: 0.9rem 1.2rem;
           border-radius: 4px; font-size: 1.2rem; line-height: 1.5; margin: 0.5rem 0 1rem 0; }
.notice { border-left: 4px solid #b7791f; background: #fdf6e7; padding: 0.7rem 1.1rem;
          border-radius: 4px; font-size: 1.0rem; margin: 0.5rem 0 1rem 0; color: #5b4a1e; }

/* Footer disclaimer: small and quiet */
.disclaimer { font-size: 0.82rem; color: #6b7480; line-height: 1.5; border-top: 1px solid #e1e5ec;
              padding-top: 0.9rem; margin-top: 2rem; }
</style>
"""


def setup_page(title):
    st.set_page_config(page_title=title, layout="wide")
    st.markdown(STYLE_CSS, unsafe_allow_html=True)


def callout(text):
    """A highlighted key sentence."""
    st.markdown(f'<div class="callout">{text}</div>', unsafe_allow_html=True)


def notice(text):
    """A muted amber note (used for 'saved data' warnings)."""
    st.markdown(f'<div class="notice">{text}</div>', unsafe_allow_html=True)


def show_disclaimer():
    st.markdown(f'<div class="disclaimer"><b>Disclaimer.</b> {DISCLAIMER}</div>', unsafe_allow_html=True)


def plain_english(markdown, label="In plain English"):
    """A drop-down with a layman's explanation (for visitors who are not finance people)."""
    with st.expander(label):
        st.markdown(markdown)


def _show_know_how(markdown):
    st.markdown(markdown)


def know_how_button(key, title, markdown):
    """A 'Know how' button that opens a pop-up with the full method: rules, factors, calculation."""
    if st.button("Know how", key=key):
        st.dialog(f"Know how: {title}", width="large")(_show_know_how)(markdown)
