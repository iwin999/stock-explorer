"""Every NSE and BSE company, for the search box that suggests companies as you type.

The list lives in data/offline/company_universe.json (made by scripts/download_company_universe.py from Yahoo
Finance's screener). The popular companies we know best come first; everything else follows in name order.
"""
import json
import os

from core import companies

PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "offline", "company_universe.json")


def _load():
    try:
        with open(PATH) as f:
            return json.load(f)                         # [{"s": symbol, "n": name, "x": exchange, "i": industry}, ...]
    except (OSError, ValueError):
        return []


ROWS = _load()
for _r in ROWS:
    companies.NAME_BY_SYMBOL.setdefault(_r["s"], _r["n"])    # so every company shows its name in dropdowns, trades and holdings


def _options():
    popular = [x for _, s, _ in companies.COMPANIES for x in companies.listings(s)]
    seen = set(popular)
    rest = [r["s"] for r in ROWS if r["s"] not in seen]
    return popular + rest


OPTIONS = _options()
INDUSTRY_OF = {r["s"]: r["i"] for r in ROWS}
