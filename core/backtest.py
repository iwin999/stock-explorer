"""Backtest: "what if I had followed a rule for the last 5 years?"

The rules live in core/strategies.py. This file replays one of them over history and
compares it with BUY-AND-HOLD (buy on day one, never sell).

Honest simplifications (say these out loud at the exhibition):
  * A signal seen at today's close is acted on at TOMORROW's price - otherwise we would
    be "cheating" by using information we couldn't have had in time.
  * Each switch between stock and cash costs `cost_pct` percent of the portfolio
    (brokerage, taxes and the gap between buy and sell prices). The first purchase costs too.
  * Cash earns nothing while we are out of the stock.
  * Past results say little about the future.
"""
import numpy as np
import pandas as pd

from core import ratios
from core.strategies import STRATEGIES

START_MONEY = 100000.0
YEARS = 5
DEFAULT_COST_PCT = 0.10


def run_backtest(close, strategy="ma_cross", years=YEARS, cost_pct=DEFAULT_COST_PCT, benchmark=None):
    """Replay a rule over the last `years` years. Returns a dict, or None if there is not
    enough history.

    `close` should hold MORE than `years` of data so the rule is already 'warmed up' on the
    first day of the test window. `benchmark` (optional) is the Nifty 50 closing-price Series.
    """
    rule = STRATEGIES[strategy]
    position_all = pd.Series(rule.fn(close.to_numpy(dtype=float)[None, :])[0], index=close.index)

    start = close.index[-1] - pd.DateOffset(years=years)
    window = close.index >= start
    px, position = close[window], position_all[window]
    rows_before = int((~window).sum())
    if len(px) < 250 or rows_before < rule.warmup:
        return None

    cost = cost_pct / 100.0
    daily_move = px.pct_change().fillna(0.0)

    # The position decided at yesterday's close is the one held today. On day one we start
    # from cash and take whatever position the rule already had.
    held = position.shift(1).fillna(position.iloc[0]).astype(float)
    switches = held.diff().abs().fillna(held.iloc[0])          # day one: buying in counts
    strategy_ret = daily_move * held - switches * cost

    hold_switches = pd.Series(0.0, index=px.index)
    hold_switches.iloc[0] = 1.0                                 # buy-and-hold also pays to buy once
    hold_ret = daily_move - hold_switches * cost

    equity = pd.DataFrame({
        "Strategy": START_MONEY * (1 + strategy_ret).cumprod(),
        "Buy and hold": START_MONEY * (1 + hold_ret).cumprod(),
    })

    bench_ret = None
    if benchmark is not None:
        bench_ret = benchmark.pct_change().reindex(px.index).dropna()

    flips = position.diff().fillna(0)
    stats = {}
    for label, ret in (("Strategy", strategy_ret), ("Buy and hold", hold_ret)):
        s = ratios.summary(ret, bench_ret)
        s["final_value"] = float(equity[label].iloc[-1])
        stats[label] = s

    return {
        "name": rule.name,
        "key": strategy,
        "equity": equity,
        "buys": px.index[flips == 1],
        "sells": px.index[flips == -1],
        "stats": stats,
        "daily": {"Strategy": strategy_ret, "Buy and hold": hold_ret},
        "trades": int((flips != 0).sum()),
        "days_invested_pct": float(held.mean() * 100),
        "cost_pct": cost_pct,
        "start": px.index[0],
        "end": px.index[-1],
    }


def verdict(result):
    """One plain-English sentence comparing the two. Never advice."""
    s, b = result["stats"]["Strategy"], result["stats"]["Buy and hold"]
    gap = (s["total_return"] - b["total_return"]) * 100
    who = "beat" if gap > 0 else "trailed"
    sentence = (f"Over the last {YEARS} years the {result['name'].lower()} {who} buy-and-hold by "
                f"{abs(gap):.1f} percentage points ({s['total_return'] * 100:+.1f}% vs "
                f"{b['total_return'] * 100:+.1f}%).")
    if s["max_drawdown"] > b["max_drawdown"]:
        sentence += (f" Its worst fall was gentler ({s['max_drawdown'] * 100:.0f}% vs "
                     f"{b['max_drawdown'] * 100:.0f}%), because it spent time in cash.")
    return sentence


# ---------------- Monte Carlo test of a backtest ----------------
def bootstrap_test(strategy_ret, hold_ret, n_paths=2000, block=10, seed=None):
    """Shuffle the past to see how much the result depended on luck.

    We cut the 5 years of daily results into 10-day blocks, then build 2,000 new
    "alternative histories" by drawing blocks at random (blocks keep short-term patterns
    intact). The same draws are used for the strategy and for buy-and-hold, so the
    comparison is fair. Returns arrays of final returns and worst falls.
    """
    s = np.asarray(strategy_ret, dtype=float)
    h = np.asarray(hold_ret, dtype=float)
    n = len(s)
    rng = np.random.default_rng(seed)
    n_blocks = -(-n // block)
    starts = rng.integers(0, n - block + 1, size=(n_paths, n_blocks))
    idx = (starts[:, :, None] + np.arange(block)).reshape(n_paths, -1)[:, :n]

    def run(r):
        equity = np.cumprod(1 + r[idx], axis=1)
        final = equity[:, -1] - 1
        worst = (equity / np.maximum.accumulate(equity, axis=1) - 1).min(axis=1)
        return final, worst

    s_final, s_worst = run(s)
    h_final, h_worst = run(h)
    return {"strategy_final": s_final, "hold_final": h_final,
            "strategy_worst": s_worst, "hold_worst": h_worst}
