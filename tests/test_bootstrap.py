"""The safety net around both sites: friendly card instead of a traceback, even for import-time failures."""
import os
import sys
import tempfile
from unittest import mock

from streamlit.testing.v1 import AppTest

import bootstrap
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(autouse=True)
def keep_the_same_core_modules():
    """These tests deliberately drop and reload our modules; put the originals back afterwards so other tests keep the same classes."""
    saved = {k: v for k, v in sys.modules.items() if k == "core" or k.startswith("core.")}
    yield
    for name in [k for k in sys.modules if k == "core" or k.startswith("core.")]:
        sys.modules.pop(name, None)
    sys.modules.update(saved)


def test_the_two_update_time_symptoms_are_recognised_and_ordinary_errors_are_not():
    assert bootstrap._stale(ImportError("cannot import name 'x'"))
    assert bootstrap._stale(KeyError("core.errors"))
    assert not bootstrap._stale(KeyError("price")) and not bootstrap._stale(ValueError("bad"))


def test_purge_drops_only_our_modules_and_survives_a_missing_one():
    import core.errors  # noqa: F401
    saved = {k: v for k, v in sys.modules.items() if k == "core" or k.startswith("core.")}
    try:
        assert "core.errors" in sys.modules
        bootstrap._purge()
        assert "core.errors" not in sys.modules and "streamlit" in sys.modules
        bootstrap._purge()                                   # a second purge, with nothing left to drop, must not fail
    finally:
        sys.modules.update(saved)                            # put the originals back so other tests keep the same classes


def _script(body):
    path = os.path.join(tempfile.mkdtemp(), "entry.py")
    with open(path, "w") as f:
        f.write(f"import sys\nsys.path.insert(0, {ROOT!r})\nimport bootstrap\n{body}\n")
    return path


def test_if_the_guard_cannot_load_the_visitor_sees_a_friendly_card_not_a_traceback():
    page = os.path.join(tempfile.mkdtemp(), "page.py")
    open(page, "w").write("import streamlit as st\nst.write('hello')\n")
    entry = _script(f"bootstrap.run_page({page!r})")
    app = AppTest.from_file(entry, default_timeout=60)
    with mock.patch.object(bootstrap, "_guard", lambda: None):
        app.run()
    text = " ".join(m.value for m in app.markdown)
    assert not app.exception and "The app is being updated" in text and "reference" in text


def test_a_stale_import_error_is_recovered_from_and_the_page_still_runs():
    page = os.path.join(tempfile.mkdtemp(), "page.py")
    open(page, "w").write(
        "import streamlit as st\n"
        "if not st.session_state.get('tried'):\n"
        "    st.session_state['tried'] = True\n"
        "    raise ImportError(\"cannot import name 'show' from 'core.charts'\")\n"
        "st.write('page ran')\n")
    entry = _script(f"bootstrap.run_page({page!r})")
    app = AppTest.from_file(entry, default_timeout=60)
    app.run()
    assert not app.exception and any("page ran" in m.value for m in app.markdown)


def test_both_entry_points_use_the_safety_net():
    for name in ("app.py", "simple.py"):
        text = open(os.path.join(ROOT, name)).read()
        assert "from bootstrap import run_page" in text and "from core" not in text


def test_the_two_sites_share_a_database_but_never_see_each_others_accounts():
    from core import accounts as acc
    inner = acc.FileStore(tempfile.mkdtemp())
    real, second = acc.NamespacedStore(inner, ""), acc.NamespacedStore(inner, "s2:")
    acc.create_account(real, "Freya", 100000)
    acc.create_account(second, "Freya", 500000)                       # the same name is allowed on each site
    acc.create_account(second, "Asha", 100000)
    assert real.names() == ["Freya"] and second.names() == ["Asha", "Freya"]
    assert acc.load_account(real, "Freya").deposited == 100000 and acc.load_account(second, "Freya").deposited == 500000
    assert len(inner.all()) == 3 and {r["key"] for r in second.all()} == {"freya", "asha"}      # the prefix never leaks out
    pf = acc.load_account(second, "Asha")
    pf.balance -= 1000
    acc.save_account(second, pf)
    assert acc.load_account(real, "Asha") is None and acc.load_account(second, "Asha").balance == pf.balance
    second.delete("asha")
    assert second.names() == ["Freya"] and real.names() == ["Freya"]


def test_a_know_how_button_inside_a_pop_up_unfolds_in_place_instead_of_opening_a_second_pop_up():
    def script():
        import streamlit as st
        from core import ui
        st.session_state["_inline_know_how"] = True
        ui.know_how_button("k1", "Futures", "the full method")

    app = AppTest.from_function(script, default_timeout=30)
    app.run()
    assert not app.exception and [e for e in app.expander if "Know how: Futures" in e.label]
    assert not [b for b in app.button if b.key == "k1"]


def test_an_error_inside_the_order_pop_up_shows_the_friendly_card_not_a_red_box():
    def script():
        import streamlit as st
        from unittest import mock
        from core import terminal_ui, trading_ui as tu, accounts as acc
        import tempfile
        store = acc.FileStore(tempfile.mkdtemp())
        pf = acc.create_account(store, "Pop", 100000)
        st.session_state.portfolio = pf
        with mock.patch.object(tu, "_cash_ticket", side_effect=RuntimeError("boom")):
            terminal_ui._order_dialog("Buy", "RELIANCE.NS", "Reliance", 100.0, True)

    app = AppTest.from_function(script, default_timeout=60)
    app.run()
    text = " ".join(m.value for m in app.markdown)
    assert not app.exception and "Reference: <b>E-" in text and "found an error" in text
