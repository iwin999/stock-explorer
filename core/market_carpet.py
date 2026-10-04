"""Data and charts for the Market carpet tab (no Streamlit screen code here; see core/carpet_ui.py).

A market carpet is a map of many companies at once (CMT Level III, Chapter 2.3):
  * every company is a tile, its SIZE is how large the company is (market capitalisation), and
  * its COLOUR is how it has performed (green up, red down).
Tiles are grouped by industry, so you can see which industries are strong before looking at single companies.

Where the data comes from: Yahoo Finance's screener, asked for each sector on the NSE and the BSE. Yahoo has no
"list every stock" call, so each sector shows its largest companies (default 60 per exchange); the full count
listed is kept so the screen can say how many are not shown. A saved snapshot is the fallback if Yahoo is down.
"""
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import pandas as pd
import plotly.graph_objects as go

SNAPSHOT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "offline", "market_carpet.json")

# Yahoo's sector names, with a friendlier name for the screen.
SECTORS = {
    "Technology": "Technology", "Financial Services": "Financial services", "Healthcare": "Healthcare",
    "Consumer Cyclical": "Consumer (discretionary)", "Consumer Defensive": "Consumer (staples)", "Energy": "Energy",
    "Industrials": "Industrials", "Basic Materials": "Materials and metals", "Real Estate": "Real estate",
    "Utilities": "Utilities", "Communication Services": "Telecom and media",
}
EXCHANGES = {"NSI": "NSE", "BSE": "BSE"}

# How performance is measured (the label, and the colour range that counts as "full green / full red").
METRICS = {
    "day": ("Today", 3.0),
    "ma50": ("Against its 50-day average", 12.0),
    "ma200": ("Against its 200-day average", 30.0),
}
DEFAULT_PER_EXCHANGE = 60


# ---------------- getting the data ----------------
def _norm(name):
    """A company's name reduced to its core, so the NSE and BSE entries of one company can be matched."""
    s = re.sub(r"[^a-z0-9 ]", " ", (name or "").lower())
    s = re.sub(r"\b(limited|ltd|the|co|company|corporation|corp|india|industries)\b", " ", s)
    return re.sub(r"\s+", "", s)


def pretty(name):
    """INFOSYS LIMITED -> Infosys."""
    s = re.sub(r"\b(LIMITED|LTD\.?)\b", "", name or "", flags=re.I)
    s = re.sub(r"\s+", " ", s).strip(" .,")
    return s.title() if s.isupper() or s.islower() else s


def _row(q, sector):
    cap = q.get("marketCap")
    if not cap or not q.get("symbol"):
        return None
    pct = lambda v: None if v is None else float(v) * 100        # Yahoo gives these two as fractions
    return {"symbol": q["symbol"], "name": pretty(q.get("longName") or q.get("shortName") or q["symbol"]),
            "exchange": EXCHANGES.get(q.get("exchange"), q.get("exchange")), "sector": sector,
            "cap": float(cap), "price": q.get("regularMarketPrice"),
            "day": None if q.get("regularMarketChangePercent") is None else float(q["regularMarketChangePercent"]),
            "ma50": pct(q.get("fiftyDayAverageChangePercent")), "ma200": pct(q.get("twoHundredDayAverageChangePercent"))}


def _screen(sector, exchange, size):
    import yfinance as yf
    from yfinance import EquityQuery as Q
    query = Q("and", [Q("eq", ["region", "in"]), Q("eq", ["exchange", exchange]), Q("eq", ["sector", sector])])
    r = yf.screen(query, sortField="intradaymarketcap", sortAsc=False, size=size)
    return [x for x in (_row(q, sector) for q in r.get("quotes", [])) if x], int(r.get("total") or 0)


def _base(symbol):
    return symbol.rsplit(".", 1)[0].upper()


def merge_exchanges(nse, bse):
    """One list per sector: all NSE companies, plus BSE companies that are not also on the NSE list
    (matched by ticker or by name, because the two exchanges spell names a little differently)."""
    tickers = {_base(c["symbol"]) for c in nse}
    names = {_norm(c["name"]) for c in nse}
    return nse + [c for c in bse if _base(c["symbol"]) not in tickers and _norm(c["name"]) not in names]


def build(per_exchange=DEFAULT_PER_EXCHANGE):
    """Ask Yahoo for every sector on both exchanges. Returns {"asof", "sectors": {sector: {...}}}.
    A sector that fails is left out; if everything fails the result has no sectors."""
    jobs = [(s, ex) for s in SECTORS for ex in EXCHANGES]

    def run(job):
        try:
            return job, _screen(job[0], job[1], per_exchange)
        except Exception:
            return job, None

    with ThreadPoolExecutor(max_workers=6) as pool:
        results = dict(pool.map(run, jobs))
    sectors = {}
    for sector in SECTORS:
        nse, bse = results.get((sector, "NSI")), results.get((sector, "BSE"))
        if not nse and not bse:
            continue
        companies = merge_exchanges(nse[0] if nse else [], bse[0] if bse else [])
        if companies:
            sectors[sector] = {"companies": companies,
                               "listed": {"NSE": nse[1] if nse else 0, "BSE": bse[1] if bse else 0}}
    return {"asof": datetime.now(timezone.utc).isoformat(timespec="seconds"), "sectors": sectors}


def save_snapshot(data, path=SNAPSHOT_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f)


def load_snapshot(path=SNAPSHOT_PATH):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def get_data():
    """(data, source): live from Yahoo if it works, else the saved snapshot ('saved'), else (None, None)."""
    data = build()
    if data["sectors"]:
        return data, "live"
    snap = load_snapshot()
    return (snap, "saved") if snap and snap.get("sectors") else (None, None)


# ---------------- numbers ----------------
def weighted(companies, metric):
    """Market-cap-weighted average of a performance measure (bigger companies count for more)."""
    rows = [(c["cap"], c[metric]) for c in companies if c.get(metric) is not None]
    total = sum(w for w, _ in rows)
    return sum(w * v for w, v in rows) / total if total else None


def sector_table(data, metric):
    """One row per industry (only industries that have NSE or BSE companies), strongest first."""
    rows = []
    for sector, info in data["sectors"].items():
        cs = info["companies"]
        rows.append({"Industry": SECTORS.get(sector, sector), "Key": sector, "Companies shown": len(cs),
                     "Listed (NSE / BSE)": f"{info['listed']['NSE']} / {info['listed']['BSE']}",
                     "Combined size (Rs crore)": sum(c["cap"] for c in cs) / 1e7,
                     "Performance": weighted(cs, metric)})
    df = pd.DataFrame(rows)
    return df.sort_values("Performance", ascending=False, na_position="last").reset_index(drop=True) if not df.empty else df


def company_table(data, sector, metric):
    cs = data["sectors"][sector]["companies"]
    df = pd.DataFrame([{"Company": c["name"], "Exchange": c["exchange"], "Symbol": c["symbol"], "Price": c["price"],
                        "Size (Rs crore)": c["cap"] / 1e7, "Performance": c.get(metric)} for c in cs])
    return df.sort_values("Size (Rs crore)", ascending=False).reset_index(drop=True)


# ---------------- charts ----------------
SCALE = [[0.0, "#b3342a"], [0.35, "#e9a59d"], [0.5, "#eceff3"], [0.65, "#9fd0b8"], [1.0, "#1f8a5b"]]


def _fmt(v):
    return "n/a" if v is None else f"{v:+.1f}%"


def carpet(data, metric, sector=None):
    """The market carpet. sector=None: one tile per industry. sector=<key>: that industry's companies."""
    label, span = METRICS[metric]
    ids, labels, values, colours, text = [], [], [], [], []
    if sector is None:
        for s, info in data["sectors"].items():
            cs = info["companies"]
            perf = weighted(cs, metric)
            ids.append(s)
            labels.append(SECTORS.get(s, s))
            values.append(sum(c["cap"] for c in cs))
            colours.append(perf if perf is not None else 0.0)
            text.append(_fmt(perf))
    else:
        for c in data["sectors"][sector]["companies"]:
            v = c.get(metric)
            ids.append(c["symbol"])
            labels.append(c["name"] + (" (BSE)" if c["exchange"] == "BSE" else ""))
            values.append(c["cap"])
            colours.append(v if v is not None else 0.0)
            text.append(_fmt(v))
    fig = go.Figure(go.Treemap(
        ids=ids, labels=labels, parents=[""] * len(ids), values=values, customdata=text, branchvalues="total",
        marker=dict(root=dict(color='rgba(0,0,0,0)'), colors=colours, colorscale=SCALE, cmin=-span, cmax=span, cmid=0,
                    line=dict(width=1.5, color="#ffffff"),
                    colorbar=dict(title=dict(text=f"{label} (%)"), thickness=12, len=0.8)),
        texttemplate="<b>%{label}</b><br>%{customdata}", textfont=dict(size=15),
        hovertemplate="<b>%{label}</b><br>%{customdata}<br>Size: Rs %{value:,.0f}<extra></extra>",
        pathbar=dict(visible=False), tiling=dict(pad=2)))
    fig.update_layout(height=560, margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor="rgba(0,0,0,0)")
    return fig
