"""A small, explainable machine-learning estimate of tomorrow's direction.

The model is a logistic regression (written with numpy only, so nothing extra has to be installed). It looks at the five CMT
strategy votes plus a dozen indicator readings, all worked out from data up to the previous day, and gives the chance (0 to 100%)
that the next day closes higher. It was trained once, on every saved NSE company at the same time, using only the first 70% of
the dates; the last 30% were kept back to check it (scripts/train_ml_model.py writes data/ml_model.json with the weights and the
checked accuracy). Nothing here looks at the future when it makes an estimate.

Honest expectations: day-to-day direction is very close to a coin toss, so a good model scores about 51 to 53%. The screen shows
the model's own tested accuracy next to its estimate.
"""
import json
import os

import numpy as np
import pandas as pd

from core import cmt_strategies as cmt
from core import daily_check as dc

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "ml_model.json")

FEATURES = ["fusion", "dow", "rs", "wyckoff", "fib",                       # the five CMT strategy votes
            "rsi", "stochrsi", "pct_b", "zscore", "macd", "adx_lean", "supertrend",
            "ret1", "mom5", "clv", "vol_ratio", "volatility", "above200"]
LABELS = {"fusion": "Fusion stage", "dow": "Dow Theory", "rs": "Relative strength", "wyckoff": "Wyckoff effort vs result",
          "fib": "Fibonacci confluence", "rsi": "RSI", "stochrsi": "Stochastic RSI", "pct_b": "Bollinger position",
          "zscore": "Z-score", "macd": "MACD", "adx_lean": "ADX direction", "supertrend": "Supertrend", "ret1": "Yesterday's move",
          "mom5": "Last 5 days", "clv": "Where yesterday closed", "vol_ratio": "Volume vs usual", "volatility": "Volatility",
          "above200": "Distance from 200-day average"}


def features_frame(hist, bench_close):
    """One row per day of model inputs, each known at the END of that day (so a row predicts the NEXT day)."""
    sig = cmt.signals_frame(hist, bench_close)
    ind = dc.indicator_frame(hist)
    close = ind["close"]
    mean20, std20 = close.rolling(20).mean(), close.rolling(20).std()
    out = pd.DataFrame(index=close.index)
    for k in ("fusion", "dow", "rs", "wyckoff", "fib"):
        out[k] = sig[k].fillna(0.0)
    out["rsi"] = (ind["rsi"] - 50) / 50
    out["stochrsi"] = ind["stochrsi"] - 0.5
    out["pct_b"] = ((close - ind["bb_lo"]) / (ind["bb_up"] - ind["bb_lo"]).replace(0, np.nan)) - 0.5
    out["zscore"] = ((close - mean20) / std20.replace(0, np.nan)).clip(-4, 4)
    out["macd"] = (ind["macd_hist"] / close * 100).clip(-5, 5)
    lean = ind["pdi"] / (ind["pdi"] + ind["mdi"]).replace(0, np.nan) - 0.5
    out["adx_lean"] = lean * (ind["adx"] / 100)
    out["supertrend"] = ind["supertrend"]
    out["ret1"] = ind["ret1"].clip(-0.1, 0.1)
    out["mom5"] = ind["mom5"].clip(-0.3, 0.3)
    out["clv"] = ind["clv"].fillna(0.0)
    out["vol_ratio"] = np.log(ind["vol_ratio"].clip(0.2, 5)).fillna(0.0)
    out["volatility"] = ind["daily_vol"].clip(0, 0.08)
    out["above200"] = (close / ind["sma200"] - 1).clip(-0.5, 0.5)
    return out[FEATURES]


# ---------------- training (numpy logistic regression) ----------------
def fit(X, y, l2=1.0, steps=400, lr=0.5):
    """Plain gradient descent for L2-regularised logistic regression. X is already standardised. Returns (weights, bias)."""
    n, k = X.shape
    w, b = np.zeros(k), 0.0
    for _ in range(steps):
        p = 1 / (1 + np.exp(-(X @ w + b)))
        g = p - y
        w -= lr * (X.T @ g / n + l2 * w / n)
        b -= lr * g.mean()
    return w, b


def standardise(X, mean=None, std=None):
    mean = X.mean(axis=0) if mean is None else mean
    std = (X.std(axis=0) + 1e-9) if std is None else std
    return (X - mean) / std, mean, std


# ---------------- using the saved model ----------------
def load_model():
    """The trained model (a dict) or None if data/ml_model.json is missing."""
    try:
        with open(MODEL_PATH) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def probability_up(row, model):
    """The model's chance (0 to 1) that the next day closes higher, for one row of features, plus each input's push on it."""
    x = np.array([float(row[k]) for k in model["features"]])
    if np.isnan(x).any():
        x = np.nan_to_num(x)
    z = (x - np.array(model["mean"])) / np.array(model["std"])
    contributions = z * np.array(model["weights"])
    p = 1 / (1 + np.exp(-(contributions.sum() + model["bias"])))
    return float(p), dict(zip(model["features"], contributions.tolist()))


def estimate(basis_hist, bench_close, model=None):
    """{'p_up', 'lean', 'top': [(label, push)], 'tested'} for the day after the last day in `basis_hist`, or None."""
    model = model or load_model()
    basis_hist = basis_hist[basis_hist["Close"].notna()]
    if model is None or bench_close is None or len(basis_hist) < 260:
        return None
    frame = features_frame(basis_hist, bench_close)
    p, contrib = probability_up(frame.iloc[-1], model)
    lean = "Up" if p >= 0.54 else "Down" if p <= 0.46 else "None"          # the same 54% / 46% line the confident days were tested at
    top = sorted(contrib.items(), key=lambda kv: -abs(kv[1]))[:3]
    return {"p_up": p, "lean": lean, "top": [(LABELS[k], v) for k, v in top], "tested": model.get("tested", {})}
