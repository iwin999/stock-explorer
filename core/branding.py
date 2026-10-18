"""The site's name, kept in ONE place so it can be changed at the last minute.

How to change it:
  * Quickest, no code and no push: in the app's Secrets (share.streamlit.io, the app's menu, Settings, Secrets) add a line
        site_name = "Your New Name"
    and save. The app restarts and every page, the About box, the chat helper and the error e-mails use the new name.
  * Or edit DEFAULT_NAME below and push.

Long texts in the code still say "Stock Explorer"; apply() swaps that for the current name whenever a text is shown, and unapply()
turns a name typed by a visitor back, so the chat helper still understands "what is <your new name>?".
"""
import html
import os
import re

import streamlit as st

DEFAULT_NAME = "Stock Explorer"
WRITTEN_AS = "Stock Explorer"            # how the name is spelled inside the long texts in the code (do not change)
MAX_LENGTH = 40
GUIDE_URL = "https://cdn.jsdelivr.net/gh/iwin999/stock-explorer@main/docs/Presenter-Guide.pdf"       # the presenter's guide (the PDF in the repository)


def name():
    """The current name: the 'site_name' secret, else the SITE_NAME environment variable, else DEFAULT_NAME."""
    value = None
    try:
        value = st.secrets.get("site_name")
    except Exception:
        pass
    value = str(value or os.environ.get("SITE_NAME") or DEFAULT_NAME).strip()[:MAX_LENGTH]
    return value or DEFAULT_NAME


def guide_url():
    """Where the presenter's guide PDF can be read: the 'guide_url' secret, else GUIDE_URL."""
    value = None
    try:
        value = st.secrets.get("guide_url")
    except Exception:
        pass
    return str(value or os.environ.get("GUIDE_URL") or GUIDE_URL).strip()


def safe():
    """The name made safe to put inside HTML."""
    return html.escape(name())


def apply(text):
    """A text written with the original name, with the current name in its place."""
    current = name()
    return text if current == WRITTEN_AS else str(text).replace(WRITTEN_AS, current)


def unapply(text):
    """A visitor's text with the current name turned back into the original (so the chat helper's notes still match it)."""
    current = name()
    return text if current == WRITTEN_AS else re.sub(re.escape(current), WRITTEN_AS, str(text), flags=re.IGNORECASE)
