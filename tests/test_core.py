import pytest

from core.formatting import format_inr
from core.trading import Portfolio, TradingError


def test_indian_format():
    assert format_inr(100000) == "Rs 1,00,000.00"
    assert format_inr(1234567.5) == "Rs 12,34,567.50"
    assert format_inr(999) == "Rs 999.00"
    assert format_inr(-2500) == "-Rs 2,500.00"
    assert format_inr(None) == "Rs --"


def test_buy_weighted_average_and_cash():
    p = Portfolio()
    p.buy("A.NS", 10, 100)
    p.buy("A.NS", 10, 200)
    assert p.holdings["A.NS"] == {"quantity": 20, "avg_price": 150}
    assert p.balance == 100000 - 3000


def test_sell_pnl_and_partial_keeps_average():
    p = Portfolio()
    p.buy("A.NS", 10, 100)
    order = p.sell("A.NS", 4, 120)
    assert order["pnl"] == 80
    assert p.holdings["A.NS"] == {"quantity": 6, "avg_price": 100}
    p.sell("A.NS", 6, 90)
    assert "A.NS" not in p.holdings


def test_rules_are_enforced():
    p = Portfolio()
    with pytest.raises(TradingError):
        p.buy("A.NS", 1000, 1000)      # too expensive
    with pytest.raises(TradingError):
        p.sell("A.NS", 1, 100)         # not owned
    with pytest.raises(TradingError):
        p.buy("A.NS", 0, 100)          # bad quantity


def test_save_and_load(tmp_path):
    path = str(tmp_path / "p.json")
    p = Portfolio()
    p.buy("A.NS", 5, 100)
    p.save(path)
    q = Portfolio.load(path)
    assert q.balance == p.balance and q.holdings == p.holdings and len(q.order_history) == 1
    assert Portfolio.load(str(tmp_path / "missing.json")).balance == 100000


def test_holdings_table_and_export(tmp_path):
    p = Portfolio()
    p.buy("A.NS", 10, 100)
    df = p.holdings_table({"A.NS": 110})
    assert df.loc[0, "P&L"] == 100 and round(df.loc[0, "P&L %"], 1) == 10.0
    assert p.total_value({"A.NS": 110}) == 100000 + 100
    assert p.export_orders_csv(str(tmp_path / "o.csv")) is True
    assert Portfolio().export_orders_csv(str(tmp_path / "x.csv")) is False


def test_deposited_tracks_added_funds_and_profit(tmp_path):
    p = Portfolio()
    p.add_funds(5000)
    assert p.deposited == 105000 and p.balance == 105000
    path = str(tmp_path / "p.json")
    p.save(path)
    assert Portfolio.load(path).deposited == 105000
    # old save files (without the field) still load
    assert Portfolio.from_dict({"balance": 500}).deposited == 100000


def test_custom_starting_capital_is_validated():
    from core.trading import check_capital
    assert check_capital(500000) == 500000.0
    for bad in (0, 999, 1e9, None):
        with pytest.raises(TradingError):
            check_capital(bad)
    p = Portfolio(balance=250000)
    assert p.balance == 250000 and p.deposited == 250000
    p.buy("A.NS", 10, 100)
    assert round(p.total_value({"A.NS": 100}) - p.deposited, 2) == 0   # profit measured against chosen capital


# ---------------- futures and options ----------------
def test_future_long_profit_and_margin_roundtrip():
    p = Portfolio(balance=100000)
    pos = p.open_future("A.NS", "2026-10-27", "LONG", 2, 1000.0, 50, 0.15)
    assert p.balance == 100000 - 0.15 * 1000 * 50 * 2            # margin blocked
    pnl = p.close_future(pos["id"], 1010.0)
    assert pnl == (1010 - 1000) * 50 * 2
    assert p.balance == 100000 + pnl and p.derivatives == []


def test_future_short_profits_when_price_falls():
    p = Portfolio(balance=100000)
    pos = p.open_future("A.NS", "2026-10-27", "SHORT", 1, 1000.0, 50, 0.15)
    assert p.close_future(pos["id"], 980.0) == 20 * 50


def test_future_loss_beyond_margin_is_capped_and_cash_checked():
    p = Portfolio(balance=100000)
    pos = p.open_future("A.NS", "2026-10-27", "LONG", 1, 1000.0, 50, 0.15)     # margin 7,500
    p.close_future(pos["id"], 500.0, reason="LIQUIDATED")                      # pnl = -25,000
    assert p.balance == 100000 - 7500                                           # only the margin is lost
    with pytest.raises(TradingError):
        Portfolio(balance=1000).open_future("A.NS", "2026-10-27", "LONG", 1, 1000.0, 50, 0.15)


def test_option_buy_sell_and_expiry_payoff():
    p = Portfolio(balance=100000)
    pos = p.buy_option("A.NS", "2026-10-27", 1000.0, "CALL", 2, 30.0, 50)
    assert p.balance == 100000 - 30 * 50 * 2
    pnl = p.sell_option(pos["id"], 45.0)
    assert pnl == 15 * 50 * 2 and p.derivatives == []
    pos2 = p.buy_option("A.NS", "2026-10-27", 1000.0, "PUT", 1, 20.0, 50)
    p.sell_option(pos2["id"], 0.0, reason="EXPIRED")                            # expires worthless
    assert round(p.balance, 2) == round(100000 + pnl - 20 * 50, 2)
    with pytest.raises(TradingError):
        p.sell_option("nope", 1.0)


def test_derivatives_survive_save_and_load(tmp_path):
    p = Portfolio(balance=100000, name="Asha")
    p.open_future("A.NS", "2026-10-27", "LONG", 1, 1000.0, 50, 0.15)
    p.buy_option("B.NS", "2026-10-27", 500.0, "PUT", 1, 10.0, 100)
    q = Portfolio.from_dict(p.to_dict())
    assert q.name == "Asha" and len(q.derivatives) == 2 and q.balance == p.balance
    assert Portfolio.from_dict({"balance": 5}).derivatives == []                # old saves still load
