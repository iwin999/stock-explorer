"""Shared screen pieces: big fonts, and the disclaimer that must be on every page."""
import streamlit as st

DISCLAIMER = "Educational project. Not investment advice."

# CSS = the styling language of web pages. These rules make text bigger for an exhibition screen.
BIG_FONT_CSS = """
<style>
/* Bigger text everywhere, for a screen viewed from a distance */
.stApp, .stApp p, .stApp li, .stApp label { font-size: 1.3rem !important; }
.stApp [data-testid="stCaptionContainer"], .stApp [data-testid="stCaptionContainer"] * { font-size: 1.2rem !important; }
input, textarea, [data-baseweb="select"] div { font-size: 1.25rem !important; }
.stApp button[data-baseweb="tab"] p { font-size: 1.5rem !important; font-weight: 600; }
.stApp .stButton button p, .stApp .stDownloadButton button p { font-size: 1.3rem !important; }
.stApp [data-testid="stRadio"] label p, .stApp [data-testid="stCheckbox"] label p { font-size: 1.25rem !important; }
h1 { font-size: 3.4rem !important; }
h2 { font-size: 2.4rem !important; }
h3 { font-size: 1.9rem !important; }
.stApp [data-testid="stMetricValue"], .stApp [data-testid="stMetricValue"] * { font-size: 2.8rem !important; }
.stApp [data-testid="stMetricLabel"], .stApp [data-testid="stMetricLabel"] * { font-size: 1.3rem !important; }
.stApp [data-testid="stMetricDelta"], .stApp [data-testid="stMetricDelta"] * { font-size: 1.15rem !important; }
.meaning { font-size: 1.2rem; color: #555; min-height: 4.5em; }
@media (prefers-color-scheme: dark) { .meaning { color: #bbb; } }
.disclaimer { text-align:center; padding:0.6rem; border-radius:8px; background:#fff3cd;
              color:#664d03 !important; font-weight:600; font-size:1.25rem; }
</style>
"""


def setup_page(title):
    st.set_page_config(page_title=title, page_icon="📈", layout="wide")
    st.markdown(BIG_FONT_CSS, unsafe_allow_html=True)


def show_disclaimer():
    st.markdown(f'<div class="disclaimer">⚠️ {DISCLAIMER}</div>', unsafe_allow_html=True)
