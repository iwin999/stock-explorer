"""Live price lookups shared by all visitors.

st.cache_data(ttl=15) means: if anyone asked for this company in the last 15 seconds,
reuse that answer instead of calling Yahoo again. That keeps the page fast and
stops many visitors from flooding Yahoo with requests.
"""
import streamlit as st

from core.market_data import get_quote

REFRESH_SECONDS = 15


@st.cache_data(ttl=REFRESH_SECONDS, show_spinner=False)
def live_quote(symbol):
    return get_quote(symbol)
