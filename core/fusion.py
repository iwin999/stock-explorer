"""Fusion analysis, as taught in CMT Level III, Chapter 8 (Lundgren, 8.1; Letizia, 8.5).

The idea, in our own words
  * A price is built from fundamentals (F), valuation (V) and sentiment (S):   P = (F x V)^S.
    The price trend is the market's own opinion of all that, so a fundamental view only pays once the market agrees.
  * Winner's Circle: three circles - quality of fundamentals, valuation, and price trend & momentum.
    Trend & momentum is NOT negotiable. Every stock falls in one of four groups:
        1  trending and outperforming, with BOTH fundamental quality and valuation
        2  trending and outperforming, with at least ONE of them
        3  trending and outperforming, with NEITHER
        4  not (yet) trending: a watchlist
    Aim for many 1s, some 2s, few 3s, and avoid 4s.
  * Technical overlay (8.5): let the technicals CONFIRM, DELAY or REJECT a fundamental view. When the two disagree,
    pay more attention to risk: tighter stops, smaller positions, reassess.

The chapter's own scores come from its authors' proprietary models, whose formulas are not published. The versions
below are open, simple stand-ins in the same spirit: each company is ranked 0-100 against the other companies in our
list (a "percentile"). The group logic itself follows the chapter exactly.

Fundamentals are the yearly results from Yahoo Finance. A year's results are only used 75 days after the year ended
(companies must publish within about 60 days), so a test never "knows" something before it was public.
"""
import numpy as np
import pandas as pd

from core import indicators as ind
from core.companies import BENCHMARK, COMPANIES
from core.market_data import load_offline

REPORT_LAG_DAYS = 75        # a year's results count only this long after the year ended
PASS_SCORE = 50             # a 0-100 score at or above this "passes" a circle
MIN_UNIVERSE = 30           # need at least this many companies with data to rank them against each other

STAGES = {3: "Clear uptrend", 2: "Base of an uptrend", 1: "Base of a downtrend", 0: "Clear downtrend"}

GROUP_TEXT = {
    1: "Winner's Circle: trending and outperforming, with both fundamental quality and attractive valuation.",
    2: "Trending and outperforming, with fundamental quality or attractive valuation, but not both.",
    3: "Trending and outperforming, but neither fundamentals nor valuation stand out.",
    4: "Watchlist: the price trend and momentum have not (yet) confirmed.",
}


# ---------------- price-trend leg ----------------
def technical_table(close, bench_close):
    """Daily trend/momentum facts for one stock (a DataFrame indexed by date).

    Trend stage counts three tests: price above its 200-day average; 50-day average above the 200-day average;
    200-day average rising (higher than 20 days ago).  3 = clear uptrend, 2 = base of an uptrend,
    1 = base of a downtrend, 0 = clear downtrend.
    "Trending & outperforming" (the Winner's Circle test) = clear uptrend AND a positive 6-month return (momentum)
    AND a 6-month return ahead of the Nifty 50's (outperformance). RSI is shown for context but is not part of the test.
    """
    s50, s200 = ind.sma(close, 50), ind.sma(close, 200)
    valid = s200.notna() & s200.shift(20).notna()
    c1, c2, c3 = close > s200, s50 > s200, s200 > s200.shift(20)
    stage = (c1.astype(int) + c2.astype(int) + c3.astype(int)).where(valid)
    rsi = ind.rsi(close)
    bench = bench_close.reindex(close.index).ffill()
    ret6, bench6 = close.pct_change(126), bench.pct_change(126)
    in_circle = ((stage == 3) & (ret6 > 0) & (ret6 > bench6)).fillna(False)
    return pd.DataFrame({"close": close, "stage": stage, "rsi": rsi, "ret6": ret6, "rel6": ret6 - bench6,
                         "in_circle": in_circle, "above200": (close / s200 - 1)})


# ---------------- fundamentals leg ----------------
def _growth(cur, prev):
    if cur is None or prev is None or prev <= 0:
        return np.nan
    return cur / prev - 1


def fundamentals_asof(record, asof, price, lag_days=REPORT_LAG_DAYS):
    """The ratios a company's latest PUBLISHED yearly results give, as of a date. None if nothing is public yet."""
    asof = pd.Timestamp(asof)
    known = [p for p in sorted(record["annual"]) if pd.Timestamp(p) + pd.Timedelta(days=lag_days) <= asof]
    if not known:
        return None
    cur = record["annual"][known[-1]]
    prev = None
    if len(known) > 1 and 300 <= (pd.Timestamp(known[-1]) - pd.Timestamp(known[-2])).days <= 430:
        prev = record["annual"][known[-2]]
    equity, shares, eps = cur.get("equity"), cur.get("shares"), cur.get("eps")
    revenue, op_inc, net = cur.get("revenue"), cur.get("operating_income"), cur.get("net_income")
    financial = record.get("financial", False)
    return {
        "as_of_year": known[-1],
        "revenue_growth": _growth(revenue, prev.get("revenue") if prev else None),
        "earnings_growth": _growth(net, prev.get("net_income") if prev else None),
        "op_margin": op_inc / revenue if (op_inc is not None and revenue) else np.nan,
        "roe": net / equity if (net is not None and equity and equity > 0) else np.nan,
        # debt ratios mean little for banks and lenders (deposits and loans are their business)
        "debt_equity": cur["debt"] / equity if (not financial and cur.get("debt") is not None and equity and equity > 0) else np.nan,
        "pe": (price / eps if eps > 0 else np.inf) if eps is not None else np.nan,          # loss-making: worst
        "pb": price / (equity / shares) if (equity and equity > 0 and shares) else np.nan,
    }


def _pct(series, higher_is_better=True):
    """0-100 rank of each company against the others (NaN stays NaN)."""
    s = series if higher_is_better else -series
    return s.rank(pct=True, na_option="keep") * 100


def score_fundamentals(table):
    """Add 0-100 scores to a table with one row per company of fundamentals_asof() ratios.

      growth  = average rank of revenue growth and earnings growth
      returns = average rank of return on equity and operating margin
      leverage= rank of LOW debt-to-equity
      F (quality of fundamentals) = average of the available parts of growth / returns / leverage
      V (valuation)               = average rank of LOW P/E and LOW price-to-book
    """
    out = table.copy()
    out["growth_score"] = pd.concat([_pct(out["revenue_growth"]), _pct(out["earnings_growth"])], axis=1).mean(axis=1)
    out["returns_score"] = pd.concat([_pct(out["roe"]), _pct(out["op_margin"])], axis=1).mean(axis=1)
    out["leverage_score"] = _pct(out["debt_equity"], higher_is_better=False)
    out["F"] = out[["growth_score", "returns_score", "leverage_score"]].mean(axis=1)
    out["V"] = pd.concat([_pct(out["pe"], False), _pct(out["pb"], False)], axis=1).mean(axis=1)
    return out


def group_of(in_circle, quality_ok, value_ok):
    if not in_circle:
        return 4
    return 1 if (quality_ok and value_ok) else 2 if (quality_ok or value_ok) else 3


def verdict_for(group, quality_ok, value_ok):
    """(label, explanation, divergence?) - the 'technical overlay' of Chapter 8.5."""
    if group == 1:
        return ("Confirm", "The market's trend backs up the fundamentals and valuation. This is the Winner's Circle.", False)
    if group == 2:
        return ("Confirm, with a caveat", "The trend is confirmed, and one of fundamentals or valuation supports it. "
                "The other does not, so keep an eye on it.", False)
    if group == 3:
        return ("Divergence: trend without fundamentals",
                "The price is trending, but neither fundamentals nor valuation stand out. When the two disagree, give "
                "risk management more weight: smaller positions, tighter stops, and reassess the evidence.", True)
    if quality_ok and value_ok:
        return ("Delay: fundamentals look fine, price has not confirmed",
                "Fundamentals and valuation rank well, but the market has not agreed yet. The framework says wait for "
                "the trend and momentum to confirm, and keep risk tight meanwhile.", True)
    return ("Reject for now", "The price trend has not confirmed, and the fundamentals do not stand out either.", False)


# ---------------- the whole list of companies ----------------
def load_universe():
    """(prices dict {symbol: close Series}, Nifty close Series) from the saved price files."""
    prices = {}
    for _name, symbol, _ in COMPANIES:
        df = load_offline(symbol)
        if df is not None and len(df) > 250:
            prices[symbol] = df["Close"]
    bench = load_offline(BENCHMARK)
    return prices, (bench["Close"] if bench is not None else None)


def build_technicals(prices, bench):
    return {s: technical_table(c, bench) for s, c in prices.items()}


def classify(asof, technicals, funds):
    """Rate every company as of a date. Returns a DataFrame (one row per company) with scores, group and verdict.

    technicals - {symbol: technical_table()};  funds - fundamentals file contents ({'companies': {...}}).
    """
    asof = pd.Timestamp(asof)
    rows = {}
    for symbol, tech in technicals.items():
        upto = tech.loc[:asof]
        if upto.empty or pd.isna(upto["stage"].iloc[-1]) or (asof - upto.index[-1]).days > 10:
            continue
        last = upto.iloc[-1]
        row = {"stage": int(last["stage"]), "stage_name": STAGES[int(last["stage"])], "rsi": last["rsi"],
               "ret6": last["ret6"], "rel6": last["rel6"], "in_circle": bool(last["in_circle"]), "close": last["close"],
               "date": upto.index[-1]}
        record = funds.get("companies", {}).get(symbol)
        row.update(fundamentals_asof(record, asof, last["close"]) or {} if record else {})
        rows[symbol] = row
    table = pd.DataFrame.from_dict(rows, orient="index")
    for col in ("revenue_growth", "earnings_growth", "op_margin", "roe", "debt_equity", "pe", "pb"):
        if col not in table:
            table[col] = np.nan
    if table.empty:
        return table
    has_funds = table[["revenue_growth", "earnings_growth", "op_margin", "roe", "pe", "pb"]].notna().any(axis=1)
    if has_funds.sum() < MIN_UNIVERSE:
        table["group"] = np.nan                      # too few companies to rank against each other
        return table
    scored = score_fundamentals(table)
    for col in ("growth_score", "returns_score", "leverage_score", "F", "V"):
        table[col] = scored[col]
    table["quality_ok"] = table["F"] >= PASS_SCORE
    table["value_ok"] = table["V"] >= PASS_SCORE
    judged = table["F"].notna() & table["V"].notna()
    table["group"] = np.nan
    table.loc[judged, "group"] = [group_of(c, q, v) for c, q, v in zip(
        table.loc[judged, "in_circle"], table.loc[judged, "quality_ok"], table.loc[judged, "value_ok"])]
    labels = [verdict_for(int(g), q, v) if g == g else ("Not enough data", "", False)
              for g, q, v in zip(table["group"], table["quality_ok"].fillna(False), table["value_ok"].fillna(False))]
    table["verdict"], table["why"], table["divergence"] = zip(*labels) if labels else ((), (), ())
    return table


from core.ratios import expectancy  # noqa: E402,F401  (kept here too: it is part of the Chapter 8 toolkit)


# ---------------- model-portfolio test ----------------
def month_starts(index, first, last):
    """The first trading day of each month between two dates."""
    days = index[(index >= first) & (index <= last)]
    return list(days.to_series().groupby([days.year, days.month]).first())


def run_fusion_backtest(prices, bench, technicals, funds, cost_pct=0.10):
    """Equal-weight model portfolios rebuilt on the first trading day of each month using only what was public then.

    Ratings use only data up to the close of the signal day; the trade is made at the next day's close.
    Returns None if there is not enough data, else a dict with equity curves (Rs 1,00,000 start) for:
      Group 1 only / Groups 1 and 2 / all companies equal-weighted / Nifty 50, plus stats and the latest holdings.
    """
    closes = pd.DataFrame(prices).sort_index().ffill()
    if bench is None or closes.empty:
        return None
    # the first month when enough companies have both prices and published results
    probe_dates = month_starts(closes.index, closes.index[260], closes.index[-1])
    start_i = None
    for i, d in enumerate(probe_dates):
        table = classify(d, technicals, funds)
        if "group" in table and table["group"].notna().sum() >= MIN_UNIVERSE:
            start_i = i
            break
    if start_i is None:
        return None
    dates = probe_dates[start_i:]
    end = closes.index[-1]
    # A rating is known at the CLOSE of the signal day, so the trade happens at the NEXT trading day's close
    # (otherwise the test would buy at a price it only learned about after the close).
    positions = closes.index
    execs = [positions[positions.get_loc(d) + 1] for d in dates if positions.get_loc(d) + 1 < len(positions)]
    dates = dates[:len(execs)]

    arms = {"Group 1 only": (1,), "Groups 1 and 2": (1, 2), "All companies (equal weight)": None}
    equity = {k: [] for k in arms}
    value = {k: 100000.0 for k in arms}
    weights_prev = {k: pd.Series(dtype=float) for k in arms}
    held_log, counts = {}, {k: [] for k in arms}
    index_out = []
    classified_all = {}

    for i, d in enumerate(dates):
        table = classify(d, technicals, funds)
        classified_all[d] = table
        upto = execs[i + 1] if i + 1 < len(execs) else end
        window = closes.loc[execs[i]:upto]
        if len(window) < 2:
            continue
        for arm, groups in arms.items():
            if groups is None:
                chosen = list(table.index[table["group"].notna()])
            else:
                chosen = list(table.index[table["group"].isin(groups)])
            held_log[arm] = chosen
            counts[arm].append(len(chosen))
            w_new = pd.Series(1.0 / len(chosen), index=chosen) if chosen else pd.Series(dtype=float)
            # trading cost on the amount bought and sold at this rebalance
            union = w_new.index.union(weights_prev[arm].index)
            turnover = (w_new.reindex(union, fill_value=0) - weights_prev[arm].reindex(union, fill_value=0)).abs().sum()
            value[arm] *= (1 - turnover * cost_pct / 100.0)
            if chosen:
                growth = window[chosen] / window[chosen].iloc[0]           # each stock's value path this month
                path = growth.mul(w_new, axis=1)
                port = path.sum(axis=1)                                     # portfolio value (starts at 1)
                weights_prev[arm] = path.iloc[-1] / port.iloc[-1]          # weights after the month's drift
                series = value[arm] * port
            else:
                weights_prev[arm] = pd.Series(dtype=float)
                series = pd.Series(value[arm], index=window.index)
            value[arm] = float(series.iloc[-1])
            equity[arm].append(series.iloc[:-1] if i + 1 < len(dates) else series)
        index_out.append(d)

    curves = pd.DataFrame({k: pd.concat(v) for k, v in equity.items()})
    bench_series = bench.reindex(curves.index).ffill()
    curves["Nifty 50"] = 100000.0 * bench_series / bench_series.iloc[0]
    from core import ratios

    daily = curves.pct_change().dropna()
    stats = {}
    for col in curves.columns:
        s = ratios.summary(daily[col], daily["Nifty 50"] if col != "Nifty 50" else None)
        if s:
            s["final_value"] = float(curves[col].iloc[-1])
            stats[col] = s
    last_table = classified_all[dates[-1]]
    return {"curves": curves, "stats": stats, "start": curves.index[0], "end": curves.index[-1],
            "rebalances": len(dates), "execution_dates": execs, "avg_holdings": {k: float(np.mean(v)) if v else 0.0 for k, v in counts.items()},
            "latest": last_table, "cost_pct": cost_pct}
