"""Stock Explorer - Streamlit entry point.  Run with:  streamlit run app.py

This small file only does one job: it runs the real page (stock_page.py) inside a safety net, so that if
something goes wrong, visitors see a short friendly message instead of a technical error.
"""
import os
import sys

from core.errors import guard

PAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stock_page.py")



def _run_page():
    with open(PAGE, encoding="utf-8") as f:
        code = compile(f.read(), PAGE, "exec")
    exec(code, {"__name__": "__main__", "__file__": PAGE})


with guard():
    try:
        _run_page()
    except ImportError:
        # After an update the server can still hold OLD copies of our modules in memory, while the page file is new
        # ("cannot import name ..."). Dropping our modules makes Python load the new files, so no manual reboot is needed.
        for module in [m for m in sys.modules if m == "core" or m.startswith("core.")]:
            del sys.modules[module]
        _run_page()
