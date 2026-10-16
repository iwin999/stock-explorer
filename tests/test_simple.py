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


def _app(name, tour_seen=True, phone=True):
    store = acc.FileStore(tempfile.mkdtemp())
    pf = acc.create_account(store, name, 100000)
    pf.tour_seen = tour_seen
    acc.save_account(store, pf)
    app = AppTest.from_file(APP, default_timeout=240)
    app.query_params["user"] = name
    if phone:                                  # the second site opens in the Dashboard; these tests look at the phone layout
        app.session_state["dash_init"] = True
        app.session_state["terminal_view"] = False
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


def test_a_bar_names_the_company_being_looked_at_on_both_sites():
    store, app = _app("Barfly")
    a, b = _patches(store)
    with a, b:
        app.run()
        app.session_state["scompany"] = "TCS.NS"
        app.radio(key="spage").set_value("Company").run()
        assert any("companybar-name" in m.value and "Tata Consultancy" in m.value for m in app.markdown)
    full = AppTest.from_file(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py"), default_timeout=240)
    full.query_params["user"] = "Barfly"
    with a, b:
        full.run()
        assert not full.exception
        assert any("companybar-name" in m.value and "You are looking at" in m.value for m in full.markdown)


def test_the_second_site_opens_straight_into_the_dashboard():
    store, app = _app("Termy", phone=False)
    a, b = _patches(store)
    with a, b:
        app.run()
        assert app.toggle(key="terminal_view").value is True                 # no click needed
        assert not app.exception and not _errors(app)
        text = " ".join(m.value for m in app.markdown)
        assert "MCGS Stock Explorer" in text and "Portfolio value" in text
        assert app.toggle(key="dark_site").value is False and app.toggle(key="dark_chart").value is False   # opens in the normal light look
        assert [x for x in app.button if x.key == "term_buy_btn"] and [x for x in app.button if x.key == "term_exit_btn"]
        assert [x for x in app.button if x.key == "term_exit_btn"][0].disabled is True            # nothing held yet
        assert app.selectbox(key="term_refresh").value == "15 seconds"
        app.selectbox(key="term_refresh").set_value("Off").run()
        assert not app.exception
        app.toggle(key="terminal_view").set_value(False).run()          # and back to the tabs
        assert not app.exception and [x for x in app.radio if x.key == "spage"]            # back in the phone layout


def test_the_full_site_has_no_dashboard_switch():
    """The Dashboard view belongs to the simple site only; the full site must not change."""
    full = AppTest.from_file(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py"), default_timeout=240)
    store, _ = _app("FullOnly")
    full.query_params["user"] = "FullOnly"
    a, b = _patches(store)
    with a, b:
        full.run()
        assert not full.exception and not [t for t in full.toggle if t.key == "terminal_view"]


def test_the_dashboard_search_is_one_compact_row_without_the_live_search_drawer():
    store, app = _app("Compact", phone=False)
    a, b = _patches(store)
    with a, b:
        app.run()
        assert not app.exception
        box = app.selectbox(key="company")
        assert box.placeholder == "SEARCH STOCK" and box.label == "Search stock"
        assert not [e for e in app.expander if "Yahoo Finance live" in e.label]
        assert not [t for t in app.text_input if t.key == "live_query"]


def test_the_dashboard_shows_one_two_or_four_charts_in_any_timeframe_without_errors():
    store, app = _app("Mtf", phone=False)
    a, b = _patches(store)
    with a, b:
        app.run()
        assert not app.exception
        for layout, tf in (("1 chart", "Weekly"), ("2 charts", None), ("4 charts", None), ("1 chart", "Monthly"), ("1 chart", "Daily")):
            app.session_state["mtf_layout"] = layout
            if tf:
                app.session_state["mtf_tf"] = tf
            app.run()
            assert not app.exception and not _errors(app), (layout, tf)


def test_weekly_and_monthly_candles_are_built_from_the_daily_ones():
    import numpy as np
    import pandas as pd
    from core import multi_chart as mc
    idx = pd.bdate_range("2025-01-01", periods=300)
    c = pd.Series(np.linspace(100, 160, 300), index=idx)
    h = pd.DataFrame({"Open": c, "High": c + 1, "Low": c - 1, "Close": c, "Volume": 1000.0}, index=idx)
    week = mc.resample(h, "Weekly")
    assert len(week) < len(h) / 4 and week["Volume"].iloc[1] == 5000.0 and week["High"].iloc[1] == h["High"].iloc[3:8].max()
    assert mc.resample(h, "Daily") is h and len(mc.resample(h, "Monthly")) <= 15
    fig = mc.figure(h, "TEST", "Weekly", 52, show_fib=True)
    assert any("week" in (t.name or "") for t in fig.data)


def test_the_about_dialog_on_the_second_site_shows_the_second_sites_text():
    store, app = _app("Abouter", phone=False)
    a, b = _patches(store)
    with a, b:
        app.run()
        app.button(key="about_btn").click().run()
        assert not app.exception
        text = " ".join(m.value for m in app.markdown)
        assert "Search stock" in text and "Possible outcomes" not in text and "Black-Scholes" not in text


def test_the_second_site_has_its_own_leaderboard_and_its_own_accounts():
    import streamlit as st
    from core import accounts as acc
    st.cache_data.clear()                       # the leaderboard is cached for 10 seconds, so start from a clean slate
    inner = acc.FileStore(tempfile.mkdtemp())
    real = acc.NamespacedStore(inner, "")
    acc.create_account(real, "RealOnly", 100000)                                       # an account on the real site
    second = acc.NamespacedStore(inner, "s2:")
    for n in ("Zed", "Yara"):
        pf = acc.create_account(second, n, 100000)
        pf.tour_seen = True
        acc.save_account(second, pf)
    app = AppTest.from_file(APP, default_timeout=240)
    app.query_params["user"] = "Zed"
    app.session_state["dash_init"] = True
    app.session_state["terminal_view"] = True
    with mock.patch("core.trading_ui._file_store", lambda: inner), mock.patch("core.trading_ui.st.secrets", {}):
        app.run()
        assert not app.exception
        text = " ".join(m.value for m in app.markdown)
        assert "Leaderboard" in text and "Zed" in text and "Yara" in text and "RealOnly" not in text
