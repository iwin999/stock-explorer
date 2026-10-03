"""Risk and return ratios, each with a plain-English sentence.

Input: a pandas Series of DAILY returns (e.g. 0.01 = +1% that day), and optionally the
benchmark's daily returns (the Nifty 50) for the ratios that compare against the market.
"""
import numpy as np
import pandas as pd

TRADING_DAYS = 252
RISK_FREE = 0.065   # assumed 6.5% a year: roughly what a safe Indian government bond pays


def summary(returns, benchmark=None, risk_free=RISK_FREE):
    """All the ratios as a dict. Values that cannot be computed are None."""
    r = pd.Series(returns).dropna()
    if len(r) < 20:
        return None

    rf_d = (1 + risk_free) ** (1 / TRADING_DAYS) - 1           # risk-free return per day
    equity = (1 + r).cumprod()
    total = float(equity.iloc[-1] - 1)
    years = len(r) / TRADING_DAYS
    cagr = float((1 + total) ** (1 / years) - 1) if total > -1 else -1.0
    vol = float(r.std() * np.sqrt(TRADING_DAYS))
    excess = r - rf_d
    drawdown = equity / equity.cummax() - 1
    max_dd = float(drawdown.min())

    downside = float(np.sqrt((np.minimum(excess, 0) ** 2).mean()) * np.sqrt(TRADING_DAYS))
    tail = np.percentile(r, 5)

    out = {
        "total_return": total,
        "cagr": cagr,
        "volatility": vol,
        "max_drawdown": max_dd,
        "sharpe": float(excess.mean() * TRADING_DAYS / vol) if vol > 1e-9 else None,
        "sortino": float(excess.mean() * TRADING_DAYS / downside) if downside > 1e-9 else None,
        "calmar": float(cagr / abs(max_dd)) if max_dd < 0 else None,
        "var95": float(-tail),                                   # a bad day: loss exceeded on 1 day in 20
        "cvar95": float(-r[r <= tail].mean()),                   # average loss on those bad days
        "win_rate": float((r > 0).mean()),
        "best_day": float(r.max()),
        "worst_day": float(r.min()),
        "beta": None, "alpha": None, "treynor": None, "information": None, "correlation": None,
    }

    if benchmark is not None:
        b = pd.Series(benchmark).dropna()
        both = pd.concat([r, b], axis=1, join="inner").dropna()
        if len(both) >= 60 and both.iloc[:, 1].var() > 0:
            rr, bb = both.iloc[:, 0], both.iloc[:, 1]
            beta = float(rr.cov(bb) / bb.var())
            out["beta"] = beta
            out["correlation"] = float(rr.corr(bb))
            out["alpha"] = float(((rr - rf_d).mean() - beta * (bb - rf_d).mean()) * TRADING_DAYS)
            if abs(beta) > 0.05:
                out["treynor"] = float((rr - rf_d).mean() * TRADING_DAYS / beta)
            active = rr - bb
            if active.std() > 0:
                out["information"] = float(active.mean() * TRADING_DAYS / (active.std() * np.sqrt(TRADING_DAYS)))
    return out


# ---------------- text for the screen ----------------
def pct(x, digits=1, sign=False):
    return "n/a" if x is None else f"{x * 100:{'+' if sign else ''}.{digits}f}%"


def num(x, digits=2):
    return "n/a" if x is None else f"{x:.{digits}f}"


def describe(key, s):
    """(value as text, one-sentence meaning) for a ratio key, from a summary dict."""
    v = s.get(key)
    if v is None:
        return "n/a", "Not enough data to calculate this."
    if key == "cagr":
        return pct(v, sign=True), f"On average the investment grew about {v * 100:.1f}% a year over this period."
    if key == "volatility":
        return pct(v), f"The price typically swings about {v * 100:.0f}% up or down over a year. Higher means a bumpier ride."
    if key == "max_drawdown":
        return pct(v), f"The worst fall from a peak to a low point was {abs(v) * 100:.0f}%. This is the pain an investor would have lived through."
    if key == "var95":
        return pct(v), f"On 1 day in 20, the loss has been at least {v * 100:.1f}% (Value at Risk, 95%)."
    if key == "sharpe":
        word = "poor" if v < 0.5 else "decent" if v < 1 else "good" if v < 2 else "excellent"
        return num(v), f"Return earned per unit of total risk, after the safe rate: {word}. Above 1 is generally considered good."
    if key == "sortino":
        return num(v), "Like Sharpe, but only counts the bad swings (falls) as risk. Higher is better."
    if key == "calmar":
        return num(v), "Yearly growth divided by the worst fall. It shows how much return you got for the pain endured. Higher is better."
    if key == "treynor":
        return pct(v), "Extra return earned per unit of risk taken from moving with the market (beta)."
    if key == "beta":
        word = "more" if v > 1.05 else "less" if v < 0.95 else "about as much"
        return num(v), f"When the Nifty 50 moves 1%, this stock has tended to move {v:.2f}%: {word} swing than the market."
    if key == "alpha":
        return pct(v, sign=True), "Yearly return beyond what the market's movements alone would explain. Positive means it did better than expected for its risk."
    if key == "information":
        return num(v), "How consistently it beat (or trailed) the Nifty 50, relative to how much it differed. Above 0.5 is considered good."
    if key == "correlation":
        return num(v), "How closely it moves with the Nifty 50: 1 means in step, 0 means unrelated, below 0 means opposite."
    if key == "win_rate":
        return pct(v, 0), "The share of days the price closed higher."
    return str(v), ""


GLOSSARY = """
**Annual return (CAGR).** The steady yearly growth rate that would turn the starting value into the ending value.

**Volatility.** How much the price jumps around, as a yearly percentage. Calm stocks are low, bumpy stocks are high.

**Maximum drawdown.** The biggest fall from a high point to the next low point. It tells you the worst loss someone holding through the period would have seen.

**Value at Risk (VaR, 95%).** A "bad day" measure: on 19 days out of 20 the loss was smaller than this; on 1 day in 20 it was bigger.

**Sharpe ratio.** (Return minus the safe interest rate) divided by volatility. It asks: how much reward for each unit of risk? Higher is better, and above 1 is generally considered good.

**Sortino ratio.** Like Sharpe, but it only counts the falls as risk, since investors do not mind upward jumps.

**Calmar ratio.** Yearly return divided by the maximum drawdown: reward compared with the worst pain.

**Beta.** How strongly the stock moves compared with the market (the Nifty 50). Beta 1.5 means that when the market moves 1%, this stock tends to move 1.5%.

**Alpha.** The extra yearly return beyond what its beta alone would explain. Positive alpha means it beat what its market risk deserved.

**Treynor ratio.** Extra return over the safe rate, divided by beta: reward per unit of market risk.

**Information ratio.** How steadily the stock beat (or trailed) the Nifty 50.

**Correlation.** How closely it moves in step with the Nifty 50, from -1 to 1.

*Safe rate used here: 6.5% a year (about what a government bond pays). Ratios describe the past only.*
"""
