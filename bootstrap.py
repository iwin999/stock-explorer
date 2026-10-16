"""The safety net around both sites' pages (used by app.py and simple.py).

It has to work even when the site's own code is half-way through an update, so it lives outside the `core` package and imports
`core.errors` only inside a retry loop. Two things used to escape it and show a raw Streamlit traceback:
  * an import error while the server still held OLD copies of our modules after an update, and
  * a KeyError such as 'core.errors', which happens when one visitor's page drops stale modules while another visitor's page is
    importing them at the same moment.
Now the modules are dropped under a lock (only once, and only for these two symptoms), the import is retried, and if the site
still cannot load, the visitor sees a short friendly 'being updated' card instead of a traceback.
"""
import html
import sys
import threading
import time
import uuid

import streamlit as st

ADMIN_EMAIL = "shahfreya002@gmail.com"


@st.cache_resource
def _lock():
    return threading.RLock()


def _purge():
    """Forget our modules so the next import reads the new files from disk (done under a lock, and tolerant of a race)."""
    with _lock():
        for name in [m for m in list(sys.modules) if m == "core" or m.startswith("core.")]:
            sys.modules.pop(name, None)


def _guard():
    """core.errors.guard, retried a few times because it can fail briefly during an update. None if it never loads."""
    for _ in range(6):
        try:
            from core.errors import guard
            return guard
        except Exception:                                  # ImportError, or a KeyError from a half-finished update
            time.sleep(0.4)
    return None


def _stale(error):
    """True for the two update-time symptoms: an ImportError, or a KeyError naming one of our modules."""
    if isinstance(error, ImportError):
        return True
    return isinstance(error, KeyError) and str(error).strip("'\" ").startswith("core")


def _fallback():
    code = "E-" + uuid.uuid4().hex[:6].upper()
    st.markdown(
        '<div style="border:1px solid #c9d2e0;background:#f3f5f8;border-radius:8px;padding:1.1rem 1.4rem;margin:1rem 0;color:#1b2430">'
        '<div style="font-size:1.4rem;font-weight:700;color:#1d3557;margin-bottom:.4rem">The app is being updated</div>'
        "<p>A new version is being installed. Please wait a few seconds and refresh the page.</p>"
        f'<p style="font-size:.95rem;color:#5b6573">If it keeps happening, please write to the admin at '
        f'<a href="mailto:{ADMIN_EMAIL}">{ADMIN_EMAIL}</a> and quote reference <b>{html.escape(code)}</b>.</p></div>',
        unsafe_allow_html=True)


def run_page(page_path):
    """Run a page file inside the friendly-error net, recovering from a stale or half-loaded update."""
    guard = _guard()
    if guard is None:
        _fallback()
        return

    def run():
        with open(page_path, encoding="utf-8") as f:
            code = compile(f.read(), page_path, "exec")
        exec(code, {"__name__": "__main__", "__file__": page_path})

    with guard():
        try:
            run()
        except Exception as error:
            if not _stale(error):
                raise
            _purge()
            run()
