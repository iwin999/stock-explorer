"""Back-test the five CMT strategies and the ML model on EACH saved NSE company separately and write data/cmt_company_stats.json.

For every company and every strategy: on the days the strategy voted Up or Down, how often did the price move that way over the
next day and over the next 20 days? The numbers come from that company's own history (after a 260-day warm-up), so they differ from
company to company. The ML model is checked only on the dates it was NOT trained on (after the split date in data/ml_model.json).

Run:  python scripts/evaluate_company_backtests.py
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
from core import ml_model as ml  # noqa: E402

KEYS = {"Fusion stage": "fusion", "Dow Theory": "dow", "Relative strength": "rs", "Wyckoff effort vs result": "wyckoff", "Fibonacci confluence": "fib"}


def load(path):
    return pd.read_csv(path, parse_dates=["Date"], index_col="Date").dropna(subset=["Close"])


def precision(vote, ahead):
    ok = (vote.fillna(0) != 0) & (ahead != 0) & ahead.notna()
    if not ok.any():
        return {"accuracy": None, "calls": 0}
    return {"accuracy": float((np.sign(vote[ok]) == np.sign(ahead[ok])).mean()), "calls": int(ok.sum())}


def main():
    bench = load(os.path.join(ROOT, "data", "offline", "IDX_NSEI.csv"))["Close"]
    model = ml.load_model()
    out = {"made_on": str(date.today()), "split_date": model["split_date"] if model else None, "companies": {}}
    for path in sorted(glob.glob(os.path.join(ROOT, "data", "offline", "*.NS.csv"))):
        d = load(path)
        if len(d) < 500:
            continue
        sym = os.path.basename(path)[:-len(".csv")]
        f = cmt.signals_frame(d, bench)
        f["next"] = f["close"].pct_change().shift(-1)
        f["next20"] = f["close"].shift(-20) / f["close"] - 1
        rows = f.iloc[260:-20]
        rec = {"strategies": {}}
        for name, col in KEYS.items():
            rec["strategies"][name] = {"next day": precision(rows[col], rows["next"]), "next 20 days": precision(rows[col], rows["next20"])}
        if model:
            frame = ml.features_frame(d, bench)
            frame["next"] = d["Close"].pct_change().shift(-1)
            test = frame.iloc[260:-1]
            test = test[(test.index > pd.Timestamp(model["split_date"])) & test["next"].notna() & (test["next"] != 0)].dropna(subset=ml.FEATURES)
            if len(test) >= 30:
                z = (test[ml.FEATURES].values - np.array(model["mean"])) / np.array(model["std"])
                p = 1 / (1 + np.exp(-(z @ np.array(model["weights"]) + model["bias"])))
                up = (test["next"] > 0).values
                conf = (p >= 0.54) | (p <= 0.46)
                rec["ML model"] = {"accuracy": float(((p > 0.5) == up).mean()), "days": int(len(test)),
                                   "confident_accuracy": float(((p[conf] > 0.5) == up[conf]).mean()) if conf.sum() >= 10 else None,
                                   "confident_days": int(conf.sum())}
        out["companies"][sym] = rec
    path = cmt.COMPANY_STATS_PATH
    with open(path, "w") as fh:
        json.dump(out, fh, separators=(",", ":"))
    print("saved", path, "for", len(out["companies"]), "companies,", round(os.path.getsize(path) / 1024), "KB")


if __name__ == "__main__":
    main()
