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
