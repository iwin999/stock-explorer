from datetime import datetime

from core import builder as b, derivatives as dv, instruments as ins
from core.trading import Portfolio

NOW = datetime(2026, 10, 5, 11, 0, tzinfo=dv.IST)
PRICES = {"RELIANCE.NS": 1000.0, "TCS.NS": 3000.0, "GOLDBEES.NS": 100.0, "EBBETF0430.NS": 1500.0, "^NSEI": 22000.0}
SIG = {"RELIANCE.NS": 0.25, "^NSEI": 0.15}


def plan(alloc, picks, cash=1000000):
    return b.plan_portfolio(cash, alloc, picks, PRICES, SIG, NOW)


def test_cash_instruments_split_equally_and_leave_remainder_as_cash():
    p = plan({ins.STOCKS: 40}, {ins.STOCKS: ["RELIANCE.NS", "TCS.NS"]})
    by = {o["symbol"]: o for o in p["orders"]}
    assert by["RELIANCE.NS"]["qty"] == 200 and by["TCS.NS"]["qty"] == 66      # 200,000 each; 200,000/3000 = 66
    assert abs(p["spent"] + p["left"] - 1000000) < 1e-6 and p["left"] > 600000


def test_futures_use_budget_as_margin_and_options_as_premium():
    p = plan({ins.FUTURES: 30, ins.OPTIONS: 10},
             {ins.FUTURES: [("RELIANCE.NS", "LONG")], ins.OPTIONS: [("^NSEI", "CALL")]})
    kinds = {o["kind"]: o for o in p["orders"]}
    fut, opt = kinds["FUT"], kinds["OPT"]
    assert fut["cost"] <= 300000 and fut["side"] == "LONG" and fut["expiry"] == dv.expiry_dates(NOW, 1)[0]
    assert opt["cost"] <= 100000 and opt["strike"] > 21000 and opt["qty"] >= 1


def test_class_without_picks_or_too_small_budget_is_skipped_politely():
    p = plan({ins.BONDS: 20, ins.STOCKS: 1}, {ins.STOCKS: ["TCS.NS"]}, cash=10000)
    assert p["orders"] == [] and len(p["skipped"]) == 2 and p["left"] == 10000


def test_missing_price_is_skipped():
    p = plan({ins.STOCKS: 50}, {ins.STOCKS: ["UNKNOWN.NS"]})
    assert p["orders"] == [] and "no price" in p["skipped"][0]


def test_execute_plan_places_everything_and_keeps_cash_consistent():
    pf = Portfolio(balance=1000000)
    p = plan({ins.STOCKS: 25, ins.ETFS: 15, ins.BONDS: 20, ins.FUTURES: 10, ins.OPTIONS: 5},
             {ins.STOCKS: ["RELIANCE.NS"], ins.ETFS: ["GOLDBEES.NS"], ins.BONDS: ["EBBETF0430.NS"],
              ins.FUTURES: [("^NSEI", "SHORT")], ins.OPTIONS: [("RELIANCE.NS", "PUT")]})
    assert b.execute_plan(pf, p) == len(p["orders"]) == 5
    assert len(pf.holdings) == 3 and len(pf.derivatives) == 2
    assert abs(pf.balance - p["left"]) < 1e-6                   # cash left = plan's leftover
