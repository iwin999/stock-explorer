"""How each thing you hold is doing, and how much it matters to the whole portfolio.

No screen code here (see core/holdings_ui.py). For every holding we work out:
  * Weight        - its share of the total portfolio value (cash counts as part of the total)
  * Contribution  - how many percentage points it added to (or took off) your total return:
                    its profit or loss divided by the money you started with
  * Today         - today's move in the price, when a live quote is available
  * Days held     - since your first purchase
"""
from datetime import datetime

from core.trading import IST

import pandas as pd


def first_buy_dates(pf):
    """{symbol: datetime of the first BUY} from the order history."""
    dates = {}
    for order in pf.order_history:
        sym = order.get("symbol", "")
        if order.get("type") == "BUY" and sym not in dates:
            try:
                dates[sym] = datetime.fromisoformat(order["timestamp"])
            except (KeyError, ValueError):
                pass
    return dates


def analyse(pf, snap, quote_fn=None, now=None):
    """One row per position: the snapshot's rows plus Weight %, Contribution (points), Today % and Days held."""
    table = snap["positions"]
    if table.empty:
        return table
    now = now or datetime.now(IST).replace(tzinfo=None)             # order times are stored in Indian time
    total = snap["total"] or 1.0
    deposited = pf.deposited or 1.0
    bought = first_buy_dates(pf)
    out = table.copy()
    out["Weight %"] = out["Value"] / total * 100
    out["Contribution"] = out["P&L"] / deposited * 100
    today, days = [], []
    for _, row in out.iterrows():
        sym = row["Symbol"]
        move = None
        if quote_fn is not None and row["Class"] != "Futures" and row["Class"] != "Options":
            q = quote_fn(sym)
            if q and q.get("previous_close"):
                move = (q["price"] / q["previous_close"] - 1) * 100
        today.append(move)
        first = bought.get(sym) if row["Class"] not in ("Futures", "Options") else None
        days.append((now - first).days if first else None)
    out["Today %"] = today
    out["Days held"] = days
    return out.sort_values("Value", ascending=False).reset_index(drop=True)


def verdict(row):
    """One plain sentence about a holding."""
    pnl, weight, contrib = row["P&L %"], row["Weight %"], row["Contribution"]
    if abs(pnl) < 0.05:
        mood = "is about where you bought it"
    else:
        mood = f"is {'up' if pnl > 0 else 'down'} {abs(pnl):.1f}% since you bought it"
    size = "a big part" if weight >= 25 else "a medium part" if weight >= 10 else "a small part"
    effect = (f"it has added {contrib:+.2f} points to your total return" if contrib >= 0
              else f"it has taken {abs(contrib):.2f} points off your total return")
    return f"{row['Instrument']} {mood}. It is {size} of your portfolio ({weight:.0f}%), and {effect}."


def biggest_effects(df, n=1):
    """(best, worst) holdings by contribution, or None if there are fewer than two."""
    if df.empty or len(df) < 2:
        return None
    ranked = df.sort_values("Contribution")
    return ranked.iloc[-n], ranked.iloc[0]
