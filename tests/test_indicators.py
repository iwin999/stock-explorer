import numpy as np
import pandas as pd

from core import indicators as ind


def test_rsi_extremes():
    up = pd.Series(np.arange(1.0, 60.0))
    assert ind.rsi(up).iloc[-1] == 100
    down = pd.Series(np.arange(60.0, 1.0, -1))
    assert ind.rsi(down).iloc[-1] < 1


def test_sma_and_bollinger():
    s = pd.Series(np.arange(1.0, 41.0))
    assert ind.sma(s, 5).iloc[-1] == 38  # mean of 36..40
    mid, up, lo = ind.bollinger(s)
    assert (up.iloc[-1] > mid.iloc[-1] > lo.iloc[-1])


def test_volatility_of_flat_series_is_zero():
    assert ind.annualised_volatility(pd.Series([100.0] * 50)) == 0


def test_trend_labels():
    rising = pd.Series(np.linspace(100, 300, 300))
    assert ind.describe_trend(rising)[0] == "Uptrend"
    falling = pd.Series(np.linspace(300, 100, 300))
    assert ind.describe_trend(falling)[0] == "Downtrend"
    assert ind.describe_trend(pd.Series([1.0] * 10))[0] == "Unknown"


def test_macd_direction():
    rising = pd.Series(np.linspace(100, 200, 100) + np.sin(np.arange(100)))
    assert ind.describe_macd(rising)[0] in ("Bullish", "Bearish")
