"""Download yearly company results for every company in our list and save them for the fusion analysis.

Run this occasionally while you have internet (about 3-5 minutes):

    .venv/bin/python scripts/download_fundamentals.py

It writes data/offline/fundamentals.json. Commit and push that file to update the online app.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import fundamentals as fd  # noqa: E402
from core.companies import COMPANIES  # noqa: E402


def main():
    records, failed = {}, []
    total = len(COMPANIES)
    for i, (name, symbol, _) in enumerate(COMPANIES, start=1):
        record = None
        for attempt in range(3):
            try:
                record = fd.fetch_company(symbol)
            except Exception as e:
                print(f"      retry {symbol}: {str(e)[:60]}")
            if record:
                break
            time.sleep(1.5 * (attempt + 1))
        if record:
            records[symbol] = record
            years = sorted(record["annual"])
            print(f"[{i:3}/{total}] saved   {symbol:<16} {len(years)} years ({years[0][:4]}-{years[-1][:4]}) {record['sector']}")
        else:
            failed.append(symbol)
            print(f"[{i:3}/{total}] FAILED  {symbol}  ({name})")
    fd.save(records)
    print(f"\nDone: {len(records)} companies saved, {len(failed)} failed -> {fd.PATH}")
    if failed:
        print("Failed:", ", ".join(failed))


if __name__ == "__main__":
    main()
