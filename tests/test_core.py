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
