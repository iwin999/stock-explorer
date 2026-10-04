"""Yearly company results (revenue, profit, equity, debt ...) saved as a file that ships with the app.

Source: Yahoo Finance's yearly statements (about 4-5 years per company). They are fetched by
scripts/download_fundamentals.py and stored in data/offline/fundamentals.json, so the app never needs the
internet to run the fusion analysis.

Each company's record looks like:
    {"sector": "Energy", "financial": False,
     "annual": {"2025-03-31": {"revenue": ..., "operating_income": ..., "net_income": ..., "eps": ...,
                               "equity": ..., "debt": ..., "shares": ...}, ...}}
"""
import json
import logging
import os
from datetime import datetime

log = logging.getLogger(__name__)

PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "offline", "fundamentals.json")

# our name -> the row names Yahoo may use (first one found wins)
ROWS = {
    "revenue": ["Total Revenue", "Operating Revenue"],
    "operating_income": ["Operating Income", "Total Operating Income As Reported"],
    "net_income": ["Net Income", "Net Income Common Stockholders"],
    "eps": ["Diluted EPS", "Basic EPS"],
    "equity": ["Stockholders Equity", "Common Stock Equity", "Total Equity Gross Minority Interest"],
    "debt": ["Total Debt"],
    "shares": ["Ordinary Shares Number", "Share Issued"],
}


def _pick(frame, names, column):
    for name in names:
        if name in frame.index:
            value = frame.at[name, column]
            if value == value and value is not None:      # skip NaN
                return float(value)
    return None


def fetch_company(symbol):
    """Download one company's yearly results. Returns the record described above, or None if nothing was found."""
    import yfinance as yf

    ticker = yf.Ticker(symbol)
    income, balance = ticker.income_stmt, ticker.balance_sheet
    if income is None or income.empty:
        return None
    annual = {}
    for column in income.columns:
        row = {key: _pick(income, ROWS[key], column) for key in ("revenue", "operating_income", "net_income", "eps")}
        if balance is not None and column in balance.columns:
            row.update({key: _pick(balance, ROWS[key], column) for key in ("equity", "debt", "shares")})
        if row.get("revenue") is not None or row.get("net_income") is not None:
            annual[column.strftime("%Y-%m-%d")] = row
    if not annual:
        return None
    try:
        sector = ticker.info.get("sector") or ""
    except Exception:
        sector = ""
    return {"sector": sector, "financial": sector == "Financial Services", "annual": annual}


def save(records, path=PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = {"downloaded_at": datetime.now().isoformat(timespec="seconds"), "source": "Yahoo Finance yearly statements",
               "companies": records}
    with open(path, "w") as f:
        json.dump(payload, f)


def load(path=PATH):
    """{'downloaded_at', 'companies': {symbol: record}} or an empty structure if the file is missing."""
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"downloaded_at": None, "source": None, "companies": {}}
