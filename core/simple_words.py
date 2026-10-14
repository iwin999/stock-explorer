"""Plain-words descriptions for the simple site. No Streamlit here, so they can be tested on their own."""
from core import companies
from core import indicators as ind
from core import universe

PERIODS = {"1 month": 21, "6 months": 126, "1 year": 252}


def verdict(hist):
    """[(heading, sentence, colour)] describing a company in everyday words. Colour is 'up', 'down' or 'flat'."""
    close = hist["Close"].dropna()
    out = []
    trend, _ = ind.describe_trend(close)
    if trend == "Uptrend":
        out.append(("Direction", "Climbing. The price has been rising steadily and is above its usual levels.", "up"))
    elif trend == "Downtrend":
        out.append(("Direction", "Falling. The price has been drifting down and is below its usual levels.", "down"))
    else:
        out.append(("Direction", "Sideways. The price is not going clearly up or down right now.", "flat"))

    vol = ind.annualised_volatility(close.iloc[-252:])
    if vol < 20:
        out.append(("How bumpy", "Calm. The price moves gently, which usually means fewer surprises.", "up"))
    elif vol < 35:
        out.append(("How bumpy", "A little bumpy. The price swings up and down fairly often.", "flat"))
    else:
        out.append(("How bumpy", "Very jumpy. The price can swing a lot in a short time, so it is riskier.", "down"))

    value = float(ind.rsi(close).iloc[-1])
    if value >= 70:
        out.append(("Recent speed", "It rose very fast lately. After a run like that prices often cool off.", "flat"))
    elif value <= 30:
        out.append(("Recent speed", "It fell very fast lately. After a drop like that prices sometimes bounce back.", "flat"))
    else:
        out.append(("Recent speed", "Moving at a normal speed. Nothing unusual in the last few weeks.", "flat"))

    year = close.iloc[-252:]
    high, low, now = float(year.max()), float(year.min()), float(year.iloc[-1])
    if high > low:
        place = (now - low) / (high - low)
        where = ("near the top of" if place >= 0.8 else "near the bottom of" if place <= 0.2 else "in the middle of")
        out.append(("Over the year", f"The price is {where} its range this year (from Rs {low:,.0f} to Rs {high:,.0f}).",
                    "flat"))
    return out


def move_words(change, pct):
    """'up Rs 12.30 (0.8%) today' / 'down ...' / 'unchanged today'."""
    if abs(pct) < 0.005:
        return "unchanged today", "flat"
    way = "up" if change > 0 else "down"
    return f"{way} Rs {abs(change):,.2f} ({abs(pct):.2f}%) today", ("up" if change > 0 else "down")


def gain_words(amount, pct):
    way = "gained" if amount >= 0 else "lost"
    return f"{way} Rs {abs(amount):,.0f} ({abs(pct):.1f}%)"


def resolve_search(value):
    """What to do with text typed in the search box: ('open', symbol) when it is clearly one company, ('list', symbols)
    when there are several close matches (best first), ('none', []) when nothing is close."""
    if value in universe.OPTIONS:
        return "open", value
    found = []                                      # the simple site shows one entry per company (the NSE listing)
    for sym in universe.rank(value, 12):
        nse = companies.to_nse(sym)
        if nse not in found:
            found.append(nse)
    found = found[:6]
    if len(found) == 1 or (found and universe.renamed(value)):
        return "open", found[0]
    return ("list", found) if found else ("none", [])
