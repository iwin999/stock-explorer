"""The simple site (simple.py): every page opens without an error, the tour walks through all its steps, and a practice
purchase and sale work from the company page."""
import os
import tempfile
from unittest import mock

from streamlit.testing.v1 import AppTest

from core import accounts as acc
from core import simple_words as words
from core import tour

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "simple.py")
PRICES = {"RELIANCE.NS": 1000.0, "TCS.NS": 3000.0}


def _app(name, tour_seen=True):
    store = acc.FileStore(tempfile.mkdtemp())
    pf = acc.create_account(store, name, 100000)
    pf.tour_seen = tour_seen
    acc.save_account(store, pf)
    app = AppTest.from_file(APP, default_timeout=240)
    app.query_params["user"] = name
    return store, app


def _patches(store):
    return (mock.patch("core.trading_ui.get_store", lambda: store), mock.patch("core.portfolio_ui.get_store", lambda: store))


def _errors(app):
    return [m.value for m in app.markdown if "Reference: E-" in m.value]


def test_every_page_opens_cleanly():
    store, app = _app("Pages")
    a, b = _patches(store)
    with a, b:
        app.run()
        assert not app.exception and not _errors(app)
        for page in ("Company", "Portfolio", "Learn", "Home"):
            app.radio(key="spage").set_value(page).run()
            assert not app.exception and not _errors(app), page


def test_the_tour_is_offered_once_and_walks_through_every_step():
    store, app = _app("Newbie", tour_seen=False)
    a, b = _patches(store)
    with a, b:
        app.run()
        assert [x for x in app.button if x.key == "tour_yes"], "the first-time prompt should be offered"
        [x for x in app.button if x.key == "tour_yes"][0].click().run()
        seen_pages = []
        for step in range(len(tour.STEPS)):
            assert not app.exception and not _errors(app), step
            assert app.session_state["tour_step"] == step
            seen_pages.append(app.session_state["spage"])
            assert any("Step %d of %d" % (step + 1, len(tour.STEPS)) in c.value for c in app.caption)
            [x for x in app.button if x.key == "tour_next"][0].click().run()
        assert app.session_state["tour_step"] is None
        assert set(seen_pages) == {"Home", "Company", "Portfolio", "Learn"}
        assert acc.load_account(store, "Newbie").tour_seen is True
        assert not [x for x in app.button if x.key == "tour_yes"], "the prompt must not come back"


def test_not_now_hides_the_prompt_for_good():
    store, app = _app("Shy", tour_seen=False)
    a, b = _patches(store)
    with a, b:
        app.run()
        [x for x in app.button if x.key == "tour_no"][0].click().run()
        assert acc.load_account(store, "Shy").tour_seen is True
        assert not [x for x in app.button if x.key == "tour_yes"]


def test_buy_then_sell_from_the_company_page():
    store, app = _app("Trader")
    a, b = _patches(store)
    with a, b, mock.patch("core.market_data.get_latest_price", lambda s: PRICES.get(s)), \
            mock.patch("core.live.live_quote", lambda s: None):
        app.run()
        app.session_state["scompany"] = "RELIANCE.NS"
        app.radio(key="spage").set_value("Company").run()
        assert not app.exception and not _errors(app)
        [x for x in app.button if x.key == "s_buy"][0].click().run()
        assert not app.exception
        pf = acc.load_account(store, "Trader")
        assert pf.holdings.get("RELIANCE.NS", {}).get("quantity", 0) >= 1
        app.radio(key="spage").set_value("Portfolio").run()
        assert not app.exception and [x for x in app.button if x.key == "sellrow_RELIANCE.NS"]
        [x for x in app.button if x.key == "sellrow_RELIANCE.NS"][0].click().run()
        assert app.session_state["spage"] == "Company" and app.session_state["s_mode"] == "Sell"
        [x for x in app.button if x.key == "s_sell"][0].click().run()
        assert not app.exception
        assert "RELIANCE.NS" not in acc.load_account(store, "Trader").holdings


def test_plain_words():
    import pandas as pd
    close = pd.Series(range(100, 400), index=pd.bdate_range("2024-01-01", periods=300), dtype=float)
    hist = pd.DataFrame({"Close": close})
    kinds = {h: k for h, _, k in words.verdict(hist)}
    assert kinds["Direction"] == "up"
    assert words.move_words(5, 1.0)[1] == "up" and words.move_words(-5, -1.0)[1] == "down"
    assert "lost" in words.gain_words(-100, -1.0)


def test_searching_with_a_spelling_slip_opens_or_lists_the_company():
    assert words.resolve_search("RELIANCE.NS") == ("open", "RELIANCE.NS")
    action, found = words.resolve_search("relience")
    assert action == "list" and found[0] == "RELIANCE.NS"
    assert words.resolve_search("zomato")[1] == "ETERNAL.NS"                    # an old name opens today's company
    assert words.resolve_search("qqqqzzzz") == ("none", [])
