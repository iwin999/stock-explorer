"""Is the visitor on a phone? (Decided once, from the browser's own name, so one link can open the right layout.)

Only phones get the simple one-column layout. Tablets and iPads are big enough for the wide Dashboard, so they get it, like computers."""
import streamlit as st


def user_agent():
    """The browser's name as it announced itself, in lower case ('' if it cannot be read)."""
    try:
        return str(st.context.headers.get("User-Agent") or "").lower()
    except Exception:
        return ""


def on_phone(agent=None):
    """True when the browser says it is a phone: an iPhone or iPod, or an Android browser that says "Mobile" (Android tablets do not).
    An iPad's name also says "Mobile", so tablets are ruled out first. When the browser cannot be read the answer is False, which gives
    the wide Dashboard."""
    agent = user_agent() if agent is None else agent.lower()
    if "ipad" in agent or "tablet" in agent:
        return False
    return any(word in agent for word in ("iphone", "ipod", "mobile"))
