"""The easy-to-use pieces: demo account, start guide, plain-words mode and the sticky company bar."""
import os
import tempfile
from unittest import mock

from streamlit.testing.v1 import AppTest

from core import accounts as acc
from core import ui

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")


def _patched(store):
    return (mock.patch("core.trading_ui.get_store", lambda: store), mock.patch("core.portfolio_ui.get_store", lambda: store))


def test_try_a_demo_makes_a_guest_with_holdings_who_is_not_ranked_or_listed():
    from core import portfolio_ui
    store = acc.FileStore(tempfile.mkdtemp())
    acc.create_account(store, "Real Person", 100000)
    a, b = _patched(store)
    with a, b:
        app = AppTest.from_file(APP, default_timeout=240).run()
        assert not app.exception and app.button(key="gate_demo")
        app.button(key="gate_demo").click().run()
        assert not app.exception
        guests = [n for n in store.names() if acc.is_guest_name(n)]
        assert len(guests) == 1 and guests[0].startswith("Guest-")
        pf = acc.load_account(store, guests[0])
        assert pf.demo and len(pf.holdings) >= 3 and pf.deposited == 100000 and 0 < pf.balance < 100000
        ranked = portfolio_ui._ranked(store.all())
        assert [r["Name"] for r in ranked] == ["Real Person"]                      # the guest is not on the leaderboard


def test_returning_user_list_hides_guest_accounts():
    store = acc.FileStore(tempfile.mkdtemp())
    acc.create_account(store, "Asha K", 100000)
    acc.create_account(store, "Guest-1234", 100000)
    a, b = _patched(store)
    with a, b:
        app = AppTest.from_file(APP, default_timeout=240).run()
        app.radio(key="gate_mode").set_value("Returning user").run()
        assert list(app.selectbox(key="gate_pick").options) == ["Asha K"]


def test_the_start_guide_buttons_switch_tabs_pick_a_company_and_can_be_hidden():
    store = acc.FileStore(tempfile.mkdtemp())
    acc.create_account(store, "Guided", 100000)
    a, b = _patched(store)
    with a, b:
        app = AppTest.from_file(APP, default_timeout=240)
        app.query_params["user"] = "Guided"
        app.run()
        assert not app.exception and app.button(key="guide_trade")
        app.button(key="guide_trade").click().run()
        assert app.session_state["main_tabs"] == "Paper trading" and not app.exception
        app.button(key="guide_bot").click().run()
        assert app.session_state["main_tabs"] == "Ask the bot"
        app.button(key="guide_strong").click().run()
        assert not app.exception and app.session_state["company"].endswith(".NS")
        assert any("Showing" in i.value for i in app.info)
        app.button(key="guide_hide").click().run()
        assert not app.exception and app.button(key="guide_show") and not [x for x in app.button if x.key == "guide_trade"]


def test_plain_words_swaps_the_label_and_keeps_the_finance_term():
    with mock.patch.object(ui.st, "session_state", {"plain_words": True}):
        plain = ui.jargon("Sharpe ratio", "sharpe")
    assert "Reward for the risk taken" in plain and "(Sharpe ratio)" in plain and "swap" not in plain
    with mock.patch.object(ui.st, "session_state", {}):
        normal = ui.jargon("Sharpe ratio", "sharpe")
    assert "Sharpe ratio" in normal and 'class="tip"' in normal and "Reward for the risk taken" in normal      # (i) hint + hover text
    with mock.patch.object(ui.st, "session_state", {"plain_words": True}):
        assert ui.jargon("Some other term", "not_a_term") == "Some other term"              # no translation: unchanged


def test_the_company_bar_is_sticky_and_the_toggle_is_on_the_page():
    store = acc.FileStore(tempfile.mkdtemp())
    acc.create_account(store, "Sticky", 100000)
    a, b = _patched(store)
    with a, b:
        app = AppTest.from_file(APP, default_timeout=240)
        app.query_params["user"] = "Sticky"
        app.run()
        assert not app.exception and app.toggle(key="plain_words")
        app.toggle(key="plain_words").set_value(True).run()
        assert not app.exception
    assert "position: sticky" in ui.STYLE_CSS and "company_bar" in ui.STYLE_CSS
