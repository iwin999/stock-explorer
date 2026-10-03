"""Futures and options, priced with standard formulas.

IMPORTANT - be honest about this at the exhibition: Yahoo Finance has NO real NSE futures or
options prices. So here they are MODELLED from the live price of the underlying share or index:

  * Futures price  = spot x e^(r x time left)           ("cost of carry")
  * Option price   = Black-Scholes formula               (the classic option-pricing model)
  * Volatility used in the option formula is the stock's own last-year volatility.

These are fair-value estimates, not exchange quotes. Real prices also reflect demand, dividends
and traders' views. Lot sizes and margins are simplified for learning (see below).
"""
import calendar
import math
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import numpy as np

IST = ZoneInfo("Asia/Kolkata")
RISK_FREE = 0.065            # 6.5% a year, same assumption as the ratios
EXPIRY_TIME = time(15, 30)   # contracts expire at the market close
FUTURES_MARGIN = 0.15        # 15% of the contract value is blocked as margin (simplified)
CONTRACT_VALUE = 200000      # a lot is sized to be worth about Rs 2 lakh (the real exchange minimum is larger)

_NICE_LOTS = [1, 2, 3, 4, 5, 8, 10, 15, 20, 25, 30, 40, 50, 75, 100, 125, 150, 200, 250, 300, 400, 500,
              600, 750, 1000, 1500, 2000, 3000, 5000]


def lot_size(spot):
    """Units in one lot: a 'nice' number that makes a lot worth about Rs 2 lakh.

    The real exchange fixes lot sizes (and they change from time to time). This version keeps
    contracts affordable for practice accounts.
    """
    target = CONTRACT_VALUE / max(spot, 0.01)
    return min(_NICE_LOTS, key=lambda n: abs(math.log(n / target)))


def contract_value(spot, lots=1):
    return spot * lot_size(spot) * lots


# ---------------- expiries ----------------
def last_tuesday(year, month):
    """Monthly NSE contracts expire on the last Tuesday of the month."""
    last = date(year, month, calendar.monthrange(year, month)[1])
    return last - timedelta(days=(last.weekday() - 1) % 7)


def expiry_dates(now=None, count=3):
    """The next `count` monthly expiry dates that have not yet passed."""
    now = now or datetime.now(IST)
    out, year, month = [], now.year, now.month
    while len(out) < count:
        d = last_tuesday(year, month)
        if datetime.combine(d, EXPIRY_TIME, tzinfo=IST) > now:
            out.append(d)
        month += 1
        if month > 12:
            year, month = year + 1, 1
    return out


def years_left(expiry, now=None):
    """Time to expiry in years (never below a tiny positive number)."""
    now = now or datetime.now(IST)
    end = datetime.combine(expiry, EXPIRY_TIME, tzinfo=IST)
    return max((end - now).total_seconds() / (365 * 24 * 3600), 1e-6)


def has_expired(expiry, now=None):
    now = now or datetime.now(IST)
    return datetime.combine(expiry, EXPIRY_TIME, tzinfo=IST) <= now


# ---------------- prices ----------------
def future_price(spot, years, r=RISK_FREE):
    """Fair futures price: today's price grown at the safe rate until expiry."""
    return spot * math.exp(r * years)


def _norm_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def option_price(spot, strike, years, sigma, kind, r=RISK_FREE):
    """Black-Scholes price of one unit of a call or put (European, no dividends).

    kind: "CALL" or "PUT". At (or past) expiry this is just the intrinsic value.
    """
    if years <= 1e-5 or sigma <= 0:
        return max(spot - strike, 0.0) if kind == "CALL" else max(strike - spot, 0.0)
    d1 = (math.log(spot / strike) + (r + 0.5 * sigma**2) * years) / (sigma * math.sqrt(years))
    d2 = d1 - sigma * math.sqrt(years)
    if kind == "CALL":
        return spot * _norm_cdf(d1) - strike * math.exp(-r * years) * _norm_cdf(d2)
    return strike * math.exp(-r * years) * _norm_cdf(-d2) - spot * _norm_cdf(-d1)


def volatility_for_pricing(close):
    """The stock's last-year volatility, kept between 12% and 80% so prices stay sensible."""
    daily = np.log(close / close.shift(1)).dropna().iloc[-252:]
    return float(min(max(daily.std() * math.sqrt(252), 0.12), 0.80)) if len(daily) > 20 else 0.25


def strike_step(spot):
    """Gap between strikes, about 1% of the price, rounded to a tidy number."""
    steps = [1, 2.5, 5, 10, 20, 25, 50, 100, 200, 500]
    return min(steps, key=lambda s: abs(math.log(s / max(spot * 0.01, 0.5))))


def strike_grid(spot, count=8):
    """Strikes around the current price (the middle one is 'at the money')."""
    step = strike_step(spot)
    atm = round(spot / step) * step
    return [round(atm + i * step, 2) for i in range(-count, count + 1)], atm


def margin_for_future(spot_or_price, lots):
    return FUTURES_MARGIN * spot_or_price * lot_size(spot_or_price) * lots
