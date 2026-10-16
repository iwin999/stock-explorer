"""Five strategies from the CMT curriculum, each casting a vote (Up, Down or Neutral) on where the price goes next.

    1  Fusion stage / Winner's Circle  (CMT Level III, Chapter 8)   trend stage and outperformance, as in core/fusion.py
    2  Dow Theory trend                (CMT Level I)                higher highs and higher lows (or lower, lower)
    3  Relative strength vs the market (CMT core topic)             is the stock beating its index?
    4  Wyckoff effort vs result        (CMT Level II)               is heavy volume moving the price, or stalling?
    5  Fibonacci confluence            (CMT Levels I and II)        is the price sitting on a retracement level?

Everything here is worked out from data up to a given day only, so the same functions serve the live call and the back-test.
No Streamlit code. See core/daily_check.py for how a call, a range and the comparison with today's price are made.
"""
import json
import os

import numpy as np
import pandas as pd

from core import daily_check as dc
from core import fusion
from core import indicators as ind

NAMES = ["Fusion stage", "Dow Theory", "Relative strength", "Wyckoff effort vs result", "Fibonacci confluence"]
SOURCE = {"Fusion stage": "CMT Level III, Chapter 8", "Dow Theory": "CMT Level I", "Relative strength": "CMT core topic",
          "Wyckoff effort vs result": "CMT Level II", "Fibonacci confluence": "CMT Levels I and II"}
PIVOT = 5                      # a swing high or low needs this many lower (higher) bars on each side to count
FIB_WINDOW = 126               # the swing for the Fibonacci levels: the last six months
FIB_LEVELS = (0.382, 0.5, 0.618)
FIB_BAND = 0.04                # within 4% of the swing's size from a level counts as "on" the level
STATS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "cmt_strategy_stats.json")


# ---------------- 2. Dow Theory ----------------
def _dow(high, low):
    """+1 when the last two swing highs AND swing lows are rising, -1 when both are falling, else 0.
    A swing point is only known PIVOT days after it happens, so nothing here looks ahead."""
    h, l = high.values, low.values
    n = len(h)
    vote = np.zeros(n)
    sh, sl = [], []                                   # (index, value) of confirmed swing highs and lows
    for t in range(n):
        i = t - PIVOT                                 # the candidate pivot day that has just been confirmed
        if i >= PIVOT:
            if h[i] == h[i - PIVOT:i + PIVOT + 1].max() and (not sh or sh[-1][0] != i):
                sh.append((i, h[i]))
            if l[i] == l[i - PIVOT:i + PIVOT + 1].min() and (not sl or sl[-1][0] != i):
                sl.append((i, l[i]))
        if len(sh) >= 2 and len(sl) >= 2:
            up = sh[-1][1] > sh[-2][1] and sl[-1][1] > sl[-2][1]
            down = sh[-1][1] < sh[-2][1] and sl[-1][1] < sl[-2][1]
            vote[t] = 1 if up else -1 if down else 0
    return pd.Series(vote, index=high.index)


# ---------------- 5. Fibonacci confluence ----------------
def _fib(high, low, close, window=FIB_WINDOW):
    """+1 when a rising swing has pulled back to a 38.2%, 50% or 61.8% level (support), -1 when a falling swing has bounced
    up to one (resistance), else 0. Also returns the depth of the pullback (0 to 1) for the screen."""
    hi = high.rolling(window).max()
    lo = low.rolling(window).min()
    hi_pos = high.rolling(window).apply(np.argmax, raw=True)
    lo_pos = low.rolling(window).apply(np.argmin, raw=True)
    rising = hi_pos > lo_pos
    swing = (hi - lo).replace(0, np.nan)
    depth = pd.Series(np.where(rising, (hi - close) / swing, (close - lo) / swing), index=close.index)
    near = pd.concat([(depth - lv).abs() <= FIB_BAND for lv in FIB_LEVELS], axis=1).any(axis=1)
    vote = pd.Series(0.0, index=close.index)
    vote[near & rising] = 1.0
    vote[near & ~rising] = -1.0
    vote[swing.isna()] = 0.0
    level = pd.Series(np.nan, index=close.index)
    for lv in FIB_LEVELS:
        level[(depth - lv).abs() <= FIB_BAND] = lv
    return vote, depth, rising, level


# ---------------- 4. Wyckoff effort vs result ----------------
def _wyckoff(hist):
    """Effort is volume against its usual level; result is the price move against a typical day's range (ATR).
    Big effort with a big result follows the move (+1 up, -1 down). Big effort with little result is a stall:
    at the bottom of the range it is absorption (+1), at the top it is distribution (-1). Anything else is 0."""
    close, high, low = hist["Close"].astype(float), hist["High"].astype(float), hist["Low"].astype(float)
    vol = ind.clean_volume(hist)
    if vol is None:
        return pd.Series(np.nan, index=close.index), pd.Series(np.nan, index=close.index), pd.Series(np.nan, index=close.index)
    effort = vol / vol.shift(1).rolling(20).mean()
    tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / 14, adjust=False).mean()
    move = close.diff()
    result = move.abs() / atr
    clv = ((close - low) - (high - close)) / (high - low).replace(0, np.nan)
    loc = (close - low.rolling(60).min()) / (high.rolling(60).max() - low.rolling(60).min()).replace(0, np.nan)
    vote = pd.Series(0.0, index=close.index)
    big = effort >= 1.4
    vote[big & (result >= 1.0) & (move > 0) & (clv > 0)] = 1.0
    vote[big & (result >= 1.0) & (move < 0) & (clv < 0)] = -1.0
    stalled = big & (result < 0.6)
    vote[stalled & (loc <= 0.35)] = 1.0
    vote[stalled & (loc >= 0.65)] = -1.0
    vote[effort.isna() | atr.isna()] = np.nan
    return vote, effort, result


# ---------------- 3. relative strength ----------------
def _relative_strength(close, bench):
    """+1 when the stock's line against the index is above its 50-day average and has risen over three months, -1 when
    it is below and has fallen, else 0."""
    b = bench.reindex(close.index).ffill()
    rs = close / b
    above = rs > rs.rolling(50).mean()
    chg = rs / rs.shift(63) - 1
    vote = pd.Series(0.0, index=close.index)
    vote[above & (chg > 0)] = 1.0
    vote[~above & (chg < 0)] = -1.0
    vote[rs.rolling(50).mean().isna() | chg.isna()] = np.nan
    return vote, chg


# ---------------- all five, for every day ----------------
def signals_frame(hist, bench_close):
    """A DataFrame, one row per day, with the five votes (fusion, dow, rs, wyckoff, fib) and the numbers behind them."""
    close = hist["Close"].astype(float)
    high = hist["High"].astype(float) if "High" in hist else close
    low = hist["Low"].astype(float) if "Low" in hist else close
    h2 = hist.copy()
    h2["High"], h2["Low"] = high, low
    tech = fusion.technical_table(close, bench_close)
    f = pd.Series(0.0, index=close.index)
    f[tech["in_circle"]] = 1.0
    f[tech["stage"] == 0] = -1.0
    f[tech["stage"].isna()] = np.nan
    dow = _dow(high, low)
    dow[close.rolling(2 * PIVOT + 20).count() < 2 * PIVOT + 20] = np.nan
    rs, rs_chg = _relative_strength(close, bench_close)
    wy, effort, result = _wyckoff(h2)
    fib, depth, rising, level = _fib(high, low, close)
    return pd.DataFrame({"close": close, "fusion": f, "stage": tech["stage"], "rel6": tech["rel6"], "ret6": tech["ret6"],
                         "dow": dow, "rs": rs, "rs_chg": rs_chg, "wyckoff": wy, "effort": effort, "result": result,
                         "fib": fib, "fib_depth": depth, "fib_rising": rising, "fib_level": level,
                         "daily_vol": close.pct_change().rolling(60, min_periods=20).std()})


def call_from_row(row):
    """(prediction, score, voters) from one row: each strategy with data votes; two net votes decide."""
    vals = [row[k] for k in ("fusion", "dow", "rs", "wyckoff", "fib") if pd.notna(row[k])]
    score = int(sum(vals))
    prediction = dc.UP if score >= dc.VOTE_UP else dc.DOWN if score <= dc.VOTE_DOWN else dc.SIDEWAYS
    return prediction, score, len(vals)


# ---------------- the words ----------------
def entries(row):
    """One dict per strategy (name, source, vote, reading, why) for a row, in the shape the prediction bar draws."""
    def vote(k):
        v = row[k]
        return None if pd.isna(v) else int(v)

    out = []
    stage = {3: "Clear uptrend", 2: "Base of an uptrend", 1: "Base of a downtrend", 0: "Clear downtrend"}.get(
        int(row["stage"]) if pd.notna(row["stage"]) else -1, "Not enough history")
    out.append(("Fusion stage", vote("fusion"), stage,
                "Winner's Circle trend test: in a clear uptrend, up over six months and ahead of the market." if row["fusion"] == 1
                else "In a clear downtrend." if row["fusion"] == -1 else "Not in the Winner's Circle trend, and not in a clear downtrend."))
    v = vote("dow")
    out.append(("Dow Theory", v, {1: "Higher highs, higher lows", -1: "Lower highs, lower lows", 0: "Mixed swings"}.get(v, "Too little history"),
                "Both the swing highs and the swing lows are rising." if v == 1 else
                "Both the swing highs and the swing lows are falling." if v == -1 else "Swing highs and lows do not agree."))
    v = vote("rs")
    chg = row["rs_chg"]
    out.append(("Relative strength", v, f"{chg * 100:+.1f}% vs the market (3 months)" if pd.notna(chg) else "No index data",
                "Beating its index and improving." if v == 1 else "Lagging its index and getting worse." if v == -1 else "Neither clearly beating nor lagging the index."))
    v = vote("wyckoff")
    if v is None:
        out.append(("Wyckoff effort vs result", None, "No volume data", "Needs trading volume."))
    else:
        eff = row["effort"]
        out.append(("Wyckoff effort vs result", v, f"Volume {eff:.1f}x usual",
                    "Heavy volume pushed the price up: effort is being rewarded." if v == 1 and row["result"] >= 1.0 else
                    "Heavy volume with little movement near the lows: sellers are being absorbed." if v == 1 else
                    "Heavy volume pushed the price down: effort is being rewarded the wrong way." if v == -1 and row["result"] >= 1.0 else
                    "Heavy volume with little movement near the highs: buyers may be exhausted." if v == -1 else
                    "Volume is ordinary, or it did not clearly move the price."))
    v = vote("fib")
    lv = row["fib_level"]
    out.append(("Fibonacci confluence", v, f"At the {lv * 100:.1f}% level" if pd.notna(lv) else "Not at a key level",
                "A pullback in an uptrend has reached a retracement level, a common place for support." if v == 1 else
                "A bounce in a downtrend has reached a retracement level, a common place for resistance." if v == -1 else
                "The price is between the key retracement levels."))
    return [{"name": n, "source": SOURCE[n], "voting": True, "vote": 0 if v is None else v, "available": v is not None,
             "reading": r, "why": w} for n, v, r, w in out]


# ---------------- the whole check for one company ----------------
def evaluate(basis_hist, bench_close, plan_info):
    """Same result shape as daily_check.evaluate (so the prediction bar can draw it), made from the five CMT strategies.
    Returns None when there is not enough history."""
    basis_hist = basis_hist[basis_hist["Close"].notna()]
    if len(basis_hist) < 260 or bench_close is None:
        return None
    frame = signals_frame(basis_hist, bench_close)
    row = frame.iloc[-1]
    prediction, score, n = call_from_row(row)
    prev_close = float(row["close"])
    vol = float(row["daily_vol"]) if pd.notna(row["daily_vol"]) else 0.015
    out = {"prediction": prediction, "score": score, "n": n, "votes": entries(row), "prev_close": prev_close,
           "basis_date": basis_hist.index[-1].date(), "range": (prev_close * (1 - vol), prev_close * (1 + vol)), "daily_vol": vol,
           "status": plan_info["status"], "target": plan_info["target"], "note": plan_info["note"], "actual": plan_info["actual"],
           "change": None, "actual_direction": None, "matched": None, "in_range": None}
    if plan_info["actual"]:
        out["change"] = plan_info["actual"] / prev_close - 1
        out["actual_direction"] = dc.direction_of(out["change"], vol)
        out["matched"] = out["actual_direction"] == prediction
        out["in_range"] = out["range"][0] <= plan_info["actual"] <= out["range"][1]
    return out


def track_record(complete, bench_close, days=60):
    """Replay the five-strategy call for each of the last `days` finished days, using only earlier data (same shape and meaning
    as daily_check.track_record)."""
    complete = complete[complete["Close"].notna()]
    if len(complete) < 300 or bench_close is None:
        return None
    frame = signals_frame(complete, bench_close)
    closes = frame["close"]
    rows = []
    for k in range(max(260, len(frame) - days), len(frame)):
        prev = frame.iloc[k - 1]
        prediction, _, _ = call_from_row(prev)
        change = float(closes.iloc[k] / closes.iloc[k - 1] - 1)
        vol = float(prev["daily_vol"]) if pd.notna(prev["daily_vol"]) else 0.015
        actual = dc.direction_of(change, vol)
        rows.append({"date": frame.index[k].date(), "predicted": prediction, "actual": actual, "change": change, "matched": prediction == actual})
    if not rows:
        return None
    hits = sum(r["matched"] for r in rows)
    clear = [r for r in rows if r["predicted"] != dc.SIDEWAYS and r["actual"] != dc.SIDEWAYS]
    call_hits = sum(r["matched"] for r in clear)
    ups = sum(1 for r in clear if r["actual"] == dc.UP)
    return {"rows": rows, "n": len(rows), "hits": hits, "accuracy": hits / len(rows), "call_n": len(clear), "call_hits": call_hits,
            "call_accuracy": call_hits / len(clear) if clear else None,
            "call_baseline": max(ups, len(clear) - ups) / len(clear) if clear else None}


def load_stats():
    """The tested accuracy of each strategy (made by scripts/test_cmt_strategies.py), or {} if the file is missing."""
    try:
        with open(STATS_PATH) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}
