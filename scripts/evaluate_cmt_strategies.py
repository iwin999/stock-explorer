"""Back-test the five CMT strategies on every saved NSE company and write data/cmt_strategy_stats.json.

For each strategy: on the days it voted Up or Down, how often was the NEXT day's move in that direction? The dates are split
70% / 30% in time (the strategy rules were fixed before looking at the last 30%), and both parts are reported, together with the
combined call (two net votes) and a yardstick (always guessing the more common direction).

Run:  python scripts/evaluate_cmt_strategies.py
"""
import glob
import json
import os
import sys
from datetime import date

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from core import cmt_strategies as cmt  # noqa: E402
from core import daily_check as dc  # noqa: E402

KEYS = {"Fusion stage": "fusion", "Dow Theory": "dow", "Relative strength": "rs", "Wyckoff effort vs result": "wyckoff", "Fibonacci confluence": "fib"}


def load(path):
    return pd.read_csv(path, parse_dates=["Date"], index_col="Date").dropna(subset=["Close"])


def main():
    bench = load(os.path.join(ROOT, "data", "offline", "IDX_NSEI.csv"))["Close"]
    frames = []
    for path in sorted(glob.glob(os.path.join(ROOT, "data", "offline", "*.NS.csv"))):
        d = load(path)
        if len(d) < 500:
            continue
        f = cmt.signals_frame(d, bench)
        f["next"] = f["close"].pct_change().shift(-1)
        f["next5"] = f["close"].shift(-5) / f["close"] - 1
        f["next20"] = f["close"].shift(-20) / f["close"] - 1
        f["sym"] = os.path.basename(path)
        frames.append(f.iloc[260:-20])
    big = pd.concat(frames)
    cut = big.index.sort_values()[int(len(big) * 0.7)]
    early = (big.index <= cut)
    parts = {"first 70% of dates": big[early], "last 30% of dates": big[~early]}
    out = {"companies": int(big["sym"].nunique()), "days": int(len(big)), "split_date": str(cut.date()), "made_on": str(date.today()),
           "strategies": {}, "combined": {}}

    def precision(part, col, ahead):
        x = part[(part[col].fillna(0) != 0) & (part[ahead] != 0) & part[ahead].notna()]
        return float((np.sign(x[col]) == np.sign(x[ahead])).mean()), int(len(x))

    horizons = {"next day": "next", "next 5 days": "next5", "next 20 days": "next20"}
    for name, col in KEYS.items():
        rec = {}
        for hlabel, ahead in horizons.items():
            rec[hlabel] = {}
            for label, part in parts.items():
                acc, n = precision(part, col, ahead)
                rec[hlabel][label] = {"accuracy": acc, "calls": n}
        out["strategies"][name] = rec
        print(f"{name:26} " + " | ".join(f"{h}: {rec[h]['first 70% of dates']['accuracy']:.3f}/{rec[h]['last 30% of dates']['accuracy']:.3f}" for h in horizons))
    big = big.assign(score=big[list(KEYS.values())].fillna(0).sum(axis=1))
    parts = {"first 70% of dates": big[early], "last 30% of dates": big[~early]}
    for hlabel, ahead in horizons.items():
        out["combined"][hlabel] = {}
        for label, part in parts.items():
            x = part[(part["score"].abs() >= 2) & (part[ahead] != 0) & part[ahead].notna()]
            acc = float((np.sign(x["score"]) == np.sign(x[ahead])).mean())
            up_share = float((x[ahead] > 0).mean())
            out["combined"][hlabel][label] = {"accuracy": acc, "calls": int(len(x)), "yardstick": max(up_share, 1 - up_share)}
        c = out["combined"][hlabel]
        print(f"COMBINED {hlabel:13}: " + " | ".join(f"{l}: {v['accuracy']:.3f} (n={v['calls']}, always-guess {v['yardstick']:.3f})" for l, v in c.items()))
    with open(cmt.STATS_PATH, "w") as f:
        json.dump(out, f, indent=1)
    print("saved", cmt.STATS_PATH)


if __name__ == "__main__":
    main()
