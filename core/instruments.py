"""What can be bought in the paper-trading accounts.

Cash-market instruments (bought and sold like shares, live Yahoo prices):
  * Stocks              - the 119 companies in core/companies.py
  * Equity ETFs         - baskets that follow an index
  * Gold and silver ETFs
  * Bonds               - government / PSU bond ETFs and liquid ETFs (real NSE-traded funds)

Futures and options use these underlyings (see core/derivatives.py for how they are priced).
"""
from core.companies import COMPANIES, NAME_BY_SYMBOL

# asset classes shown to visitors
STOCKS, ETFS, BONDS, FUTURES, OPTIONS, CASH = (
    "Stocks", "ETFs (equity, gold, silver)", "Bonds", "Futures", "Options", "Cash")
CLASS_ORDER = [STOCKS, ETFS, BONDS, FUTURES, OPTIONS, CASH]

# (symbol, name, class, group shown in the picker)
_ETF_ROWS = [
    ("NIFTYBEES.NS", "Nifty 50 ETF (Nippon India Nifty BeES)", ETFS, "Equity ETF"),
    ("BANKBEES.NS", "Nifty Bank ETF (Nippon India Bank BeES)", ETFS, "Equity ETF"),
    ("JUNIORBEES.NS", "Nifty Next 50 ETF (Nippon India Junior BeES)", ETFS, "Equity ETF"),
    ("ITBEES.NS", "Nifty IT ETF (Nippon India)", ETFS, "Equity ETF"),
    ("PSUBNKBEES.NS", "PSU Bank ETF (Nippon India)", ETFS, "Equity ETF"),
    ("CPSEETF.NS", "CPSE ETF (public sector companies)", ETFS, "Equity ETF"),
    ("MON100.NS", "Nasdaq 100 ETF (Motilal Oswal)", ETFS, "International ETF"),
    ("MAFANG.NS", "NYSE FANG+ ETF (Mirae Asset)", ETFS, "International ETF"),
    ("GOLDBEES.NS", "Gold ETF (Nippon India Gold BeES)", ETFS, "Gold and silver"),
    ("HDFCGOLD.NS", "Gold ETF (HDFC)", ETFS, "Gold and silver"),
    ("BSLGOLDETF.NS", "Gold ETF (Aditya Birla Sun Life)", ETFS, "Gold and silver"),
    ("SILVERBEES.NS", "Silver ETF (Nippon India)", ETFS, "Gold and silver"),
    ("EBBETF0430.NS", "Bharat Bond ETF, April 2030", BONDS, "Government / PSU bonds"),
    ("EBBETF0431.NS", "Bharat Bond ETF, April 2031", BONDS, "Government / PSU bonds"),
    ("BBETF0432.NS", "Bharat Bond ETF, April 2032", BONDS, "Government / PSU bonds"),
    ("GILT5YBEES.NS", "5-year G-Sec ETF (Nippon India)", BONDS, "Government / PSU bonds"),
    ("LICNETFGSC.NS", "Long-term G-Sec ETF (LIC MF)", BONDS, "Government / PSU bonds"),
    ("LIQUIDBEES.NS", "Liquid ETF (Nippon India Liquid BeES)", BONDS, "Liquid (cash-like)"),
    ("LIQUIDCASE.NS", "Liquid ETF (Zerodha Nifty Liquid)", BONDS, "Liquid (cash-like)"),
]

ETF_LIST = [(sym, name, cls, group) for sym, name, cls, group in _ETF_ROWS]
CASH_INSTRUMENTS = {}                      # symbol -> {"name", "class", "group"}
for _name, _sym, _ in COMPANIES:
    CASH_INSTRUMENTS[_sym] = {"name": _name, "class": STOCKS, "group": "Stock"}
for _sym, _name, _cls, _group in _ETF_ROWS:
    CASH_INSTRUMENTS[_sym] = {"name": _name, "class": _cls, "group": _group}


def name_of(symbol):
    """Readable name for any instrument or index."""
    if symbol in CASH_INSTRUMENTS:
        return CASH_INSTRUMENTS[symbol]["name"]
    return {"^NSEI": "Nifty 50 index", "^NSEBANK": "Bank Nifty index"}.get(symbol, NAME_BY_SYMBOL.get(symbol, symbol))


def asset_class(symbol):
    """Which asset class a cash-market symbol belongs to (unknown symbols count as Stocks)."""
    return CASH_INSTRUMENTS.get(symbol, {"class": STOCKS})["class"]


def symbols_in_class(cls):
    return [s for s, v in CASH_INSTRUMENTS.items() if v["class"] == cls]


def label(symbol):
    """Dropdown text, e.g. 'Gold ETF (Nippon India Gold BeES) (GOLDBEES)'."""
    return f"{name_of(symbol)} ({symbol.replace('.NS', '')})"


# ---------------- futures and options underlyings ----------------
INDEX_UNDERLYINGS = ["^NSEI", "^NSEBANK"]
_STOCK_FNO = ["RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "SBIN", "BHARTIARTL", "ITC", "LT",
              "HINDUNILVR", "KOTAKBANK", "AXISBANK", "BAJFINANCE", "MARUTI", "SUNPHARMA", "M&M",
              "HCLTECH", "TATASTEEL", "TITAN", "WIPRO", "ASIANPAINT", "ONGC", "NTPC", "ADANIENT"]
FNO_UNDERLYINGS = INDEX_UNDERLYINGS + [s + ".NS" for s in _STOCK_FNO]

# every symbol the app may need prices for (used by the offline download script)
ALL_PRICED_SYMBOLS = list(dict.fromkeys(
    [s for _, s, _ in COMPANIES] + [r[0] for r in _ETF_ROWS] + INDEX_UNDERLYINGS))
