"""The 'New here? Three easy steps' guide shown at the top of the page for first-time visitors."""
import random

import streamlit as st

from core import companies


def strong_company():
    """A company that looks strong right now: in the Winner's Circle's top group (an uptrend, ahead of the market, with
    good fundamentals) and among the best recent performers. None if the saved data is not available."""
    try:
        from core import fusion_ui
        d = fusion_ui._data()
        table = fusion_ui._classified(d["asof"])
        good = table[table["group"] == 1].sort_values("ret6", ascending=False)
        if good.empty:
            good = table[table["stage"] == 3].sort_values("ret6", ascending=False)
        return random.choice(list(good.index[:8])) if len(good) else None
    except Exception:
        return None


def _show_strong():
    symbol = strong_company()
    if symbol:
        st.session_state["company"] = symbol
        st.session_state["guide_note"] = (f"Showing {companies.NAME_BY_SYMBOL.get(symbol, symbol)}: its price has been "
                                          "rising and it is doing better than the market. Scroll down to see why.")
    else:
        st.session_state["guide_note"] = "Pick any company in the search box below to begin."


def _go(tab):
    st.session_state["main_tabs"] = tab


def _hide():
    st.session_state["guide_hidden"] = True


def _show():
    st.session_state["guide_hidden"] = False


def render():
    if st.session_state.get("guide_hidden"):
        st.button("Show the quick guide", key="guide_show", on_click=_show, type="tertiary")
        return
    with st.container(key="guide_box"):
        st.markdown("#### New here? Three easy steps")
        one, two, three = st.columns(3)
        with one:
            st.markdown("**1. Pick a company**  \nSearch any NSE or BSE company below, or let us suggest a strong one.")
            st.button("Show me a strong company", key="guide_strong", on_click=_show_strong, width="stretch")
        with two:
            st.markdown("**2. Read the signals**  \nColoured bars show how it is doing. Turn on **Plain words** if a term is new.")
            st.button("Ask the bot what a term means", key="guide_bot", on_click=_go, args=("Ask the bot",), width="stretch")
        with three:
            st.markdown("**3. Try a practice trade**  \nBuy and sell with virtual money. Nothing is real, so just explore.")
            st.button("Go to Paper trading", key="guide_trade", on_click=_go, args=("Paper trading",), width="stretch")
        note = st.session_state.pop("guide_note", None)
        if note:
            st.info(note)
        st.button("Hide this guide", key="guide_hide", on_click=_hide, type="tertiary")
