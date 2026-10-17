"""The Daily check: which day is 'today', the indicator votes use only data up to the day before, the comparison with
today's price, the track record, and the screens."""
import os
import tempfile
from datetime import datetime
from unittest import mock

import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest

from core import accounts as acc
from core import daily_check as dc


def _hist(days=300, end="2026-10-13", drift=0.0, seed=3):
    idx = pd.bdate_range(end=end, periods=days)
    close = 100 * np.exp(np.cumsum(np.random.default_rng(seed).normal(drift, 0.01, days)))
    c = pd.Series(close, index=idx)
    return pd.DataFrame({"Open": c, "High": c * 1.01, "Low": c * 0.99, "Close": c, "Volume": 1_000_000.0}, index=idx)


def test_the_call_never_looks_at_the_target_day():
    h = _hist()
    now = datetime(2026, 10, 14, 13, 0)                               # a Wednesday, market open, history ends yesterday
    a = dc.plan(h, now, live_price=104.0, market_open=True)
    b = dc.plan(h, now, live_price=50.0, market_open=True)            # a wildly different price today ...
    ra, rb = dc.evaluate(a["basis"], a), dc.evaluate(b["basis"], b)
    assert ra["prediction"] == rb["prediction"] and ra["votes"] == rb["votes"]      # ... changes nothing about the call
    assert ra["basis_date"] == h.index[-1].date() and ra["target"] == now.date()


def test_a_bar_for_today_in_the_history_is_not_used_to_predict_today():
    h = _hist(end="2026-10-14")                                        # the history already holds today's bar
    now = datetime(2026, 10, 14, 13, 0)
    p = dc.plan(h, now, live_price=101.0, market_open=True)
    assert p["basis"].index[-1].date() == datetime(2026, 10, 13).date() and p["status"] == "live" and p["actual"] == 101.0


def test_before_the_open_there_is_a_call_but_nothing_to_compare():
    now = datetime(2026, 10, 14, 8, 30)
    p = dc.plan(_hist(), now, live_price=None, market_open=False)
    r = dc.evaluate(p["basis"], p)
    assert p["status"] == "pending" and r["prediction"] in ("Up", "Down", "Sideways") and r["matched"] is None
    assert "not available yet" in dc.headline(r)


def test_on_a_weekend_the_last_session_is_checked():
    h = _hist(end="2026-10-16")                                        # a Friday
    now = datetime(2026, 10, 17, 11, 0)                                # Saturday
    p = dc.plan(h, now, market_open=False)
    assert p["status"] == "final" and p["target"] == datetime(2026, 10, 16).date() and p["basis"].index[-1].date() == datetime(2026, 10, 15).date()
    assert "closed today" in p["note"]


def test_matching_the_direction_and_the_range():
    h = _hist(drift=0.004)
    now = datetime(2026, 10, 14, 13, 0)
    prev = float(h["Close"].iloc[-1])
    up = dc.plan(h, now, live_price=prev * 1.03, market_open=True)
    r = dc.evaluate(up["basis"], up)
    assert r["actual_direction"] == "Up" and r["matched"] == (r["prediction"] == "Up")
    flat = dc.plan(h, now, live_price=prev * 1.0001, market_open=True)
    assert dc.evaluate(flat["basis"], flat)["actual_direction"] == "Sideways"
    far = dc.plan(h, now, live_price=prev * 1.5, market_open=True)
    assert dc.evaluate(far["basis"], far)["in_range"] is False


def test_a_strong_uptrend_votes_up_and_a_strong_downtrend_votes_down():
    now = datetime(2026, 10, 14, 13, 0)
    for drift, expected in ((0.006, "Up"), (-0.006, "Down")):
        h = _hist(drift=drift)
        p = dc.plan(h, now, live_price=float(h["Close"].iloc[-1]), market_open=True)
        r = dc.evaluate(p["basis"], p)
        trend = [v["vote"] for v in r["votes"] if v["name"] == "Trend"][0]
        assert trend == (1 if expected == "Up" else -1)


def test_track_record_is_honest_and_uses_only_earlier_data():
    h = _hist()
    rec = dc.track_record(h)
    assert rec["n"] == 60 and 0 <= rec["accuracy"] <= 1 and 0.3 <= rec["baseline"] <= 1
    assert rec["call_n"] <= rec["n"] and (rec["call_accuracy"] is None or 0 <= rec["call_accuracy"] <= 1)
    # changing the LAST day's price must not change the call that was made for the last day
    h2 = h.copy()
    h2.iloc[-1, h2.columns.get_loc("Close")] *= 1.2
    rec2 = dc.track_record(h2)
    assert rec["rows"][-1]["predicted"] == rec2["rows"][-1]["predicted"]
    assert dc.track_record(h.iloc[:50]) is None and dc.evaluate(h.iloc[:30], dc.plan(h, datetime(2026, 10, 14, 13), market_open=True)) is None


APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
SIMPLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "simple.py")


def _open(path, name):
    store = acc.FileStore(tempfile.mkdtemp())
    pf = acc.create_account(store, name, 100000)
    pf.tour_seen = True
    acc.save_account(store, pf)
    app = AppTest.from_file(path, default_timeout=240)
    app.query_params["user"] = name
    if path == SIMPLE:                         # the second site opens in the Dashboard; this test looks at its phone layout
        app.session_state["dash_init"] = True
        app.session_state["terminal_view"] = False
    return store, app


def test_the_daily_check_tab_and_the_simple_card_show_without_errors():
    for path, name in ((APP, "DailyFull"), (SIMPLE, "DailySimple")):
        store, app = _open(path, name)
        with mock.patch("core.trading_ui.get_store", lambda: store), mock.patch("core.portfolio_ui.get_store", lambda: store):
            app.run()
            if path == SIMPLE:
                app.radio(key="spage").set_value("Company").run()
            assert not app.exception
            assert not [m for m in app.markdown if "Reference: E-" in m.value]
            text = " ".join(m.value for m in app.markdown)
            assert ("Leaning" in text) if path == APP else ("Yesterday's signals vs today" in text)


def test_only_the_six_validated_indicators_vote():
    h = _hist()
    p = dc.plan(h, datetime(2026, 10, 14, 13, 0), live_price=100.0, market_open=True)
    r = dc.evaluate(p["basis"], p)
    voters = {v["name"] for v in r["votes"] if v["voting"]}
    assert voters == {"Trend", "Bollinger band", "Stochastic RSI", "Money flow (MFI)", "Where it closed", "Yesterday's move"}
    assert r["n"] == 6 and {"RSI (speed)", "MACD (momentum)", "On-Balance Volume", "Ichimoku cloud"} <= {v["name"] for v in r["votes"] if not v["voting"]}
    assert all(0.0 <= v["gauge"]["pos"] <= 1.0 for v in r["votes"])


def test_the_pictures_build_without_errors():
    from core import daily_visuals as vis
    h = _hist()
    p = dc.plan(h, datetime(2026, 10, 14, 13, 0), live_price=float(h["Close"].iloc[-1]) * 1.01, market_open=True)
    r = dc.evaluate(p["basis"], p)
    voters = [v for v in r["votes"] if v["voting"]]
    assert "Leaning" in vis.hero(r["prediction"], r["score"], voters) and vis.hero("Up", 3, voters).count("dc-dot") >= 6
    assert "dc-band" in vis.range_bar(r["range"][0], r["range"][1], r["prev_close"], r["actual"])
    assert vis.cards(r["votes"]).count("dc-card") == len(r["votes"])
    rec = dc.track_record(p["complete"])
    assert vis.strip(rec["rows"]).count("dc-sq") == rec["n"] and "This rule" in vis.bars(55, 50)
    assert "The call" in vis.versus("Up", "Down", False)


def test_the_second_sites_gauges_use_the_real_sites_key_signal_scales_and_the_real_site_keeps_its_own():
    h = _hist()
    p = dc.plan(h, datetime(2026, 10, 14, 13, 0), live_price=float(h["Close"].iloc[-1]), market_open=True)
    plain = dc.evaluate(p["basis"], p)
    styled = dc.evaluate(p["basis"], p, scales=True)
    assert {v["gauge"]["kind"] for v in plain["votes"]} == {"neutral"}                     # the real site's Daily check: unchanged
    kinds = {v["name"]: v["gauge"]["kind"] for v in styled["votes"]}
    assert set(kinds.values()) == {"grade"}                              # every gauge is the same red-to-green bar as the Trend one
    assert "Volatility" in kinds and len(styled["votes"]) == len(plain["votes"]) + 2        # Z-score and Volatility
    assert (plain["prediction"], plain["score"]) == (styled["prediction"], styled["score"])    # the call itself does not change
    rsi = [v for v in styled["votes"] if v["name"] == "RSI (speed)"][0]["gauge"]
    assert rsi["ends"] == ("Overbought (70)", "Oversold (30)")             # reversal indicators are turned round: red end = stretched high


def _obv_series(up_volume, down_volume, n=300):
    idx = pd.bdate_range("2025-01-01", periods=n)
    close = 100 + np.cumsum(np.where(np.arange(n) % 2 == 0, 1.0, -0.8))             # up, down, up, down... a gentle climb
    volume = np.where(np.arange(n) % 2 == 0, up_volume, down_volume).astype(float)
    return pd.DataFrame({"Open": close, "High": close + 1, "Low": close - 1, "Close": close, "Volume": volume}, index=idx)


def test_on_balance_volume_flow_reads_buyers_or_sellers():
    buyers = dc.indicator_frame(_obv_series(200, 100)).iloc[-1]["obv_flow"]
    sellers = dc.indicator_frame(_obv_series(100, 200)).iloc[-1]["obv_flow"]
    assert buyers > dc.OBV_LEAN and sellers < -dc.OBV_LEAN and abs(buyers + sellers) < 0.05      # same size, opposite sign
    balanced = dc.indicator_frame(_obv_series(100, 100)).iloc[-1]["obv_flow"]
    assert abs(balanced) < dc.OBV_LEAN
    row = dc.indicator_frame(_obv_series(200, 100)).iloc[-1]
    gauge = dc.key_signal_gauges(row)["On-Balance Volume"]
    assert gauge["label"] == "Buyers backing it" and gauge["pos"] > 0.5 and gauge["ends"] == ("Selling", "Buying")
    no_volume = _obv_series(200, 100).drop(columns=["Volume"])
    assert pd.isna(dc.indicator_frame(no_volume).iloc[-1]["obv_flow"])                           # no volume data: no reading, no crash
