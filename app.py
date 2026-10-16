"""Stock Explorer - Streamlit entry point.  Run with:  streamlit run app.py

This small file only does one job: it runs the real page (stock_page.py) inside a safety net (bootstrap.py), so that if
something goes wrong, visitors see a short friendly message instead of a technical error.
"""
import os

from bootstrap import run_page

run_page(os.path.join(os.path.dirname(os.path.abspath(__file__)), "stock_page.py"))
