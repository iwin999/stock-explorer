"""Charts in different timeframes (daily, weekly, monthly candles), one at a time or two or four side by side.

The weekly and monthly candles are built from the daily history: the first open, the highest high, the lowest low, the last
close and the total volume of each week or month. Moving averages are scaled to the timeframe (50 and 200 days on the daily
chart, 10 and 40 weeks on the weekly one, 3 and 10 months on the monthly one: about the same stretch of time).
"""
import pandas as pd

from core import indicators as ind
from core.charts import add_fibonacci, price_chart, zoom_to_window

TIMEFRAMES = ["Daily", "Weekly", "Monthly"]
UNIT = {"Daily": "day", "Weekly": "week", "Monthly": "month"}
MA = {"Daily": (50, 200), "Weekly": (10, 40), "Monthly": (3, 10)}
RULE = {"Weekly": "W-FRI", "Monthly": "ME"}

# How far back to look, as the period buttons name it, in bars of each timeframe
PERIOD_BARS = {
    "Daily": {"6 months": 126, "1 year": 252, "2 years": 504, "5 years": 1260},
    "Weekly": {"6 months": 26, "1 year": 52, "2 years": 104, "5 years": 260},
    "Monthly": {"6 months": 12, "1 year": 12, "2 years": 24, "5 years": 60},        # a monthly chart needs at least a year to say anything
}

# Ready-made views for the two and four chart layouts: (timeframe, how many bars, label)
PRESETS = {
    "Daily · 3 months": ("Daily", 63), "Daily · 6 months": ("Daily", 126), "Daily · 1 year": ("Daily", 252),
    "Weekly · 1 year": ("Weekly", 52), "Weekly · 2 years": ("Weekly", 104), "Weekly · 5 years": ("Weekly", 260),
    "Monthly · 5 years": ("Monthly", 60),
}
DEFAULTS = {2: ["Daily · 6 months", "Weekly · 2 years"],
            4: ["Daily · 3 months", "Daily · 1 year", "Weekly · 2 years", "Monthly · 5 years"]}


def resample(hist, timeframe):
    """The daily history as weekly or monthly candles (unchanged for Daily)."""
    if timeframe == "Daily":
        return hist
    agg = {"Open": "first", "High": "max", "Low": "min", "Close": "last"}
    if "Volume" in hist:
        agg["Volume"] = "sum"
    out = hist.resample(RULE[timeframe]).agg(agg)
    return out.dropna(subset=["Close"])


def figure(hist, symbol_short, timeframe, bars, label="", show_fib=False, height=None, volume=True, title_size=18):
    """One candlestick chart in the chosen timeframe showing the last `bars` candles."""
    data = resample(hist, timeframe)
    ma = MA[timeframe]
    title = f"{symbol_short} · {label}" if label else f"{symbol_short} · {timeframe}"
    fig = price_chart(data, symbol_short, symbol_short, unit=UNIT[timeframe], ma=ma, volume=volume, title=title, title_size=title_size)
    if height:
        fig.update_layout(height=height)
    fib = ind.fibonacci_levels(data, bars) if show_fib else None
    if show_fib and fib:
        add_fibonacci(fig, fib)
    extra = [price for _, price in fib["extensions"]] if fib else ()
    fig = zoom_to_window(fig, data, bars, include=extra, ma=ma)
    if len(data) < 2:
        return fig
    fig.update_layout(legend=dict(orientation="h", y=-0.18, font=dict(size=11)), font=dict(size=13), margin=dict(l=10, r=10, t=44, b=10))
    return fig
