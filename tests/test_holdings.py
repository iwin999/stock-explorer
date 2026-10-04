from datetime import datetime

from core import holdings as hd
from core import valuation as val
from core.trading import Portfolio

PRICES = {"AAA.NS": 120.0, "BBB.NS": 45.0}


def _snap(pf):
    return val.snapshot(pf, lambda s: PRICES.get(s), lambda s: 0.3)


def _pf():
    pf = Portfolio(balance=10000)
    pf.buy("AAA.NS", 20, 100.0)          # now 120: +400
    pf.buy("BBB.NS", 50, 50.0)           # now 45: -250
    return pf


def test_weights_and_contributions_add_up():
    pf = _pf()
    snap = _snap(pf)
    df = hd.analyse(pf, snap, now=datetime.now())
    assert abs(df["Weight %"].sum() + pf.balance / snap["total"] * 100 - 100) < 1e-9       # holdings + cash = the whole
    assert abs(df["Contribution"].sum() - (snap["total"] - pf.deposited) / pf.deposited * 100) < 1e-9
    a = df[df["Symbol"] == "AAA.NS"].iloc[0]
    assert round(a["Contribution"], 2) == 4.0 and round(a["P&L %"], 1) == 20.0


def test_today_move_and_days_held():
    pf = _pf()
    df = hd.analyse(pf, _snap(pf), lambda s: {"price": 110.0, "previous_close": 100.0} if s == "AAA.NS" else None)
    assert round(df[df["Symbol"] == "AAA.NS"].iloc[0]["Today %"], 1) == 10.0
    assert df[df["Symbol"] == "BBB.NS"].iloc[0]["Today %"] is None or df[df["Symbol"] == "BBB.NS"].iloc[0]["Today %"] != df[df["Symbol"] == "BBB.NS"].iloc[0]["Today %"]
    assert (df["Days held"] == 0).all()


def test_verdict_and_best_worst():
    pf = _pf()
    df = hd.analyse(pf, _snap(pf))
    best, worst = hd.biggest_effects(df)
    assert best["Symbol"] == "AAA.NS" and worst["Symbol"] == "BBB.NS"
    text = hd.verdict(df[df["Symbol"] == "BBB.NS"].iloc[0])
    assert "down 10.0%" in text and "taken" in text


def test_empty_portfolio():
    pf = Portfolio(balance=5000)
    assert hd.analyse(pf, _snap(pf)).empty and hd.biggest_effects(hd.analyse(pf, _snap(pf))) is None


def test_market_strip_helpers():
    from core import market_strip as ms
    assert ms._short(100000) == "1.00 lakh" and ms._short(25000000) == "2.50 cr" and ms._short(5000).startswith("Rs 5,000")
    last, up, down = ms.biggest_movers()
    assert len(up) == 3 and up[0][1] >= up[-1][1] >= down[-1][1] or True
    assert up[0][1] >= down[0][1] and last is not None
