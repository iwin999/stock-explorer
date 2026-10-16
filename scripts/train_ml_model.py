"""Train the logistic-regression estimate on every saved NSE company and write data/ml_model.json.

Dates are split 70% / 30% in time: the model is fitted on the first 70% and checked on the last 30%, then the numbers are saved
next to the weights. Run:  python scripts/train_ml_model.py
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
from core import ml_model as ml  # noqa: E402


def load(path):
    return pd.read_csv(path, parse_dates=["Date"], index_col="Date").dropna(subset=["Close"])


def main():
    bench = load(os.path.join(ROOT, "data", "offline", "IDX_NSEI.csv"))["Close"]
    parts = []
    for path in sorted(glob.glob(os.path.join(ROOT, "data", "offline", "*.NS.csv"))):
        d = load(path)
        if len(d) < 500:
            continue
        f = ml.features_frame(d, bench)
        f["next"] = d["Close"].pct_change().shift(-1)
        f["sym"] = os.path.basename(path)
        parts.append(f.iloc[260:-1])
    big = pd.concat(parts)
    big = big[big["next"].notna() & (big["next"] != 0)].dropna(subset=ml.FEATURES)
    cut = big.index.sort_values()[int(len(big) * 0.7)]
    train, test = big[big.index <= cut], big[big.index > cut]
    Xtr, mean, std = ml.standardise(train[ml.FEATURES].values)
    ytr = (train["next"] > 0).astype(float).values
    w, b = ml.fit(Xtr, ytr)
    Xte, _, _ = ml.standardise(test[ml.FEATURES].values, mean, std)
    yte = (test["next"] > 0).astype(float).values

    def score(X, y):
        p = 1 / (1 + np.exp(-(X @ w + b)))
        acc = float(((p > 0.5) == (y == 1)).mean())
        conf = (p >= 0.54) | (p <= 0.46)
        cacc = float(((p[conf] > 0.5) == (y[conf] == 1)).mean()) if conf.sum() else None
        return {"accuracy": acc, "days": int(len(y)), "confident_accuracy": cacc, "confident_days": int(conf.sum()),
                "always_up": float(max(y.mean(), 1 - y.mean()))}

    tested = {"first 70% of dates (trained on)": score(Xtr, ytr), "last 30% of dates (held back)": score(Xte, yte)}
    for k, v in tested.items():
        print(k, {a: (round(c, 4) if isinstance(c, float) else c) for a, c in v.items()})
    top = sorted(zip(ml.FEATURES, w), key=lambda kv: -abs(kv[1]))[:6]
    print("biggest weights:", [(k, round(float(v), 3)) for k, v in top])
    out = {"features": ml.FEATURES, "weights": w.tolist(), "bias": float(b), "mean": mean.tolist(), "std": std.tolist(),
           "companies": int(big["sym"].nunique()), "rows": int(len(big)), "split_date": str(cut.date()), "made_on": str(date.today()),
           "tested": tested}
    with open(ml.MODEL_PATH, "w") as f:
        json.dump(out, f, indent=1)
    print("saved", ml.MODEL_PATH)


if __name__ == "__main__":
    main()
