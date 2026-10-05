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
    assert ind.describe_macd(rising)[0] in ("Positive", "Negative")


# ---------------- volume ----------------
def _volume_frame(volume_last5, move, base=1000.0, days=60):
    import numpy as np
    import pandas as pd
    close = np.full(days, 100.0)
    close[-5:] = np.linspace(100, 100 * (1 + move), 5)
    volume = np.full(days, base)
    volume[-5:] = volume_last5
    return pd.DataFrame({"Open": close, "High": close, "Low": close, "Close": close, "Volume": volume},
                        index=pd.date_range("2026-01-01", periods=days))


def test_volume_backing_yes_no_mixed():
    from core import indicators as ind
    assert ind.describe_volume(_volume_frame(1800, 0.05))[0] == "Yes"          # rise on heavy volume
    assert ind.describe_volume(_volume_frame(1800, -0.05))[0] == "Yes"         # fall on heavy volume: sellers are serious
    assert ind.describe_volume(_volume_frame(500, 0.05))[0] == "No"            # rise on thin volume
    assert ind.describe_volume(_volume_frame(1000, 0.05))[0] == "Mixed"        # normal volume
    assert ind.describe_volume(_volume_frame(3000, 0.002))[0] == "Mixed"       # no real move to confirm
    stats = ind.volume_stats(_volume_frame(1800, 0.05))
    assert round(stats["ratio"], 2) == 1.8 and stats["direction"] == "up" and stats["buyers"] == 1.0


def test_volume_is_not_available_when_the_data_is_missing_or_useless():
    from core import indicators as ind
    frame = _volume_frame(1800, 0.05)
    assert ind.describe_volume(frame.assign(Volume=0.0))[0] == "n/a"           # zero = no figure
    assert ind.describe_volume(frame.drop(columns="Volume"))[0] == "n/a"
    assert ind.describe_volume(frame.iloc[:20])[0] == "n/a"                    # too little history
    assert ind.clean_volume(None) is None


def test_zero_volume_days_are_ignored_not_counted_as_quiet_days():
    from core import indicators as ind
    frame = _volume_frame(1800, 0.05)
    frame.iloc[-10:-7, frame.columns.get_loc("Volume")] = 0.0                  # three missing days in the comparison period
    assert ind.describe_volume(frame)[0] == "Yes"


# ---------------- Fibonacci ----------------
def _swing_frame(prices):
    import pandas as pd
    p = pd.Series(prices, dtype=float, index=pd.date_range("2026-01-01", periods=len(prices)))
    return pd.DataFrame({"Open": p, "High": p + 1, "Low": p - 1, "Close": p, "Volume": 1000.0})


def test_fibonacci_levels_after_a_rise_measure_the_pullback_from_the_high():
    import numpy as np
    from core import indicators as ind
    fib = ind.fibonacci_levels(_swing_frame(np.linspace(100, 200, 60)), 60)         # low 99, high 201: swing 102
    assert fib["direction"] == "up" and fib["high"] == 201 and fib["low"] == 99
    levels = dict(fib["levels"])
    assert abs(levels[0.5] - 150.0) < 1e-9 and abs(levels[0.618] - (201 - 0.618 * 102)) < 1e-9
    assert levels[0.236] > levels[0.382] > levels[0.5] > levels[0.618] > levels[0.786]       # pulling back further = lower


def test_fibonacci_levels_after_a_fall_measure_the_bounce_from_the_low():
    import numpy as np
    from core import indicators as ind
    fib = ind.fibonacci_levels(_swing_frame(np.linspace(200, 100, 60)), 60)
    assert fib["direction"] == "down"
    levels = dict(fib["levels"])
    assert abs(levels[0.5] - 150.0) < 1e-9 and levels[0.236] < levels[0.382] < levels[0.5] < levels[0.618] < levels[0.786]


def test_fibonacci_needs_enough_history_and_a_real_swing():
    from core import indicators as ind
    assert ind.fibonacci_levels(_swing_frame([100.0] * 10), 10) is None
    flat = _swing_frame([100.0] * 40)
    flat["High"] = flat["Low"] = flat["Close"]
    assert ind.fibonacci_levels(flat, 40) is None
    assert "not enough" in ind.describe_fibonacci(None)


def test_fibonacci_extensions_go_past_the_swing():
    import numpy as np
    from core import indicators as ind
    up = ind.fibonacci_levels(_swing_frame(np.linspace(100, 200, 60)), 60)               # low 99, high 201, swing 102
    ext = dict(up["extensions"])
    assert abs(ext[1.272] - (99 + 1.272 * 102)) < 1e-9 and abs(ext[1.618] - (99 + 1.618 * 102)) < 1e-9
    assert ext[1.272] > up["high"] and ext[1.618] > ext[1.272]                          # above the high after a rise
    down = ind.fibonacci_levels(_swing_frame(np.linspace(200, 100, 60)), 60)
    dext = dict(down["extensions"])
    assert dext[1.272] < down["low"] and dext[1.618] < dext[1.272]                      # below the low after a fall
    assert "Extension" in ind.describe_fibonacci(up) and "127.2%" in ind.describe_fibonacci(up)
