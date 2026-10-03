"""Valuing a whole account: shares, ETFs, bonds, futures, options and cash.

Prices are passed in as functions (spot_fn, sigma_fn, settle_fn) so this file contains only
the maths and can be tested without the internet.
"""
from datetime import date, datetime

import pandas as pd

from core import derivatives as dv
from core import instruments as ins


def mark_future(pos, spot, now=None):
    """Current price, value and profit/loss of a futures position."""
    years = dv.years_left(date.fromisoformat(pos["expiry"]), now)
    price = dv.future_price(spot, years)
    direction = 1 if pos["side"] == "LONG" else -1
    pnl = direction * (price - pos["entry"]) * pos["lot_size"] * pos["lots"]
    return {"price": price, "pnl": pnl, "value": max(pos["margin"] + pnl, 0.0)}


def mark_option(pos, spot, sigma, now=None):
    years = dv.years_left(date.fromisoformat(pos["expiry"]), now)
    price = dv.option_price(spot, pos["strike"], years, sigma, pos["kind"])
    units = pos["lot_size"] * pos["lots"]
    return {"price": price, "pnl": (price - pos["premium"]) * units, "value": price * units}


def snapshot(pf, spot_fn, sigma_fn, now=None):
    """Value everything the account holds.

    Returns {"total", "by_class", "positions" (DataFrame), "return_pct", "invested_pct"}.
    A missing price falls back to the price paid, so the row shows no profit rather than crashing.
    """
    now = now or datetime.now(dv.IST)
    rows = []
    by_class = {c: 0.0 for c in ins.CLASS_ORDER}
    by_class[ins.CASH] = pf.balance

    for sym, h in pf.holdings.items():
        cls = ins.asset_class(sym)
        price = spot_fn(sym) or h["avg_price"]
        value, cost = h["quantity"] * price, h["quantity"] * h["avg_price"]
        by_class[cls] += value
        rows.append({"Class": cls, "Instrument": ins.name_of(sym), "Details": f"{h['quantity']} units",
                     "Bought at": h["avg_price"], "Now": price, "Value": value, "P&L": value - cost,
                     "P&L %": (value - cost) / cost * 100 if cost else 0.0, "Symbol": sym})

    for pos in pf.derivatives:
        spot = spot_fn(pos["underlying"])
        under = ins.name_of(pos["underlying"])
        if pos["type"] == "FUT":
            m = mark_future(pos, spot, now) if spot else {"price": pos["entry"], "pnl": 0.0, "value": pos["margin"]}
            cost = pos["margin"]
            by_class[ins.FUTURES] += m["value"]
            detail = f"{pos['side']}, {pos['lots']} lot(s) x {pos['lot_size']}, exp {pos['expiry']}"
            rows.append({"Class": ins.FUTURES, "Instrument": f"{under} future", "Details": detail,
                         "Bought at": pos["entry"], "Now": m["price"], "Value": m["value"], "P&L": m["pnl"],
                         "P&L %": m["pnl"] / cost * 100 if cost else 0.0, "Symbol": pos["underlying"]})
        else:
            sigma = sigma_fn(pos["underlying"]) if spot else None
            m = mark_option(pos, spot, sigma, now) if spot and sigma else \
                {"price": pos["premium"], "pnl": 0.0, "value": pos["premium"] * pos["lot_size"] * pos["lots"]}
            cost = pos["premium"] * pos["lot_size"] * pos["lots"]
            by_class[ins.OPTIONS] += m["value"]
            detail = f"{pos['strike']:g} {pos['kind']}, {pos['lots']} lot(s) x {pos['lot_size']}, exp {pos['expiry']}"
            rows.append({"Class": ins.OPTIONS, "Instrument": f"{under} option", "Details": detail,
                         "Bought at": pos["premium"], "Now": m["price"], "Value": m["value"], "P&L": m["pnl"],
                         "P&L %": m["pnl"] / cost * 100 if cost else 0.0, "Symbol": pos["underlying"]})

    total = sum(by_class.values())
    return {
        "total": total,
        "by_class": by_class,
        "positions": pd.DataFrame(rows),
        "return_pct": (total / pf.deposited - 1) * 100 if pf.deposited else 0.0,
    }


def settle_and_square_off(pf, spot_fn, sigma_fn, settle_fn, now=None):
    """Housekeeping that real brokers do automatically. Returns a list of messages (empty if nothing happened).

    1. Contracts past their expiry are settled: futures at the closing price on expiry day, options at
       their intrinsic value (worthless if out of the money).
    2. A futures position whose losses have used up all its margin is closed automatically.

    settle_fn(underlying, expiry_date) gives the closing price on that date (or None if unknown).
    """
    now = now or datetime.now(dv.IST)
    events = []
    for pos in list(pf.derivatives):
        name = ins.name_of(pos["underlying"])
        expiry = date.fromisoformat(pos["expiry"])
        if dv.has_expired(expiry, now):
            price = settle_fn(pos["underlying"], expiry)
            if price is None:
                continue                                   # try again later, when the price is available
            if pos["type"] == "FUT":
                pnl = pf.close_future(pos["id"], price, reason="EXPIRED")
                events.append(f"{name} future expired on {expiry:%d %b}; settled at {price:,.2f} (profit/loss {pnl:+,.0f}).")
            else:
                intrinsic = max(price - pos["strike"], 0.0) if pos["kind"] == "CALL" else max(pos["strike"] - price, 0.0)
                pnl = pf.sell_option(pos["id"], intrinsic, reason="EXPIRED")
                events.append(f"{name} {pos['strike']:g} {pos['kind'].lower()} expired on {expiry:%d %b}; "
                              f"value {intrinsic:,.2f} per unit (profit/loss {pnl:+,.0f}).")
        elif pos["type"] == "FUT":
            spot = spot_fn(pos["underlying"])
            if spot and mark_future(pos, spot, now)["value"] <= 0:
                price = mark_future(pos, spot, now)["price"]
                pf.close_future(pos["id"], price, reason="LIQUIDATED")
                events.append(f"{name} future was closed automatically: losses used up the whole margin.")
    return events
