"""Backtest: "what if I had followed a simple rule for the last 5 years?"

THE RULE (50/200-day moving-average crossover, a classic):
  * 50-day average rises ABOVE the 200-day average  -> "golden cross" -> hold the stock
  * 50-day average falls BELOW the 200-day average  -> "death cross"  -> sell, sit in cash
We compare it with BUY-AND-HOLD: buy on day one, never sell.

Honest simplifications (say these out loud at the exhibition):
  * No brokerage fees, taxes or slippage.
  * Cash earns nothing while we are out of the stock.
  * A signal seen at today's close is acted on at TOMORROW's price - otherwise we
    would be "cheating" by using information we couldn't have had in time.
  * Past results say little about the future.
"""
import numpy as np
import pandas as pd

from core.indicators import sma

START_MONEY = 100000.0
YEARS = 5


def run_backtest(close, years=YEARS, fast=50, slow=200):
    """Run both strategies over the last `years` years. Returns a dict, or None if
    there is not enough history.

    `close` should hold MORE than `years` of data, so the 200-day average is
    already 'warmed up' on the first day of the test window.
    """
    ma_fast, ma_slow = sma(close, fast), sma(close, slow)
    in_market = (ma_fast > ma_slow).astype(int)          # 1 = hold stock, 0 = cash
    in_market[ma_slow.isna()] = 0                         # no signal until 200 days exist

    # Cut to the test window AFTER the signals are calculated.
    start = close.index[-1] - pd.DateOffset(years=years)
    window = close.index >= start
    px = close[window]
    position = in_market[window]
    if len(px) < 250 or ma_slow[window].isna().any():
        return None

    daily_move = px.pct_change().fillna(0.0)
    # shift(1): the position decided yesterday earns today's move (no peeking ahead).
    strategy_move = daily_move * position.shift(1).fillna(position.iloc[0])

    equity = pd.DataFrame({
        "Crossover strategy": START_MONEY * (1 + strategy_move).cumprod(),
        "Buy and hold": START_MONEY * (1 + daily_move).cumprod(),
    })

    # Days where the signal flipped = trades.
    flips = position.diff().fillna(0)
    buys = px.index[flips == 1]
    sells = px.index[flips == -1]

    return {
        "equity": equity,
        "buys": buys,
        "sells": sells,
        "stats": {name: _stats(equity[name]) for name in equity},
        "trades": int((flips != 0).sum()),
        "days_invested_pct": float(position.mean() * 100),
        "start": px.index[0],
        "end": px.index[-1],
    }


def _stats(curve):
    """Summary numbers for one equity curve (a line of portfolio value over time)."""
    total = curve.iloc[-1] / curve.iloc[0] - 1
    years = (curve.index[-1] - curve.index[0]).days / 365.25
    cagr = (curve.iloc[-1] / curve.iloc[0]) ** (1 / years) - 1 if years > 0 else 0.0
    drawdown = curve / curve.cummax() - 1                # how far below its previous peak
    return {
        "final_value": float(curve.iloc[-1]),
        "total_return_pct": float(total * 100),
        "yearly_return_pct": float(cagr * 100),          # compound annual growth rate
        "worst_fall_pct": float(drawdown.min() * 100),   # "maximum drawdown"
    }


def verdict(result):
    """One plain-English sentence comparing the two. Never advice."""
    s, b = result["stats"]["Crossover strategy"], result["stats"]["Buy and hold"]
    gap = s["total_return_pct"] - b["total_return_pct"]
    who = "beat" if gap > 0 else "trailed"
    sentence = (f"Over the last {YEARS} years the crossover rule {who} buy-and-hold by "
                f"{abs(gap):.1f} percentage points ({s['total_return_pct']:+.1f}% vs "
                f"{b['total_return_pct']:+.1f}%).")
    if s["worst_fall_pct"] > b["worst_fall_pct"]:
        sentence += (f" It also had a gentler worst fall ({s['worst_fall_pct']:.0f}% vs "
                     f"{b['worst_fall_pct']:.0f}%), because it sat in cash during some declines.")
    return sentence
