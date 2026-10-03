"""Yahoo Finance symbol search, limited to NSE (.NS) and BSE (.BO) stocks.

Carried over from the senior's app. In the finished project this is the
FALLBACK: we look in our own list of ~100 popular companies first.
"""
import logging

import requests

log = logging.getLogger(__name__)

SEARCH_URL = "https://query1.finance.yahoo.com/v1/finance/search"
SEARCH_LIMIT = 20


def yahoo_search(query):
    """Return [{'symbol': 'RELIANCE.NS', 'name': 'Reliance Industries Limited'}, ...].

    Returns an empty list (never raises) if the network is down.
    """
    query = query.strip()
    if len(query) < 2:
        return []
    try:
        resp = requests.get(
            SEARCH_URL,
            params={"q": query},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        resp.raise_for_status()
        quotes = resp.json().get("quotes", [])[:SEARCH_LIMIT]
    except Exception:
        log.exception("Yahoo search failed for %r", query)
        return []

    results = []
    for q in quotes:
        symbol = q.get("symbol", "")
        # The senior dropped any result with no long name. We accept the short
        # name too, and finally the ticker, so good matches aren't hidden.
        name = q.get("longname") or q.get("shortname") or symbol
        if symbol.endswith((".NS", ".BO")):
            results.append({"symbol": symbol, "name": name})
    return results
