"""Download the list of NSE and BSE companies (name, ticker, industry) from Yahoo Finance's screener.

    .venv/bin/python scripts/download_company_universe.py

It pages through the screener for each industry on each exchange and saves data/offline/company_universe.json.
The app reads that file to suggest companies as you type in the search box. Run it again now and then to pick up
newly listed companies (it takes about a minute).
"""
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.market_carpet import EXCHANGES, SECTORS, pretty  # noqa: E402

PAGE = 250
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "offline", "company_universe.json")


def fetch(job):
    import yfinance as yf
    from yfinance import EquityQuery as Q
    sector, exchange = job
    query = Q("and", [Q("eq", ["region", "in"]), Q("eq", ["exchange", exchange]), Q("eq", ["sector", sector])])
    rows, offset = [], 0
    while True:
        for attempt in range(3):
            try:
                r = yf.screen(query, sortField="intradaymarketcap", sortAsc=False, size=PAGE, offset=offset)
                break
            except Exception:
                r = None
                time.sleep(1.5 * (attempt + 1))
        if not r or not r.get("quotes"):
            break
        for q in r["quotes"]:
            if q.get("symbol"):
                rows.append({"s": q["symbol"], "n": pretty(q.get("longName") or q.get("shortName") or q["symbol"]),
                             "x": EXCHANGES.get(q.get("exchange"), q.get("exchange")), "i": sector})
        offset += len(r["quotes"])
        if offset >= int(r.get("total") or 0):
            break
    return job, rows


def main():
    jobs = [(s, ex) for s in SECTORS for ex in EXCHANGES]
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(fetch, jobs))
    seen, companies = set(), []
    for job, rows in results:
        print(f"{job[0]:24} {EXCHANGES[job[1]]}: {len(rows)}")
        for r in rows:
            if r["s"] not in seen:
                seen.add(r["s"])
                companies.append(r)
    companies.sort(key=lambda r: r["n"].lower())
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(companies, f, separators=(",", ":"))
    print(f"\nSaved {len(companies)} companies to {OUT}")


if __name__ == "__main__":
    main()
