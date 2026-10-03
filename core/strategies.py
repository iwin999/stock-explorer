"""Trading rules, written once and used in two places:

  1. the BACKTEST (replay the past 5 years), and
  2. the FORWARD SIMULATION on the Possible outcomes tab (apply the same rule to
     thousands of simulated futures).

Every rule works on a 2-D array `prices` shaped (paths, days). A historical test is
just one path; a simulation has 2,000 paths. A rule returns an array of the same
shape with 1 = "hold the stock at the close of this day" and 0 = "hold cash".
A position decided at the close of day t is earned on day t+1 (no peeking ahead).
"""
from dataclasses import dataclass
from typing import Callable

import numpy as np


# ---------------- indicator maths on 2-D arrays ----------------
def _sma(x, n):
    """Simple moving average. NaN until n prices exist."""
    c = np.cumsum(x, axis=1)
    out = np.full(x.shape, np.nan)
    lagged = np.concatenate([np.zeros((x.shape[0], 1)), c[:, :-n]], axis=1)
    out[:, n - 1:] = (c[:, n - 1:] - lagged) / n
    return out


def _ema(x, span):
    """Exponential moving average (recent days weigh more), same recursion as pandas ewm(adjust=False)."""
    alpha = 2.0 / (span + 1)
    out = np.empty(x.shape)
    out[:, 0] = x[:, 0]
    for t in range(1, x.shape[1]):
        out[:, t] = alpha * x[:, t] + (1 - alpha) * out[:, t - 1]
    return out


def _rsi(x, n=14):
    """Wilder's RSI, matching core.indicators.rsi."""
    change = np.diff(x, axis=1)
    gain, loss = np.clip(change, 0, None), np.clip(-change, 0, None)
    alpha = 1.0 / n
    avg_g, avg_l = np.empty(gain.shape), np.empty(loss.shape)
    avg_g[:, 0], avg_l[:, 0] = gain[:, 0], loss[:, 0]
    for t in range(1, gain.shape[1]):
        avg_g[:, t] = alpha * gain[:, t] + (1 - alpha) * avg_g[:, t - 1]
        avg_l[:, t] = alpha * loss[:, t] + (1 - alpha) * avg_l[:, t - 1]
    with np.errstate(divide="ignore", invalid="ignore"):
        rsi = 100 - 100 / (1 + avg_g / avg_l)
    rsi = np.where(avg_l == 0, 100.0, rsi)
    out = np.full(x.shape, np.nan)
    out[:, 1:] = rsi
    out[:, :n] = np.nan                      # needs n changes before it is meaningful
    return out


def _bollinger(x, n=20, k=2.0):
    """Middle, upper and lower Bollinger Bands (sample standard deviation, like pandas)."""
    mid = _sma(x, n)
    c1, c2 = np.cumsum(x, axis=1), np.cumsum(x**2, axis=1)
    pad = np.zeros((x.shape[0], 1))
    s1 = c1[:, n - 1:] - np.concatenate([pad, c1[:, :-n]], axis=1)
    s2 = c2[:, n - 1:] - np.concatenate([pad, c2[:, :-n]], axis=1)
    var = np.clip((s2 - s1**2 / n) / (n - 1), 0, None)
    std = np.full(x.shape, np.nan)
    std[:, n - 1:] = np.sqrt(var)
    return mid, mid + k * std, mid - k * std


def _latch(enter, leave):
    """Turn two yes/no signals into a position that is held between them.

    Enter when `enter` is true, stay in until `leave` is true. Works for all paths at once.
    """
    pos = np.zeros(enter.shape, dtype=int)
    for t in range(enter.shape[1]):
        prev = pos[:, t - 1] if t else np.zeros(enter.shape[0], dtype=int)
        pos[:, t] = np.where(enter[:, t], 1, np.where(leave[:, t], 0, prev))
    return pos


# ---------------- the rules ----------------
def ma_cross(prices):
    fast, slow = _sma(prices, 50), _sma(prices, 200)
    return ((fast > slow) & ~np.isnan(slow)).astype(int)


def macd_rule(prices):
    line = _ema(prices, 12) - _ema(prices, 26)
    signal = _ema(line, 9)
    pos = (line > signal).astype(int)
    pos[:, :35] = 0                            # let the averages settle first
    return pos


def rsi_rule(prices):
    rsi = _rsi(prices)
    valid = ~np.isnan(rsi)
    return _latch((rsi < 30) & valid, (rsi > 55) & valid)


def bollinger_rule(prices):
    mid, _, lower = _bollinger(prices)
    valid = ~np.isnan(lower)
    return _latch((prices < lower) & valid, (prices > mid) & valid)


# ---------------- descriptions (plain words + the full "know how") ----------------
@dataclass
class Strategy:
    key: str
    name: str            # tab title
    headline: str        # one line under the title
    fn: Callable
    warmup: int          # days of history the rule needs before it can give a signal
    plain: str           # "In plain English"
    know_how: str        # the in-depth details


STRATEGIES = {
    "ma_cross": Strategy(
        "ma_cross", "Moving-average crossover",
        "Hold the stock while its 50-day average price is above its 200-day average, otherwise stay in cash.",
        ma_cross, 200,
        plain=(
            "- Think of the **50-day average** as the stock's recent mood and the **200-day average** as its long-term mood.\n"
            "- When the recent mood is better than the long-term mood, the rule says: be in the stock.\n"
            "- When it turns worse, the rule says: sell and wait in cash.\n"
            "- The rule tries to catch long climbs and avoid long slides. It is slow, so it can miss quick moves."),
        know_how=(
            "**Rule.** Position = 1 (hold the stock) when the 50-day simple moving average is above the 200-day simple "
            "moving average, else 0 (cash). A switch up is called a golden cross, a switch down a death cross.\n\n"
            "**Factors.** 50-day and 200-day windows. The 200-day average needs 200 days of history, so the test uses "
            "7 years of data and only measures the last 5.\n\n"
            "**How the test is done.**\n"
            "1. Compute both averages for every day.\n"
            "2. Decide the position at each day's close.\n"
            "3. Earn that position on the **next** day's price move (no look-ahead).\n"
            "4. Subtract the trading cost (set above) every time the position changes, including the first purchase.\n"
            "5. Compound the daily results into a growth curve starting at Rs 1,00,000 and compare it with buying on day one and holding.\n\n"
            "**Typical strengths and weaknesses.** Works best in long, steady trends. Whipsaws (many small losses) in "
            "sideways markets, and exits late after a fall begins.")),
    "rsi": Strategy(
        "rsi", "RSI rule",
        "Buy after the stock has fallen hard (RSI below 30) and sell once it recovers (RSI above 55).",
        rsi_rule, 30,
        plain=(
            "- RSI is a 0 to 100 score of how fast the price has been rising or falling lately.\n"
            "- Below 30 means it has fallen quickly, so the rule bets on a bounce back and buys.\n"
            "- It sells once the score recovers above 55.\n"
            "- This is a **bounce-back** idea. It can do well in choppy markets and badly when a stock keeps falling."),
        know_how=(
            "**Rule.** Enter (hold the stock) when the 14-day Relative Strength Index falls below 30. Stay invested until "
            "the RSI rises above 55, then go to cash. Between those levels the previous position is kept.\n\n"
            "**Factors.** 14-day Wilder RSI, entry level 30, exit level 55.\n\n"
            "**Calculation.** RSI = 100 - 100 / (1 + average gain / average loss), where the averages are Wilder's smoothed "
            "averages of daily up-moves and down-moves over 14 days.\n\n"
            "**How the test is done.** Same engine as every rule here: decide at the close, earn the next day's move, "
            "subtract costs on each switch, compound from Rs 1,00,000 and compare with buy-and-hold over 5 years.\n\n"
            "**Typical strengths and weaknesses.** A mean-reversion rule: it is invested only part of the time, so it often "
            "trails buy-and-hold in strong bull markets. In a steady downtrend it keeps buying dips that keep dipping.")),
    "macd": Strategy(
        "macd", "MACD rule",
        "Hold the stock while momentum (MACD) is above its signal line, otherwise stay in cash.",
        macd_rule, 60,
        plain=(
            "- MACD compares a **fast** and a **slow** average of the price to see if momentum is building up or fading.\n"
            "- When momentum is above its own recent average (the signal line), the rule says: be in the stock.\n"
            "- When it drops below, the rule says: be in cash.\n"
            "- It reacts faster than the moving-average crossover, so it trades more often."),
        know_how=(
            "**Rule.** Position = 1 when the MACD line is above its signal line, else 0.\n\n"
            "**Factors.** MACD line = 12-day exponential average minus 26-day exponential average. Signal line = 9-day "
            "exponential average of the MACD line. The first 35 days are ignored while the averages settle.\n\n"
            "**How the test is done.** Decide at the close, earn the next day's move, subtract costs on each switch, "
            "compound from Rs 1,00,000, compare with buy-and-hold over 5 years.\n\n"
            "**Typical strengths and weaknesses.** Quicker than a 50/200 crossover and catches turns earlier, but produces "
            "many more trades, so costs and false signals matter more.")),
    "bollinger": Strategy(
        "bollinger", "Bollinger Bands rule",
        "Buy when the price drops below its usual range (lower band) and sell when it returns to the middle.",
        bollinger_rule, 25,
        plain=(
            "- The **usual range** is a band around the 20-day average price.\n"
            "- If the price drops below the bottom of the band, it is unusually low, so the rule buys.\n"
            "- It sells when the price climbs back to the middle (the average).\n"
            "- Like the RSI rule, this is a bounce-back idea, and it struggles in strong downtrends."),
        know_how=(
            "**Rule.** Enter when the close is below the lower Bollinger Band. Stay invested until the close is above the "
            "middle band, then go to cash.\n\n"
            "**Factors.** 20-day average (middle band); bands are 2 standard deviations above and below it.\n\n"
            "**Calculation.** Standard deviation of the last 20 closes (sample standard deviation); lower band = average - 2 x "
            "standard deviation.\n\n"
            "**How the test is done.** Decide at the close, earn the next day's move, subtract costs on each switch, "
            "compound from Rs 1,00,000, compare with buy-and-hold over 5 years.\n\n"
            "**Typical strengths and weaknesses.** Suits calm, range-bound stocks. A stock in a real breakdown keeps "
            "closing below the band, and the rule keeps buying into the fall.")),
}
