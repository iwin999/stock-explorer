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
def indicator_frame(hist):
    """One row per day: the indicator values known at the END of that day (so a row can be used to predict the next day)."""
    close = hist["Close"].astype(float)
    line, sig, histo = ind.macd(close)
    mid, upper, lower = ind.bollinger(close)
    frame = pd.DataFrame({"close": close, "sma50": ind.sma(close, 50), "sma200": ind.sma(close, 200), "rsi": ind.rsi(close),
                          "macd_hist": histo, "bb_up": upper, "bb_lo": lower, "mom5": close / close.shift(5) - 1})
    frame["daily_vol"] = close.pct_change().rolling(60, min_periods=20).std()
    vol = ind.clean_volume(hist)
    if vol is not None:
        frame["vol_ratio"] = vol.rolling(5).mean() / vol.shift(5).rolling(20).mean()
    else:
        frame["vol_ratio"] = np.nan
    return frame


def votes(row):
    """[(indicator, reading, vote, why)] for one day's row. A vote is +1 (Up), -1 (Down) or 0 (Neutral).
    An indicator with no data is left out."""
    out = []
    c, s50, s200 = row["close"], row["sma50"], row["sma200"]
    if pd.notna(s50):
        if pd.isna(s200):
            up, down = c > s50, c < s50
        else:
            up, down = c > s50 > s200, c < s50 < s200
        if up:
            out.append(("Trend", "Price above its 50 and 200-day averages", 1, "A steady climb tends to continue more often than not."))
        elif down:
            out.append(("Trend", "Price below its 50 and 200-day averages", -1, "A steady slide tends to continue more often than not."))
        else:
            out.append(("Trend", "Price between its averages", 0, "No clear direction from the trend."))
    if pd.notna(row["rsi"]):
        r = row["rsi"]
        if r >= 70:
            out.append(("RSI (speed)", f"{r:.0f}, very high", -1, "A very fast rise often cools off, so this leans down."))
        elif r <= 30:
            out.append(("RSI (speed)", f"{r:.0f}, very low", 1, "A very fast fall often bounces, so this leans up."))
        else:
            out.append(("RSI (speed)", f"{r:.0f}, normal", 0, "The speed of recent moves is ordinary."))
    if pd.notna(row["macd_hist"]):
        h = row["macd_hist"]
        out.append(("MACD (momentum)", "Short-term momentum above its signal" if h > 0 else "Short-term momentum below its signal",
                    1 if h > 0 else -1, "Rising momentum leans up." if h > 0 else "Fading momentum leans down."))
    if pd.notna(row["bb_up"]):
        if c >= row["bb_up"]:
            out.append(("Bollinger band", "At or above the top of its usual range", -1, "Prices stretched this far often drift back."))
        elif c <= row["bb_lo"]:
            out.append(("Bollinger band", "At or below the bottom of its usual range", 1, "Prices stretched this far often drift back."))
        else:
            out.append(("Bollinger band", "Inside its usual range", 0, "Nothing stretched about the price."))
    if pd.notna(row["mom5"]):
        m = row["mom5"]
        if m > 0.01:
            out.append(("Last 5 days", f"Up {m * 100:.1f}%", 1, "Recent strength often carries on for a day or two."))
        elif m < -0.01:
            out.append(("Last 5 days", f"Down {abs(m) * 100:.1f}%", -1, "Recent weakness often carries on for a day or two."))
        else:
            out.append(("Last 5 days", f"Little change ({m * 100:+.1f}%)", 0, "No real move to follow."))
    if pd.notna(row["vol_ratio"]) and pd.notna(row["mom5"]):
        vr, m = row["vol_ratio"], row["mom5"]
        if vr >= ind.VOLUME_STRONG and m > 0.01:
            out.append(("Volume", "Busy trading behind the rise", 1, "A rise with many shares changing hands is more believable."))
        elif vr >= ind.VOLUME_STRONG and m < -0.01:
            out.append(("Volume", "Busy trading behind the fall", -1, "A fall with many shares changing hands is more believable."))
        else:
            out.append(("Volume", "Nothing special", 0, "Volume does not add to the picture."))
    return out


def call_from(vote_list):
    """(prediction, score, number of indicators). Prediction is 'Up', 'Down' or 'Sideways'."""
    score = sum(v for _, _, v, _ in vote_list)
    prediction = UP if score >= VOTE_UP else DOWN if score <= VOTE_DOWN else SIDEWAYS
    return prediction, score, len(vote_list)


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


def evaluate(basis, plan_info):
    """The whole check for one company. Returns None if there is not enough history.

    Keys: prediction, score, n, votes, prev_close, basis_date, range (low, high), actual, change, actual_direction,
    matched, in_range, status, target, note.
    """
    basis = basis[basis["Close"].notna()]
    if len(basis) < 60:
        return None
    frame = indicator_frame(basis)
    row = frame.iloc[-1]
    vote_list = votes(row)
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
    return {"rows": rows, "n": len(rows), "hits": hits, "accuracy": hits / len(rows), "baseline": float(counts.iloc[0] / len(rows))}


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
