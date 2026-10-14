"""Stock Explorer, simple version - Streamlit entry point.  Run with:  streamlit run simple.py

Same safety net as app.py: the real page (simple_page.py) runs inside it, and a stale module left in memory after an
update is dropped and reloaded instead of showing an error.
"""
import os
import sys

from core.errors import guard

PAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "simple_page.py")


def _run_page():
    with open(PAGE, encoding="utf-8") as f:
        code = compile(f.read(), PAGE, "exec")
    exec(code, {"__name__": "__main__", "__file__": PAGE})


with guard():
    try:
        _run_page()
    except ImportError:
        for module in [m for m in sys.modules if m == "core" or m.startswith("core.")]:
            del sys.modules[module]
        _run_page()
