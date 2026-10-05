"""Where each Key signal sits on a coloured scale (the same idea as the bars under Risk and return).

Each function returns a dict the screen turns into a bar with a pointer and a one-word verdict:
  pos    - 0 to 1, where the pointer sits (left to right)
  label  - the verdict word under the bar
  kind   - "grade" (red to green: left is weak, right is strong), "neutral" (blue: a description, not a grade) or
           "zones" (a bar with its own colour bands, such as RSI's oversold / balanced / overbought)
  ends   - the words at the left and right ends of the bar
  bar    - for "zones", the CSS colour bands
"""
import math

import numpy as np

from core import indicators as ind


def _clip(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, float(x)))


def rsi_scale(close):
    value = float(ind.rsi(close).iloc[-1])
    label = "Oversold" if value <= 30 else "Overbought" if value >= 70 else "Balanced"
    return {"pos": _clip(value / 100), "label": label, "kind": "zones", "ends": ("Oversold (30)", "Overbought (70)"),
            "bar": "linear-gradient(90deg, #9fd0b8 0%, #9fd0b8 30%, #e3e8ee 30%, #e3e8ee 70%, #e9a59d 70%, #e9a59d 100%)"}


def macd_scale(close):
    line, sig, hist = ind.macd(close)
    gap = float(hist.iloc[-1] / close.iloc[-1] * 100)          # momentum gap as a % of the price
    pos = _clip(0.5 + gap / 2.0)                                # a gap of +/-1% of the price is the full width
    word = "Rising" if gap > 0 else "Falling"                   # always agrees with the card (Positive / Negative)
    label = f"Slightly {word.lower()}" if abs(pos - 0.5) < 0.1 else word
    return {"pos": pos, "label": label, "kind": "grade", "ends": ("Falling", "Rising")}


def trend_scale(close):
    price = float(close.iloc[-1])
    ma = ind.sma(close, 200).iloc[-1]
    if ma != ma:
        ma = ind.sma(close, 50).iloc[-1]
    if ma != ma:
        return None
    gap = price / float(ma) - 1                                  # how far the price is above (+) or below (-) its long average
    pos = _clip(0.5 + gap / 0.5)                                 # +/-25% from the average is the full width
    word = ind.describe_trend(close)[0]
    return {"pos": pos, "label": word, "kind": "grade", "ends": ("Downtrend", "Uptrend")}


def volatility_scale(close):
    vol = ind.annualised_volatility(close)
    pos = 1 - _clip((vol - 10) / 40)                             # 10% a year or less = calm (right, green), 50%+ = very bumpy (left, red)
    label = "Calm" if vol < 20 else "Moderate" if vol < 35 else "High"
    return {"pos": pos, "label": label, "kind": "grade", "ends": ("Very bumpy", "Calm")}


def volume_scale(hist):
    stats = ind.volume_stats(hist)
    if stats is None:
        return None
    ratio = stats["ratio"]
    pos = _clip((math.log2(max(ratio, 1e-6)) + 1) / 2)           # 0.5x usual volume = left end, 1x = middle, 2x = right end
    label = "Busy" if ratio >= ind.VOLUME_STRONG else "Thin" if ratio <= ind.VOLUME_WEAK else "Normal"
    return {"pos": pos, "label": label, "kind": "neutral", "ends": ("Thin (0.5x)", "Busy (2x)")}


def rate_signals(hist):
    """{signal key: scale dict} for the Key signals cards (a key is left out when its scale cannot be worked out)."""
    close = hist["Close"]
    out = {}
    for key, fn, arg in (("rsi", rsi_scale, close), ("macd", macd_scale, close), ("trend", trend_scale, close),
                         ("volatility", volatility_scale, close.iloc[-252:]), ("volume_confirmation", volume_scale, hist)):
        try:
            rating = fn(arg)
        except Exception:
            rating = None
        if rating:
            out[key] = rating
    return out
