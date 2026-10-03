"""Download price history for every company in our list and save it as local files.

Run this ONCE while you have internet (e.g. the evening before the exhibition):

    .venv/bin/python scripts/download_offline_data.py

It creates data/offline/<TICKER>.csv for each company. If the internet or Yahoo
fails during the exhibition, the app switches to these files automatically.
Run it again any time to refresh the backup.
"""
import json
import os
import sys
import time
from datetime import datetime

# Let this script import our project files from the folder above it.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.companies import BENCHMARK, COMPANIES  # noqa: E402
from core.market_data import OFFLINE_DIR, get_history, save_offline  # noqa: E402

PERIOD = "7y"      # same length the app asks for (5 years to test + 2 to warm up)
RETRIES = 3        # Yahoo sometimes says "no" once, then "yes"


def main():
    done, failed = [], []
    everything = COMPANIES + [("Nifty 50 index (benchmark)", BENCHMARK, "")]
    total = len(everything)
    for i, (name, symbol, _) in enumerate(everything, start=1):
        hist = None
        for attempt in range(RETRIES):
            hist = get_history(symbol, PERIOD)
            if hist is not None:
                break
            time.sleep(1.5 * (attempt + 1))  # wait a little longer each time
        if hist is None:
            failed.append(symbol)
            print(f"[{i:3}/{total}] FAILED  {symbol}  ({name})")
        else:
            save_offline(symbol, hist)
            done.append(symbol)
            print(f"[{i:3}/{total}] saved   {symbol:<16} {len(hist):5} days, last {hist.index[-1].date()}")

    manifest = {"downloaded_at": datetime.now().isoformat(timespec="seconds"),
                "period": PERIOD, "saved": done, "failed": failed}
    with open(os.path.join(OFFLINE_DIR, "_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nDone: {len(done)} saved, {len(failed)} failed. Files are in {OFFLINE_DIR}")
    if failed:
        print("Failed:", ", ".join(failed), "- run the script again to retry.")


if __name__ == "__main__":
    main()
