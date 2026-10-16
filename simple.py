"""Stock Explorer, second site (the dashboard) - Streamlit entry point.  Run with:  streamlit run simple.py

Same safety net as app.py (bootstrap.py): the real page (simple_page.py) runs inside it, a stale or half-loaded module left over
from an update is recovered from, and if the site still cannot load the visitor sees a friendly card, never a traceback.
"""
import os

from bootstrap import run_page

run_page(os.path.join(os.path.dirname(os.path.abspath(__file__)), "simple_page.py"))
