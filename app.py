"""Stock Explorer - Streamlit entry point.  Run with:  streamlit run app.py

This small file only does one job: it runs the real page (stock_page.py) inside a safety net, so that if
something goes wrong, visitors see a short friendly message instead of a technical error.
"""
import os

from core.errors import guard

PAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stock_page.py")

with guard():
    with open(PAGE, encoding="utf-8") as f:
        code = compile(f.read(), PAGE, "exec")
    exec(code, {"__name__": "__main__", "__file__": PAGE})
