"""Friendly error screens.

Instead of showing visitors a long technical error, the page shows one of three short messages:

  * NETWORK    - the internet or a data service could not be reached
  * UPDATING   - the app's files changed while someone was using it (an update is being installed)
  * UNEXPECTED - anything else. The full technical details go to the server log (for the admin),
                 and the visitor gets a short reference code to quote.

Streamlit's own "rerun" and "stop" signals are not ordinary errors (they are not subclasses of Exception),
so they pass straight through this file untouched.
"""
import contextlib
import errno
import logging
import socket
import uuid

import streamlit as st

log = logging.getLogger("stock_explorer.errors")

DEFAULT_ADMIN_EMAIL = "shahfreya002@gmail.com"

NETWORK, UPDATING, UNEXPECTED = "network", "updating", "unexpected"

_NETWORK_ERRNOS = {errno.ECONNREFUSED, errno.ECONNRESET, errno.ECONNABORTED, errno.ENETUNREACH,
                   errno.EHOSTUNREACH, errno.ETIMEDOUT, errno.EPIPE}
_NETWORK_WORDS = ("failed to resolve", "name or service not known", "temporary failure in name resolution",
                  "max retries exceeded", "connection refused", "connection reset", "connection aborted",
                  "timed out", "network is unreachable", "too many requests", "nodename nor servname",
                  "could not reach", "remote end closed")
_NETWORK_CLASS_HINTS = ("requests.exceptions.connection", "requests.exceptions.timeout", "requests.exceptions.readtimeout",
                        "requests.exceptions.connecttimeout", "urllib3.exceptions", "yfinance.exceptions.yfratelimit",
                        "curl_cffi.requests.exceptions", "ssl.sslerror", "http.client.remotedisconnected")


def admin_email():
    """The contact address. Can be overridden with `admin_email` in the app's secrets."""
    try:
        return str(st.secrets["admin_email"]).strip() or DEFAULT_ADMIN_EMAIL
    except Exception:
        return DEFAULT_ADMIN_EMAIL


def _chain(exc):
    """The error and everything that caused it."""
    seen = []
    while exc is not None and exc not in seen:
        seen.append(exc)
        exc = exc.__cause__ or exc.__context__
    return seen


def classify(exc):
    """NETWORK, UPDATING or UNEXPECTED for an exception (looking at the whole chain of causes)."""
    for e in _chain(exc):
        full_name = f"{type(e).__module__}.{type(e).__name__}".lower()
        text = str(e).lower()
        if isinstance(e, (ConnectionError, TimeoutError, socket.gaierror, socket.timeout)):
            return NETWORK
        if isinstance(e, OSError) and e.errno in _NETWORK_ERRNOS:
            return NETWORK
        if any(full_name.startswith(h) for h in _NETWORK_CLASS_HINTS):
            return NETWORK
        if any(w in text for w in _NETWORK_WORDS):
            return NETWORK
    if isinstance(exc, (ImportError, SyntaxError)):      # app files changed while the app was running
        return UPDATING
    return UNEXPECTED


def _card(title, body_html, tone="info"):
    st.markdown(f'<div class="error-card {tone}"><div class="error-title">{title}</div>{body_html}</div>',
                unsafe_allow_html=True)


def show(kind, reference=None):
    """Draw the friendly message for an error kind."""
    mail = admin_email()
    link = f'<a href="mailto:{mail}">{mail}</a>'
    if kind == UPDATING:
        _card("The app is being updated",
              f"<p>This usually takes about 2 minutes. Thank you for your patience!</p>"
              f"<p class='small'>(If it takes much longer, please contact the admin at {link}.)</p>")
    elif kind == NETWORK:
        _card("Network issue",
              "<p>We could not connect to the internet or to our data services. "
              "Please check your connection, then try again in a moment.</p>"
              f"<p class='small'>If the problem continues, please contact the admin at {link}.</p>", tone="warn")
        if st.button("Try again", key=f"retry_{uuid.uuid4().hex[:6]}"):
            st.rerun()
    else:
        ref = f"<p class='small'>Reference: <b>{reference}</b> (please quote it when you write to us)</p>" if reference else ""
        subject = f"Stock Explorer error {reference or ''}".strip().replace(" ", "%20")
        _card("Congratulations! You have found an error",
              "<p>You have given us a chance to improve the app by discovering something we had not seen. "
              "Please contact the admin so it can be fixed, and so that you can carry on exploring the app.</p>"
              f"<p>Contact: <a href='mailto:{mail}?subject={subject}'>{mail}</a></p>{ref}", tone="info")


@contextlib.contextmanager
def guard():
    """Wrap a piece of the page: if it fails, show a friendly message instead of the technical error.

    Works as `with guard():` and as a decorator `@guard()`.
    """
    try:
        yield
    except Exception as exc:                              # Streamlit's rerun/stop signals are not Exceptions
        kind = classify(exc)
        reference = None
        if kind == UNEXPECTED:
            reference = "E-" + uuid.uuid4().hex[:6].upper()
            log.exception("Unexpected error %s", reference)       # full details go to the server log only
        else:
            log.warning("%s problem: %r", kind, exc)
        show(kind, reference)
