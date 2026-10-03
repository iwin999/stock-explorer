"""Portfolio builder: turn "I want 40% stocks, 20% bonds ..." into actual orders.

Pure maths (no screen, no internet) so it can be tested. The screen collects the choices and the
prices; this file works out how many shares / lots each choice buys and what is left over.

Rules (kept simple on purpose):
  * Each asset class gets its percentage of the CASH available.
  * That money is split equally between the instruments chosen in the class.
  * Shares / ETFs / bonds: buy as many whole units as the share of money allows.
  * Futures: the money pays the MARGIN; as many whole lots as it covers (nearest expiry).
  * Options: the money pays the PREMIUM of an at-the-money option (nearest expiry).
  * Whatever cannot be bought in whole units stays as cash.
"""
import math
from datetime import datetime

from core import derivatives as dv
from core import instruments as ins

BUILDER_CLASSES = [ins.STOCKS, ins.ETFS, ins.BONDS, ins.FUTURES, ins.OPTIONS]


def plan_portfolio(cash, alloc, picks, prices, sigmas, now=None):
    """Work out the orders.

    cash    - money available to invest
    alloc   - {asset class: percent of cash}, e.g. {"Stocks": 40, "Bonds": 20, ...} (the rest stays cash)
    picks   - {"Stocks": [symbols], "ETFs (equity, gold, silver)": [symbols], "Bonds": [symbols],
               "Futures": [(underlying, "LONG"/"SHORT")], "Options": [(underlying, "CALL"/"PUT")]}
    prices  - {symbol: latest price};  sigmas - {symbol: volatility} (needed for options)
    Returns {"orders": [...], "skipped": [...], "spent": x, "left": y}.
    """
    now = now or datetime.now(dv.IST)
    expiry = dv.expiry_dates(now, 1)[0]
    years = dv.years_left(expiry, now)
    orders, skipped = [], []

    for cls in BUILDER_CLASSES:
        pct = alloc.get(cls, 0)
        chosen = picks.get(cls, [])
        if pct <= 0:
            continue
        if not chosen:
            skipped.append(f"{cls}: {pct}% was set aside, but no instrument was chosen, so it stays as cash.")
            continue
        budget = cash * pct / 100.0 / len(chosen)

        for item in chosen:
            symbol = item[0] if isinstance(item, tuple) else item
            spot = prices.get(symbol)
            name = ins.name_of(symbol)
            if not spot:
                skipped.append(f"{name}: no price is available right now.")
                continue

            if cls in (ins.STOCKS, ins.ETFS, ins.BONDS):
                qty = math.floor(budget / spot)
                if qty < 1:
                    skipped.append(f"{name}: {budget:,.0f} is not enough for one unit at {spot:,.2f}.")
                    continue
                orders.append({"class": cls, "kind": "CASH", "symbol": symbol, "label": name, "qty": qty,
                               "price": spot, "cost": qty * spot, "detail": f"{qty} units"})

            elif cls == ins.FUTURES:
                side = item[1]
                price = dv.future_price(spot, years)
                lot = dv.lot_size(spot)
                margin_lot = dv.FUTURES_MARGIN * price * lot
                lots = math.floor(budget / margin_lot)
                if lots < 1:
                    skipped.append(f"{name} future: {budget:,.0f} does not cover the margin for one lot ({margin_lot:,.0f}).")
                    continue
                orders.append({"class": cls, "kind": "FUT", "symbol": symbol, "label": f"{name} future ({side.lower()})",
                               "qty": lots, "price": price, "cost": lots * margin_lot, "side": side, "lot": lot,
                               "expiry": expiry, "detail": f"{lots} lot(s) x {lot}, expires {expiry:%d %b}"})

            else:  # options
                kind = item[1]
                _, atm = dv.strike_grid(spot)
                sigma = sigmas.get(symbol) or 0.25
                premium = dv.option_price(spot, atm, years, sigma, kind)
                lot = dv.lot_size(spot)
                cost_lot = premium * lot
                lots = math.floor(budget / cost_lot) if cost_lot > 0 else 0
                if lots < 1:
                    skipped.append(f"{name} option: {budget:,.0f} does not cover one lot ({cost_lot:,.0f}).")
                    continue
                orders.append({"class": cls, "kind": "OPT", "symbol": symbol,
                               "label": f"{name} {atm:g} {kind.lower()}", "qty": lots, "price": premium,
                               "cost": lots * cost_lot, "strike": atm, "option_kind": kind, "lot": lot,
                               "expiry": expiry, "detail": f"{lots} lot(s) x {lot}, expires {expiry:%d %b}"})

    spent = sum(o["cost"] for o in orders)
    return {"orders": orders, "skipped": skipped, "spent": spent, "left": cash - spent}


def execute_plan(pf, plan):
    """Place every planned order on the account. Returns how many were placed."""
    placed = 0
    for o in plan["orders"]:
        if o["kind"] == "CASH":
            pf.buy(o["symbol"], o["qty"], o["price"])
        elif o["kind"] == "FUT":
            pf.open_future(o["symbol"], o["expiry"], o["side"], o["qty"], o["price"], o["lot"], dv.FUTURES_MARGIN)
        else:
            pf.buy_option(o["symbol"], o["expiry"], o["strike"], o["option_kind"], o["qty"], o["price"], o["lot"])
        placed += 1
    return placed
