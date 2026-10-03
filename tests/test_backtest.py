import numpy as np
import pandas as pd

from core import backtest as bt


def prices(values, start="2018-01-01"):
    return pd.Series(values, index=pd.bdate_range(start, periods=len(values)))


def test_steady_uptrend_matches_buy_and_hold():
    close = prices(np.linspace(100, 400, 2000))
    r = bt.run_backtest(close)
    s, b = r["stats"]["Crossover strategy"], r["stats"]["Buy and hold"]
    assert abs(s["total_return_pct"] - b["total_return_pct"]) < 1   # always invested
    assert r["trades"] == 0


def test_not_enough_history_returns_none():
    assert bt.run_backtest(prices(np.linspace(100, 200, 300))) is None


def test_crash_is_avoided_by_the_rule():
    # climb, crash, stay low: the rule should sell during the crash and fall less
    close = prices(np.concatenate([np.linspace(100, 300, 1200), np.linspace(300, 100, 400), np.full(400, 100.0)]))
    r = bt.run_backtest(close, years=5)
    assert r["sells"].size >= 1
    assert r["stats"]["Crossover strategy"]["worst_fall_pct"] > r["stats"]["Buy and hold"]["worst_fall_pct"]


def test_no_lookahead():
    # The position only changes the day AFTER the signal: the first day of a
    # flipped signal must not earn that day's big jump.
    close = prices(np.concatenate([np.full(1500, 100.0), [100.0, 100.0], np.linspace(100, 300, 200)]))
    r = bt.run_backtest(close, years=5)
    eq = r["equity"]["Crossover strategy"]
    assert eq.iloc[-1] < r["equity"]["Buy and hold"].iloc[-1]   # it joined the climb late, never early


def test_stats_and_verdict_text():
    close = prices(np.linspace(100, 400, 2000))
    r = bt.run_backtest(close)
    assert r["stats"]["Buy and hold"]["worst_fall_pct"] <= 0
    assert "percentage points" in bt.verdict(r)
