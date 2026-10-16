"""The five CMT strategies: what each one votes in a clear case, no peeking at the future, and the panel that shows them."""
import numpy as np
import pandas as pd

from datetime import datetime

from core import cmt_strategies as cmt
from core import daily_check as dc
from core import daily_visuals as vis


def _prices(days=420, drift=0.0, seed=5, vol=0.01):
    idx = pd.bdate_range(end="2026-10-13", periods=days)
    close = 100 * np.exp(np.cumsum(np.random.default_rng(seed).normal(drift, vol, days)))
    c = pd.Series(close, index=idx)
    hist = pd.DataFrame({"Open": c, "High": c * 1.01, "Low": c * 0.99, "Close": c, "Volume": 1_000_000.0}, index=idx)
    return hist, pd.Series(100.0, index=idx)                         # a flat market to compare against


def _waves(slope, days=420):
    """A price that rises (or falls) in waves, so it has clear swing highs and lows."""
    idx = pd.bdate_range(end="2026-10-13", periods=days)
    t = np.arange(days)
    c = pd.Series(200 + slope * t + 6 * np.sin(2 * np.pi * t / 20), index=idx)
    hist = pd.DataFrame({"Open": c, "High": c * 1.005, "Low": c * 0.995, "Close": c, "Volume": 1_000_000.0}, index=idx)
    return hist, pd.Series(100.0, index=idx)


def test_a_rising_market_in_waves_votes_up_and_a_falling_one_votes_down():
    up = cmt.signals_frame(*_waves(0.5)).iloc[-1]
    assert up["dow"] == 1 and up["rs"] == 1 and up["fusion"] == 1                     # higher highs and lows, beating a flat index
    down = cmt.signals_frame(*_waves(-0.3)).iloc[-1]
    assert down["dow"] == -1 and down["rs"] == -1 and down["fusion"] == -1


def test_nothing_looks_at_the_future():
    hist, bench = _prices(drift=0.001)
    a = cmt.signals_frame(hist, bench)
    h2 = hist.copy()
    h2.iloc[-1, h2.columns.get_loc("Close")] *= 1.3
    h2.iloc[-1, h2.columns.get_loc("High")] *= 1.3
    b = cmt.signals_frame(h2, bench)
    cols = ["fusion", "dow", "rs", "wyckoff", "fib"]
    assert a[cols].iloc[:-1].fillna(9).equals(b[cols].iloc[:-1].fillna(9))            # every earlier day is unchanged


def test_wyckoff_needs_volume_and_follows_big_effort_with_big_result():
    hist, bench = _prices()
    hist.iloc[-1, hist.columns.get_loc("Volume")] = 4_000_000.0
    hist.iloc[-1, hist.columns.get_loc("Close")] = float(hist["Close"].iloc[-2]) * 1.05
    hist.iloc[-1, hist.columns.get_loc("High")] = hist["Close"].iloc[-1]
    hist.iloc[-1, hist.columns.get_loc("Low")] = hist["Close"].iloc[-2]
    assert cmt.signals_frame(hist, bench).iloc[-1]["wyckoff"] == 1
    no_volume = hist.drop(columns=["Volume"])
    assert pd.isna(cmt.signals_frame(no_volume, bench).iloc[-1]["wyckoff"])


def test_evaluate_gives_the_shape_the_prediction_bar_draws():
    hist, bench = _prices(drift=0.002)
    plan = dc.plan(hist, datetime(2026, 10, 14, 13, 0), live_price=float(hist["Close"].iloc[-1]) * 1.02, market_open=True)
    result = cmt.evaluate(plan["basis"], bench, plan)
    assert [v["name"] for v in result["votes"]] == cmt.NAMES and result["n"] == 5 and result["matched"] in (True, False)
    html = vis.strategies_panel(result, cmt.load_stats(), "", "footer")
    assert html.count('class="pp-sname"') == 5 and "footer" in html and "Back-test" in html and html.count('class="ss-det"') == 5 and "Full view" in html
    assert cmt.evaluate(plan["basis"].iloc[:100], bench, plan) is None                 # too little history
    assert cmt.track_record(plan["complete"], bench)["n"] == 60


def test_the_tested_numbers_are_saved_and_honest():
    stats = cmt.load_stats()
    assert set(stats["strategies"]) == set(cmt.NAMES) and stats["companies"] > 100
    for rec in stats["strategies"].values():
        assert 0.4 < rec["next day"]["last 30% of dates"]["accuracy"] < 0.6          # nothing here claims a magic edge


def test_every_strategy_has_a_full_view_with_a_chart_and_plain_lines():
    hist, bench = _prices(drift=0.002)
    plan = dc.plan(hist, datetime(2026, 10, 14, 13, 0), live_price=float(hist["Close"].iloc[-1]), market_open=True)
    result = cmt.evaluate(plan["basis"], bench, plan)
    html = vis.strategies_panel(result, cmt.load_stats())
    assert html.count('<details class="ss-det"') == 5 and html.count("<svg") == 5 and html.count('class="ss-open"') == 5
    for name in cmt.NAMES:
        view = vis.strategy_view(name, result["view"])
        assert "<svg" in view and "<li>" in view, name
    no_volume = hist.drop(columns=["Volume"])
    plan2 = dc.plan(no_volume, datetime(2026, 10, 14, 13, 0), live_price=float(hist["Close"].iloc[-1]), market_open=True)
    assert "no usable trading volume" in vis.strategy_view("Wyckoff effort vs result", cmt.evaluate(plan2["basis"], bench, plan2)["view"])


def test_the_fusion_full_view_has_a_scrollable_guide_with_english_group_names():
    hist, bench = _prices(drift=0.002)
    plan = dc.plan(hist, datetime(2026, 10, 14, 13, 0), live_price=float(hist["Close"].iloc[-1]), market_open=True)
    result = cmt.evaluate(plan["basis"], bench, plan)
    row = {"group": 2, "stage_name": "Clear uptrend", "verdict": "Confirm", "quality_ok": True, "value_ok": False}
    html = vis.strategy_view("Fusion stage", result["view"], row)
    assert 'class="fg-box"' in html and "<svg" in html
    for name in ("Winner's Circle", "Strong contender", "Momentum only", "Watchlist"):
        assert name in html
    assert "Group 1" not in html and "Group 4" not in html and "&#10007;" not in html          # names, not numbers; no crosses
    assert "Clear uptrend" in html and "200-day" in html and "price-to-book" in html and "Chapter 8" in html
    assert html.count("this company</span>") == 1 and "Strong contender" in html.split("fg-card up here")[1][:200]
    assert "company results are not available" in vis.strategy_view("Fusion stage", result["view"], None)


def test_the_barometer_reads_from_strongly_down_to_strongly_up():
    for score, word in ((-5, "Strongly down"), (-2, "Leans down"), (0, "Balanced"), (1, "Leans up"), (4, "Strongly up")):
        html = vis.barometer(score, 5, 2, 2, 1)
        assert word in html and "<svg" in html and "of 5 strategies read down" in html
    assert vis.barometer(-5, 5, 0, 5, 0) != vis.barometer(5, 5, 5, 0, 0)               # the needle moves
