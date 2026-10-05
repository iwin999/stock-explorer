import numpy as np
import pandas as pd

from core import indicators as ind
from core import signal_scales as ss
from core.ui import scale_html


def _frame(prices, volume=None):
    p = pd.Series(np.asarray(prices, dtype=float), index=pd.date_range("2025-01-01", periods=len(prices)))
    return pd.DataFrame({"Open": p, "High": p + 1, "Low": p - 1, "Close": p,
                         "Volume": volume if volume is not None else 1000.0})


def test_every_signal_gets_a_bar_that_agrees_with_its_card():
    rng = np.random.default_rng(3)
    for prices in (np.linspace(100, 220, 400) + rng.normal(0, 1, 400),        # a steady climb
                   np.linspace(220, 100, 400) + rng.normal(0, 1, 400),        # a steady fall
                   100 + rng.normal(0, 2, 400).cumsum()):                       # a wander
        hist = _frame(prices)
        close = hist["Close"]
        r = ss.rate_signals(hist)
        assert set(r) == {"rsi", "macd", "trend", "volatility", "volume_confirmation"}
        assert all(0.0 <= v["pos"] <= 1.0 and v["label"] and len(v["ends"]) == 2 for v in r.values())
        assert r["trend"]["label"] == ind.describe_trend(close)[0]                          # the bar's word is the card's word
        macd_card = ind.describe_macd(close)[0]                                             # Positive / Negative
        assert r["macd"]["label"].lower().endswith("rising" if macd_card == "Positive" else "falling")
        rsi = float(ind.rsi(close).iloc[-1])
        assert abs(r["rsi"]["pos"] - rsi / 100) < 1e-9
        assert (r["rsi"]["label"] == "Oversold") == (rsi <= 30) and (r["rsi"]["label"] == "Overbought") == (rsi >= 70)


def test_bars_point_the_right_way():
    up, down = _frame(np.linspace(100, 220, 400)), _frame(np.linspace(220, 100, 400))
    assert ss.rate_signals(up)["trend"]["pos"] > 0.7 > 0.3 > ss.rate_signals(down)["trend"]["pos"]
    assert ss.rate_signals(up)["macd"]["pos"] >= 0.5 >= ss.rate_signals(down)["macd"]["pos"]
    calm = _frame(100 + np.sin(np.arange(400) / 20))                                         # barely moves
    wild = _frame(100 + np.random.default_rng(0).normal(0, 4, 400).cumsum().clip(-90, 90) + 100)
    assert ss.volatility_scale(calm["Close"])["pos"] > ss.volatility_scale(wild["Close"])["pos"]   # calm sits at the green end


def test_volume_bar_is_missing_when_there_is_no_volume_and_the_html_builds():
    hist = _frame(np.linspace(100, 120, 100), volume=0.0)
    assert "volume_confirmation" not in ss.rate_signals(hist) and ss.volume_scale(hist) is None
    for rating in ss.rate_signals(_frame(np.linspace(100, 120, 100))).values():
        html = scale_html(rating)
        assert "scale-pin" in html and rating["label"] in html
