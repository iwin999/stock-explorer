"""The Daily check: what the indicators said BEFORE today's market opened, a trend call for today, and how today is going
against that call.  No Streamlit code here (see core/daily_ui.py).

Method (deliberately simple and fully explained on screen): each indicator, looking only at data up to the previous
trading day, casts a vote of Up (+1), Down (-1) or Neutral (0). The votes are added up:
    +2 or more -> Up,   -2 or less -> Down,   anything in between -> Sideways.
This is a rule of thumb, not a forecast. Day-to-day direction is close to a coin toss, and the track record on the page
shows how often the rule has been right, next to a no-skill baseline, so nobody reads more into it than it deserves.
"""
from datetime import time as dtime

import numpy as np
import pandas as pd

from core import indicators as ind

UP, DOWN, SIDEWAYS = "Up", "Down", "Sideways"
VOTE_UP, VOTE_DOWN = 2, -2             # score needed to call Up / Down
CLOSE_TIME = dtime(15, 30)


# ---------------- indicators, worked out once for the whole history ----------------
def _supertrend_direction(high, low, close, period=10, mult=3.0):
    """+1 while the Supertrend line is below the price (uptrend), -1 while it is above (downtrend)."""
    tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / period, adjust=False).mean()
    mid = (high + low) / 2
    upper, lower = (mid + mult * atr).values, (mid - mult * atr).values
    c = close.values
    final_up, final_lo, direction = upper.copy(), lower.copy(), np.ones(len(c))
    for i in range(1, len(c)):
        final_up[i] = upper[i] if (upper[i] < final_up[i - 1] or c[i - 1] > final_up[i - 1]) else final_up[i - 1]
        final_lo[i] = lower[i] if (lower[i] > final_lo[i - 1] or c[i - 1] < final_lo[i - 1]) else final_lo[i - 1]
        if direction[i - 1] == 1 and c[i] < final_lo[i - 1]:
            direction[i] = -1
        elif direction[i - 1] == -1 and c[i] > final_up[i - 1]:
            direction[i] = 1
        else:
            direction[i] = direction[i - 1]
    return pd.Series(direction, index=close.index)


def indicator_frame(hist):
    """One row per day: the indicator values known at the END of that day (so a row can be used to predict the next day)."""
    close = hist["Close"].astype(float)
    high = hist["High"].astype(float) if "High" in hist else close
    low = hist["Low"].astype(float) if "Low" in hist else close
    line, sig, histo = ind.macd(close)
    mid, upper, lower = ind.bollinger(close)
    rsi14 = ind.rsi(close)
    lo14, hi14 = rsi14.rolling(14).min(), rsi14.rolling(14).max()
    frame = pd.DataFrame({"close": close, "sma50": ind.sma(close, 50), "sma200": ind.sma(close, 200), "rsi": rsi14,
                          "macd_hist": histo, "bb_up": upper, "bb_lo": lower, "mom5": close / close.shift(5) - 1,
                          "ret1": close.pct_change(), "stochrsi": (rsi14 - lo14) / (hi14 - lo14).replace(0, np.nan)})
    frame["clv"] = ((close - low) - (high - close)) / (high - low).replace(0, np.nan)     # -1 closed on the low, +1 on the high
    tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / 14, adjust=False).mean()
    up_move, down_move = high.diff(), -low.diff()
    plus = pd.Series(np.where((up_move > down_move) & (up_move > 0), up_move, 0.0), index=close.index)
    minus = pd.Series(np.where((down_move > up_move) & (down_move > 0), down_move, 0.0), index=close.index)
    frame["pdi"] = 100 * plus.ewm(alpha=1 / 14, adjust=False).mean() / atr
    frame["mdi"] = 100 * minus.ewm(alpha=1 / 14, adjust=False).mean() / atr
    dx = 100 * (frame["pdi"] - frame["mdi"]).abs() / (frame["pdi"] + frame["mdi"]).replace(0, np.nan)
    frame["adx"] = dx.ewm(alpha=1 / 14, adjust=False).mean()
    frame["supertrend"] = _supertrend_direction(high, low, close)
    t9, k26 = (high.rolling(9).max() + low.rolling(9).min()) / 2, (high.rolling(26).max() + low.rolling(26).min()) / 2
    span_a = ((t9 + k26) / 2).shift(26)
    span_b = ((high.rolling(52).max() + low.rolling(52).min()) / 2).shift(26)
    frame["cloud_top"], frame["cloud_bot"] = np.maximum(span_a, span_b), np.minimum(span_a, span_b)
    frame["daily_vol"] = close.pct_change().rolling(60, min_periods=20).std()
    frame["zscore"] = ((close - close.rolling(20).mean()) / close.rolling(20).std().replace(0, np.nan)).clip(-4, 4)
    vol = ind.clean_volume(hist)
    if vol is not None:
        frame["vol_ratio"] = vol.rolling(5).mean() / vol.shift(5).rolling(20).mean()
        typical = (high + low + close) / 3
        flow = typical * vol.fillna(0)
        pos = flow.where(typical > typical.shift(), 0).rolling(14).sum()
        neg = flow.where(typical < typical.shift(), 0).rolling(14).sum()
        frame["mfi"] = 100 - 100 / (1 + pos / neg.replace(0, np.nan))
    else:
        frame["vol_ratio"] = np.nan
        frame["mfi"] = np.nan
    return frame


def _clip(x):
    return float(min(1.0, max(0.0, x)))


def _gauge(pos, label, left, right):
    return {"pos": _clip(pos), "label": label, "ends": (left, right), "kind": "neutral"}


def _entry(name, voting, vote, reading, why, gauge):
    return {"name": name, "voting": voting, "vote": vote, "reading": reading, "why": why, "gauge": gauge}


def _with_real_gauges(entries, real, entries_row=None):
    """Swap each indicator's gauge for the real site's Key-signals style one, and add the Volatility reading."""
    for e in entries:
        if e["name"] in real:
            e["gauge"] = real[e["name"]]
    if "Z-score" in real and entries_row is not None:
        z = entries_row["zscore"]
        entries.append(_entry("Z-score", False, -1 if z > 2 else 1 if z < -2 else 0, f"{z:+.1f} sigma", "How far the price is from its 20-day average",
                              real["Z-score"]))
    if "Volatility" in real:
        entries.append(_entry("Volatility", False, 0, f"{real['Volatility']['label']}", "How much the price swings in a year", real["Volatility"]))
    return entries



def _zones_bar(low, high):
    """The bar used under the real site's RSI: green zone at the low end, grey in the middle, red at the high end."""
    lo, hi = int(low * 100), int(high * 100)
    return (f"linear-gradient(90deg, #9fd0b8 0%, #9fd0b8 {lo}%, #e3e8ee {lo}%, #e3e8ee {hi}%, #e9a59d {hi}%, #e9a59d 100%)")


def _zones(pos, label, left, right, low=0.2, high=0.8):
    return {"pos": _clip(pos), "label": label, "kind": "zones", "ends": (left, right), "bar": _zones_bar(low, high)}


def _grade(pos, label, left, right):
    return {"pos": _clip(pos), "label": label, "kind": "grade", "ends": (left, right)}


def key_signal_gauges(row):
    """Gauges drawn like the real site's Key signals: one red-to-green bar with a pointer and a verdict word under it, by
    indicator name. Red on the left always means 'leans down', green on the right 'leans up'. For indicators that tend to
    reverse from an extreme (Bollinger band, Stochastic RSI, money flow, where the day closed, yesterday's move, RSI) the bar
    is turned round, so the stretched-high end is red and the stretched-low end is green. Used by the second site's panel."""
    out = {}
    c = row["close"]
    ma = row["sma200"] if pd.notna(row["sma200"]) else row["sma50"]
    if pd.notna(ma):
        gap = c / ma - 1
        up = c > row["sma50"] > row["sma200"] if pd.notna(row["sma200"]) else c > row["sma50"]
        down = c < row["sma50"] < row["sma200"] if pd.notna(row["sma200"]) else c < row["sma50"]
        out["Trend"] = _grade(0.5 + gap / 0.5, "Uptrend" if up else "Downtrend" if down else "Sideways", "Downtrend", "Uptrend")
    if pd.notna(row["bb_up"]) and row["bb_up"] > row["bb_lo"]:
        b = (c - row["bb_lo"]) / (row["bb_up"] - row["bb_lo"])
        out["Bollinger band"] = _grade(1 - b, "Stretched high" if b >= 1 else "Stretched low" if b <= 0 else "Inside range",
                                       "Top of range", "Bottom of range")
    if pd.notna(row["stochrsi"]):
        v = row["stochrsi"]
        out["Stochastic RSI"] = _grade(1 - v, "Oversold" if v < 0.2 else "Overbought" if v > 0.8 else "Balanced", "Overbought (80)", "Oversold (20)")
    if pd.notna(row["mfi"]):
        v = row["mfi"] / 100
        out["Money flow (MFI)"] = _grade(1 - v, "Oversold" if v < 0.2 else "Overbought" if v > 0.8 else "Balanced", "Overbought (80)", "Oversold (20)")
    if pd.notna(row["clv"]):
        v = (row["clv"] + 1) / 2
        out["Where it closed"] = _grade(1 - v, "Near the low" if v < 0.2 else "Near the high" if v > 0.8 else "Mid-range", "Day's high", "Day's low")
    if pd.notna(row["ret1"]):
        r1 = row["ret1"]
        out["Yesterday's move"] = _grade(0.5 - r1 / 0.06, "Big fall" if r1 < -0.015 else "Big rise" if r1 > 0.015 else "Small move", "Big rise", "Big fall")
    if pd.notna(row["rsi"]):
        r = row["rsi"]
        out["RSI (speed)"] = _grade(1 - r / 100, "Oversold" if r <= 30 else "Overbought" if r >= 70 else "Balanced", "Overbought (70)", "Oversold (30)")
    if pd.notna(row["macd_hist"]):
        gap = row["macd_hist"] / c * 100
        word = "Rising" if gap > 0 else "Falling"
        pos = 0.5 + gap / 2.0
        out["MACD (momentum)"] = _grade(pos, f"Slightly {word.lower()}" if abs(_clip(pos) - 0.5) < 0.1 else word, "Falling", "Rising")
    if pd.notna(row["adx"]) and (row["pdi"] + row["mdi"]):
        lean = row["pdi"] / (row["pdi"] + row["mdi"])
        out["Trend strength (ADX)"] = _grade(lean, "Buyers lead" if lean > 0.5 else "Sellers lead", "Sellers", "Buyers")
    out["Supertrend"] = _grade(0.85 if row["supertrend"] > 0 else 0.15, "Uptrend" if row["supertrend"] > 0 else "Downtrend", "Downtrend", "Uptrend")
    if pd.notna(row["cloud_top"]):
        w = 1 if c > row["cloud_top"] else -1 if c < row["cloud_bot"] else 0
        out["Ichimoku cloud"] = _grade(0.5 + w * 0.35, "Above the cloud" if w > 0 else "Below the cloud" if w < 0 else "Inside the cloud", "Below", "Above")
    if pd.notna(row["vol_ratio"]) and pd.notna(row["mom5"]):
        vr, m = row["vol_ratio"], row["mom5"]
        push = float(np.sign(m)) * float(np.log2(max(vr, 1e-6))) if abs(m) > 0.01 else 0.0     # busy trading behind a rise or a fall
        busy = vr >= ind.VOLUME_STRONG and abs(m) > 0.01
        out["Volume"] = _grade(0.5 + max(-1.0, min(1.0, push)) / 2, ("Busy buying" if m > 0 else "Busy selling") if busy else "Normal",
                               "Busy selling", "Busy buying")
    if pd.notna(row["zscore"]):
        z = row["zscore"]
        out["Z-score"] = _grade(0.5 - z / 6, "Stretched high" if z > 2 else "Stretched low" if z < -2 else "Normal", "Stretched high", "Stretched low")
    if pd.notna(row["daily_vol"]):
        vol = row["daily_vol"] * np.sqrt(252) * 100
        out["Volatility"] = _grade(1 - _clip((vol - 10) / 40), "Calm" if vol < 20 else "Moderate" if vol < 35 else "High", "Very bumpy", "Calm")
    return out


def votes(row, scales=False):
    """A list of dicts, one per indicator, from one day's row. Keys: name, voting (does it count towards the call?), vote
    (+1 Up, -1 Down, 0 Neutral), reading (a few words), why (a short reason) and gauge (a 0 to 1 position for the picture).

    The six VOTING indicators were chosen because they held up when tested on about 200,000 company-days of past NSE data;
    the others are shown for context only (tested, and did not help next-day accuracy). An indicator with no data is left out."""
    out = []
    c = row["close"]
    real = key_signal_gauges(row) if scales else {}
    # ---- the six that vote ----
    s50, s200 = row["sma50"], row["sma200"]
    if pd.notna(s50):
        up = c > s50 > s200 if pd.notna(s200) else c > s50
        down = c < s50 < s200 if pd.notna(s200) else c < s50
        gap = (c / s50 - 1) * 100
        out.append(_entry("Trend", True, 1 if up else -1 if down else 0,
                          "Rising" if up else "Falling" if down else "Mixed",
                          "Above both averages: steady climb" if up else "Below both averages: steady slide" if down else "Between its averages",
                          _gauge(0.5 + gap / 20, f"{gap:+.1f}% vs 50-day", "Below average", "Above average")))
    if pd.notna(row["bb_up"]) and row["bb_up"] > row["bb_lo"]:
        pct_b = (c - row["bb_lo"]) / (row["bb_up"] - row["bb_lo"])
        vote = -1 if c >= row["bb_up"] else 1 if c <= row["bb_lo"] else 0
        out.append(_entry("Bollinger band", True, vote, "Stretched high" if vote < 0 else "Stretched low" if vote > 0 else "Inside range",
                          "Far above its usual range; tends to drift back" if vote < 0 else "Far below its usual range; tends to bounce" if vote > 0
                          else "Nothing stretched", _gauge(pct_b, "Top of range" if pct_b > 0.8 else "Bottom of range" if pct_b < 0.2 else "Middle", "Bottom of range", "Top of range")))
    if pd.notna(row["stochrsi"]):
        v = row["stochrsi"]
        vote = 1 if v < 0.2 else -1 if v > 0.8 else 0
        out.append(_entry("Stochastic RSI", True, vote, "Oversold" if vote > 0 else "Overbought" if vote < 0 else "Balanced",
                          "Pushed to a short-term low; often snaps back" if vote > 0 else "Pushed to a short-term high; often cools" if vote < 0 else "No extreme",
                          _gauge(v, f"{v * 100:.0f} of 100", "Oversold", "Overbought")))
    if pd.notna(row["mfi"]):
        v = row["mfi"]
        vote = 1 if v < 20 else -1 if v > 80 else 0
        out.append(_entry("Money flow (MFI)", True, vote, "Drained" if vote > 0 else "Crowded" if vote < 0 else "Normal",
                          "Heavy selling has run its course" if vote > 0 else "Heavy buying may be exhausted" if vote < 0 else "Money in and out is balanced",
                          _gauge(v / 100, f"{v:.0f} of 100", "Money leaving", "Money entering")))
    if pd.notna(row["clv"]):
        v = row["clv"]
        vote = 1 if v < -0.6 else -1 if v > 0.6 else 0
        out.append(_entry("Where it closed", True, vote, "Near the day's low" if vote > 0 else "Near the day's high" if vote < 0 else "Mid-range",
                          "Closing at the low often sees a bounce" if vote > 0 else "Closing at the high often sees a pause" if vote < 0 else "Closed away from the extremes",
                          _gauge((v + 1) / 2, "Day's low" if v < -0.2 else "Day's high" if v > 0.2 else "Middle", "Day's low", "Day's high")))
    if pd.notna(row["ret1"]):
        r1 = row["ret1"]
        vote = 1 if r1 < -0.015 else -1 if r1 > 0.015 else 0
        out.append(_entry("Yesterday's move", True, vote, f"{r1 * 100:+.1f}%",
                          "A sharp fall is often followed by a rebound" if vote > 0 else "A sharp jump is often followed by a pullback" if vote < 0 else "No big move to react to",
                          _gauge(0.5 + r1 / 0.06, f"{r1 * 100:+.1f}%", "Big fall", "Big rise")))
    # ---- shown for context, not counted ----
    if pd.notna(row["rsi"]):
        r = row["rsi"]
        out.append(_entry("RSI (speed)", False, -1 if r >= 70 else 1 if r <= 30 else 0, f"{r:.0f}", "Speed of recent moves",
                          _gauge(r / 100, f"{r:.0f} of 100", "Oversold (30)", "Overbought (70)")))
    if pd.notna(row["macd_hist"]):
        h = row["macd_hist"]
        out.append(_entry("MACD (momentum)", False, 1 if h > 0 else -1, "Rising" if h > 0 else "Fading", "Short-term vs longer-term momentum",
                          _gauge(0.5 + h / c * 40, "Above signal" if h > 0 else "Below signal", "Fading", "Rising")))
    if pd.notna(row["adx"]):
        total = row["pdi"] + row["mdi"]
        lean = row["pdi"] / total if total else 0.5
        out.append(_entry("Trend strength (ADX)", False, (1 if lean > 0.5 else -1) if row["adx"] > 20 else 0,
                          f"Strength {row['adx']:.0f}", "Above 20 means a real trend, either way",
                          _gauge(lean, "Buyers lead" if lean > 0.5 else "Sellers lead", "Sellers", "Buyers")))
    out.append(_entry("Supertrend", False, int(row["supertrend"]), "Up" if row["supertrend"] > 0 else "Down", "A trailing line that flips on a reversal",
                      _gauge(0.85 if row["supertrend"] > 0 else 0.15, "Price above the line" if row["supertrend"] > 0 else "Price below the line", "Down", "Up")))
    if pd.notna(row["cloud_top"]):
        where = 1 if c > row["cloud_top"] else -1 if c < row["cloud_bot"] else 0
        out.append(_entry("Ichimoku cloud", False, where, "Above the cloud" if where > 0 else "Below the cloud" if where < 0 else "Inside the cloud",
                          "Price against its support and resistance cloud", _gauge(0.5 + where * 0.35, "Above" if where > 0 else "Below" if where < 0 else "Inside", "Below", "Above")))
    if pd.notna(row["vol_ratio"]) and pd.notna(row["mom5"]):
        vr, m = row["vol_ratio"], row["mom5"]
        vote = 1 if vr >= ind.VOLUME_STRONG and m > 0.01 else -1 if vr >= ind.VOLUME_STRONG and m < -0.01 else 0
        out.append(_entry("Volume", False, vote, f"{vr:.1f}x usual", "Busy trading makes a move more believable",
                          _gauge(0.5 + (vr - 1) / 2, "Busy" if vr >= 1.15 else "Thin" if vr <= 0.85 else "Normal", "Thin", "Busy")))
    return _with_real_gauges(out, real, row) if scales else out


def call_from(vote_list):
    """(prediction, score, number of voting indicators). Only the voting indicators count."""
    voters = [v for v in vote_list if v["voting"]]
    score = sum(v["vote"] for v in voters)
    prediction = UP if score >= VOTE_UP else DOWN if score <= VOTE_DOWN else SIDEWAYS
    return prediction, score, len(voters)


def flat_band(daily_vol):
    """A move smaller than this (a third of a typical day's swing) counts as 'sideways'."""
    return max(0.0015, 0.35 * (daily_vol if daily_vol == daily_vol else 0.01))


def direction_of(change, daily_vol):
    band = flat_band(daily_vol)
    return UP if change > band else DOWN if change < -band else SIDEWAYS


# ---------------- which day is 'today'? ----------------
def plan(hist, now, live_price=None, market_open=False):
    """Decide what to predict and what to compare it with.

    Returns {"basis": history up to the day BEFORE the target day, "target": date, "actual": price or None,
             "status": "pending" | "live" | "final", "note": text, "complete": history of finished days}.
    pending - the market has not opened yet today, final - the day is over, live - the market is open now.
    On a weekend or holiday the last finished session is used as the day to check, and the note says so.
    """
    today, last = now.date(), hist.index[-1].date()
    if last == today:
        actual = live_price if (live_price and market_open) else float(hist["Close"].iloc[-1])
        return {"basis": hist.iloc[:-1], "target": today, "actual": actual, "status": "live" if market_open else "final",
                "note": "", "complete": hist.iloc[:-1] if market_open else hist}
    if now.weekday() < 5:
        if market_open:
            return {"basis": hist, "target": today, "actual": live_price, "status": "live", "note": "", "complete": hist}
        if now.time() < dtime(9, 15):
            return {"basis": hist, "target": today, "actual": None, "status": "pending",
                    "note": "The market has not opened yet today, so there is nothing to compare with yet.", "complete": hist}
        return {"basis": hist, "target": today, "actual": live_price, "status": "final" if live_price else "pending",
                "note": "The market is shut and no price for today is available yet (a holiday, or the data is late).",
                "complete": hist}
    return {"basis": hist.iloc[:-1], "target": last, "actual": float(hist["Close"].iloc[-1]), "status": "final",
            "note": "The market is closed today, so this checks the last trading day.", "complete": hist}


def evaluate(basis, plan_info, scales=False):
    """The whole check for one company. Returns None if there is not enough history.

    Keys: prediction, score, n, votes, prev_close, basis_date, range (low, high), actual, change, actual_direction,
    matched, in_range, status, target, note.
    """
    basis = basis[basis["Close"].notna()]
    if len(basis) < 60:
        return None
    frame = indicator_frame(basis)
    row = frame.iloc[-1]
    vote_list = votes(row, scales)
    prediction, score, n = call_from(vote_list)
    prev_close = float(row["close"])
    vol = float(row["daily_vol"]) if pd.notna(row["daily_vol"]) else 0.015
    out = {"prediction": prediction, "score": score, "n": n, "votes": vote_list, "prev_close": prev_close,
           "basis_date": basis.index[-1].date(), "range": (prev_close * (1 - vol), prev_close * (1 + vol)),
           "daily_vol": vol, "status": plan_info["status"], "target": plan_info["target"], "note": plan_info["note"],
           "actual": plan_info["actual"], "change": None, "actual_direction": None, "matched": None, "in_range": None}
    if plan_info["actual"]:
        out["change"] = plan_info["actual"] / prev_close - 1
        out["actual_direction"] = direction_of(out["change"], vol)
        out["matched"] = out["actual_direction"] == prediction
        out["in_range"] = out["range"][0] <= plan_info["actual"] <= out["range"][1]
    return out


# ---------------- how often has the rule been right? ----------------
def track_record(complete, days=60):
    """Replay the rule for each of the last `days` finished trading days, using only data up to the day before.

    Returns {"rows": [{date, predicted, actual, change, matched}], "n", "hits", "accuracy", "baseline"} where baseline is
    how often you would be right by always guessing the most common outcome (a no-skill yardstick), or None."""
    complete = complete[complete["Close"].notna()]
    if len(complete) < 80:
        return None
    frame = indicator_frame(complete)
    closes = frame["close"]
    rows = []
    for k in range(max(60, len(frame) - days), len(frame)):
        prev = frame.iloc[k - 1]
        prediction, _, _ = call_from(votes(prev))
        change = float(closes.iloc[k] / closes.iloc[k - 1] - 1)
        vol = float(prev["daily_vol"]) if pd.notna(prev["daily_vol"]) else 0.015
        actual = direction_of(change, vol)
        rows.append({"date": frame.index[k].date(), "predicted": prediction, "actual": actual, "change": change,
                     "matched": prediction == actual})
    if not rows:
        return None
    hits = sum(r["matched"] for r in rows)
    counts = pd.Series([r["actual"] for r in rows]).value_counts()
    # "clear calls": days the rule said Up or Down and the day really moved (not sideways). A coin toss gets 50%.
    clear = [r for r in rows if r["predicted"] != SIDEWAYS and r["actual"] != SIDEWAYS]
    call_hits = sum(r["matched"] for r in clear)
    ups = sum(1 for r in clear if r["actual"] == UP)
    return {"rows": rows, "n": len(rows), "hits": hits, "accuracy": hits / len(rows), "baseline": float(counts.iloc[0] / len(rows)),
            "call_n": len(clear), "call_hits": call_hits, "call_accuracy": call_hits / len(clear) if clear else None,
            "call_baseline": max(ups, len(clear) - ups) / len(clear) if clear else None}


# ---------------- words ----------------
def headline(result):
    """One plain sentence: what was predicted and how it is going."""
    p = result["prediction"]
    word = {"Up": "rise", "Down": "fall", "Sideways": "go roughly sideways"}[p]
    base = f"Going by data up to {result['basis_date']:%d %b}, the indicators leaned towards the price to {word}"
    if result["actual"] is None:
        return base + ". Today's price is not available yet to compare."
    way = {"Up": "up", "Down": "down", "Sideways": "about flat"}[result["actual_direction"]]
    tail = "so far today" if result["status"] == "live" else "on the day"
    verdict = "That matches." if result["matched"] else "That does not match."
    return f"{base}. The price is {way} ({result['change'] * 100:+.2f}%) {tail}. {verdict}"
