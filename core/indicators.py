"""Technical indicators + a plain-English sentence for each one.

All functions take a pandas Series of closing prices (oldest first).
"""
import numpy as np
import pandas as pd

TRADING_DAYS = 252  # trading days in a year, used to scale volatility to a year


# ---------------- the numbers ----------------
def sma(close, window):
    """Simple moving average: the average of the last `window` closing prices."""
    return close.rolling(window).mean()


def bollinger(close, window=20, num_std=2):
    """Bollinger Bands: a 20-day average with a band 2 standard deviations above and below.
    Wide bands = price is swinging a lot; narrow bands = calm."""
    middle = sma(close, window)
    spread = close.rolling(window).std()
    return middle, middle + num_std * spread, middle - num_std * spread


def rsi(close, window=14):
    """Relative Strength Index (0-100), Wilder's method.
    Compares the size of recent up-days to recent down-days."""
    change = close.diff()
    gain = change.clip(lower=0)
    loss = -change.clip(upper=0)
    # Wilder's smoothing is an exponential average with alpha = 1/window.
    avg_gain = gain.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    rs = avg_gain / avg_loss
    out = 100 - 100 / (1 + rs)
    # If there were no losses at all, RSI is 100 by definition.
    return out.where(avg_loss != 0, 100.0)


def macd(close, fast=12, slow=26, signal=9):
    """MACD line = 12-day EMA minus 26-day EMA; signal line = 9-day EMA of the MACD line."""
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    line = ema_fast - ema_slow
    sig = line.ewm(span=signal, adjust=False).mean()
    return line, sig, line - sig


def annualised_volatility(close):
    """How much the price typically swings in a year, as a percentage.
    Standard deviation of daily % moves, scaled by sqrt(252)."""
    daily = np.log(close / close.shift(1)).dropna()
    return float(daily.std() * np.sqrt(TRADING_DAYS) * 100)


# ---------------- the plain-English meanings ----------------
def describe_rsi(close):
    value = float(rsi(close).iloc[-1])
    if value >= 70:
        meaning = "The stock has risen quickly and may be overextended, so a pause or dip is possible."
    elif value <= 30:
        meaning = "The stock has fallen quickly and may be due a rebound, though it can keep falling."
    else:
        meaning = "Recent buying and selling are fairly balanced."
    return f"{value:.0f} / 100", meaning


def describe_macd(close):
    line, sig, hist = macd(close)
    if line.iloc[-1] > sig.iloc[-1]:
        return "Positive", "Short-term price movement is stronger than the longer-term movement: a sign of upward momentum."
    return "Negative", "Short-term price movement is weaker than the longer-term movement: a sign of downward momentum."


def describe_trend(close):
    """Trend from where the price sits against its 50- and 200-day averages."""
    price = float(close.iloc[-1])
    ma50 = sma(close, 50).iloc[-1]
    ma200 = sma(close, 200).iloc[-1]
    if pd.isna(ma50):
        return "Unknown", "There is not enough price history to judge the trend."
    if pd.isna(ma200):  # young stock: judge on the 50-day average only
        up = price > ma50
        return ("Uptrend" if up else "Downtrend",
                f"The price is {'above' if up else 'below'} its 50-day average.")
    if price > ma50 > ma200:
        return "Uptrend", "The price is above both its 50-day and 200-day averages: a steady upward direction."
    if price < ma50 < ma200:
        return "Downtrend", "The price is below both its 50-day and 200-day averages: a steady downward direction."
    return "Sideways", "Signals are mixed, with no clear direction at the moment."


def describe_volatility(close):
    vol = annualised_volatility(close)
    if vol < 20:
        meaning = "fairly calm"
    elif vol < 35:
        meaning = "moderately active"
    else:
        meaning = "highly active"
    return f"{vol:.0f}%", (f"In a typical year the price moves about {vol:.0f}% up or down. "
                           f"That makes it {meaning}.")


# ---------------- volume ----------------
VOLUME_RECENT_DAYS = 5          # the recent move we look at
VOLUME_BASE_DAYS = 20           # the usual level of volume it is compared with (the 20 days before that)
VOLUME_STRONG, VOLUME_WEAK = 1.15, 0.85      # recent volume at least 15% above usual = "backed"; 15% below = "thin"
VOLUME_MIN_MOVE = 0.01          # a price change smaller than 1% over the 5 days is not a move worth confirming


def clean_volume(hist):
    """The Volume column with zero (a missing day) treated as unknown, or None if there is no usable volume."""
    if hist is None or "Volume" not in hist:
        return None
    vol = hist["Volume"].astype(float).replace(0.0, np.nan)
    window = vol.iloc[-(VOLUME_RECENT_DAYS + VOLUME_BASE_DAYS):]
    if len(window) < VOLUME_RECENT_DAYS + VOLUME_BASE_DAYS or window.notna().sum() < 0.6 * len(window):
        return None
    return vol


def volume_stats(hist):
    """The numbers behind the volume verdict, or None if volume is not available.

    ratio  - average volume of the last 5 sessions / average volume of the 20 sessions before them
    move   - the price change over those 5 sessions
    buyers - the share of the last 20 sessions' volume that came on days the price rose
    verdict - "Yes" (the move had above-average volume), "No" (below-average volume), "Mixed" (about normal, or no move)
    """
    vol = clean_volume(hist)
    if vol is None:
        return None
    close = hist["Close"].astype(float)
    recent = vol.iloc[-VOLUME_RECENT_DAYS:].mean()
    base = vol.iloc[-(VOLUME_RECENT_DAYS + VOLUME_BASE_DAYS):-VOLUME_RECENT_DAYS].mean()
    if not (recent == recent and base == base and base > 0):
        return None
    ratio = float(recent / base)
    move = float(close.iloc[-1] / close.iloc[-VOLUME_RECENT_DAYS - 1] - 1)
    ret = close.pct_change().iloc[-20:]
    v20 = vol.iloc[-20:]
    up, down = v20[ret > 0].sum(), v20[ret < 0].sum()
    buyers = float(up / (up + down)) if (up + down) > 0 else None
    direction = "up" if move > VOLUME_MIN_MOVE else "down" if move < -VOLUME_MIN_MOVE else "flat"
    if direction == "flat":
        verdict = "Mixed"
    else:
        verdict = "Yes" if ratio >= VOLUME_STRONG else "No" if ratio <= VOLUME_WEAK else "Mixed"
    return {"ratio": ratio, "move": move, "buyers": buyers, "direction": direction, "verdict": verdict,
            "latest": float(vol.dropna().iloc[-1])}


def describe_volume(hist):
    """(value, plain-English meaning) for the 'Volume' card: Yes, No, Mixed or n/a."""
    s = volume_stats(hist)
    if s is None:
        return "n/a", "Volume figures are not available for this company right now."
    way = {"up": "rose", "down": "fell", "flat": "barely moved"}[s["direction"]]
    head = (f"In the last {VOLUME_RECENT_DAYS} sessions the price {way}"
            + (f" {abs(s['move']) * 100:.1f}%" if s["direction"] != "flat" else "")
            + f", on {s['ratio']:.1f}x the usual volume. ")
    if s["direction"] == "flat":
        tail = "There is no clear move to confirm."
    elif s["verdict"] == "Yes":
        tail = ("More people took part, so the move is better backed."
                if s["direction"] == "up" else "More people were selling, so the fall is serious.")
    elif s["verdict"] == "No":
        tail = ("Fewer people took part, so the rise is less convincing."
                if s["direction"] == "up" else "Fewer people were selling, so the fall is less convincing.")
    else:
        tail = "Volume is normal, so it neither backs nor weakens the move."
    return s["verdict"], head + tail


# ---------------- Fibonacci retracement ----------------
FIB_RATIOS = (0.236, 0.382, 0.5, 0.618, 0.786)


def fibonacci_levels(hist, days):
    """Fibonacci retracement levels for the last `days` trading days, found automatically.

    The swing is the highest high and the lowest low in the window. If the high came AFTER the low the price has been
    rising, so the levels measure how far it might pull back down from the high (price = high - ratio x swing). If the
    high came BEFORE the low the price has been falling, so the levels measure how far it might bounce up from the low
    (price = low + ratio x swing). Returns None when there is not enough history or no swing.
    """
    if hist is None or len(hist) < 20:
        return None
    view = hist.iloc[-min(days, len(hist)):]
    high, low = float(view["High"].max()), float(view["Low"].min())
    if not (high > low):
        return None
    high_date, low_date = view["High"].idxmax(), view["Low"].idxmin()
    rising = high_date > low_date
    swing = high - low
    levels = [(r, high - r * swing if rising else low + r * swing) for r in FIB_RATIOS]
    return {"high": high, "low": low, "high_date": high_date, "low_date": low_date,
            "direction": "up" if rising else "down", "levels": levels,
            "last": float(view["Close"].iloc[-1])}


def describe_fibonacci(fib):
    """A plain-English sentence about where the price stands against the levels."""
    if fib is None:
        return "There is not enough price history in this period to draw Fibonacci levels."
    price, high, low = fib["last"], fib["high"], fib["low"]
    pulled = (high - price) / (high - low) if fib["direction"] == "up" else (price - low) / (high - low)
    word = "pulled back" if fib["direction"] == "up" else "bounced"
    start = "high" if fib["direction"] == "up" else "low"
    return (f"In this period the price went {'up' if fib['direction'] == 'up' else 'down'}, from Rs {low if fib['direction'] == 'up' else high:,.2f} "
            f"to Rs {high if fib['direction'] == 'up' else low:,.2f}. It has {word} about {abs(pulled) * 100:.0f}% of that move "
            f"from the {start}.")
