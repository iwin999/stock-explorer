"""Is the visitor on a phone or a tablet? (Decided once, from the browser's own name, so one link can open the right layout.)"""
import streamlit as st

PHONE_WORDS = ("iphone", "ipod", "ipad", "android", "mobile", "tablet", "silk", "kindle")


def user_agent():
    """The browser's name as it announced itself, in lower case ('' if it cannot be read)."""
    try:
        return str(st.context.headers.get("User-Agent") or "").lower()
    except Exception:
        return ""


def on_phone_or_tablet(agent=None):
    """True when the browser says it is a phone or a tablet. An iPad that asks for the desktop site cannot be told apart from a Mac,
    and when the browser cannot be read at all the answer is False, which gives the wide Dashboard."""
    agent = user_agent() if agent is None else agent.lower()
    return any(word in agent for word in PHONE_WORDS)
