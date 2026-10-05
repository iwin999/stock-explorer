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
