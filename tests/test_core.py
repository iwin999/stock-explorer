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


def test_created_at_is_saved_and_old_accounts_still_load():
    p = Portfolio(balance=1000, name="Asha", created_at="2026-10-03T15:32:22+00:00")
    assert Portfolio.from_dict(p.to_dict()).created_at == "2026-10-03T15:32:22+00:00"
    assert Portfolio.from_dict({"balance": 5, "name": "Old"}).created_at is None


def test_indian_time_conversion():
    from core.formatting import format_ist
    assert format_ist("2026-10-03T15:32:22+00:00") == "03 Oct 2026, 9:02 PM"
    assert format_ist("2026-10-03T16:37:54+00:00") == "03 Oct 2026, 10:07 PM"
    assert format_ist("2026-10-03T18:30:00Z") == "04 Oct 2026, 12:00 AM"          # crosses midnight
    assert format_ist("2026-10-03T06:30:00") == "03 Oct 2026, 12:00 PM"           # no zone: treated as UTC
    assert format_ist(None) == "not recorded" and format_ist("garbage") == "not recorded"


def test_search_adds_bse_and_other_companies_from_yahoo(monkeypatch):
    from core import companies
    fake = [{"symbol": "SUZLON.NS", "name": "Suzlon Energy Limited"}, {"symbol": "SUZLON.BO", "name": "Suzlon Energy Limited"},
            {"symbol": "RELIANCE.NS", "name": "Reliance Industries Limited"}]
    monkeypatch.setattr(companies, "yahoo_search", lambda q: fake)
    results, source = companies.search("reliance")
    symbols = [r["symbol"] for r in results]
    assert symbols[0] == "RELIANCE.NS" and symbols.count("RELIANCE.NS") == 1          # ours first, no duplicates
    assert "SUZLON.BO" in symbols and "BSE" in source
    assert companies.label("SUZLON.BO").startswith("Suzlon Energy") and companies.label("SUZLON.BO").endswith("(BSE: SUZLON)")
    assert companies.label("RELIANCE.NS") == "Reliance Industries (RELIANCE)"
    from core import instruments as ins
    assert ins.name_of("SUZLON.BO").startswith("Suzlon Energy") and ins.asset_class("SUZLON.BO") == ins.STOCKS


def test_search_still_works_when_yahoo_is_down(monkeypatch):
    from core import companies
    monkeypatch.setattr(companies, "yahoo_search", lambda q: [])
    results, source = companies.search("tata motors")
    assert results and source == "our company list"


def test_every_builtin_company_has_a_bse_twin_that_behaves_like_the_nse_one():
    from core import companies, instruments as ins
    assert len(companies.BSE_OF) == len(companies.COMPANIES)
    for _name, nse, _ in companies.COMPANIES:
        bse = companies.BSE_OF[nse]
        assert bse.endswith(".BO") and companies.to_nse(bse) == nse and companies.twin_of(nse) == bse
        assert ins.asset_class(bse) == ins.STOCKS and ins.name_of(bse) == ins.name_of(nse)
    assert companies.listings("TCS.NS") == ["TCS.NS", "TCS.BO"] and companies.listings("UNKNOWN.NS") == ["UNKNOWN.NS"]
    assert companies.benchmark_for("TCS.BO") == ("^BSESN", "Sensex") and companies.benchmark_for("TCS.NS")[1] == "Nifty 50"
    hits = [r["symbol"] for r in companies.search_local("reliance")]
    assert "RELIANCE.NS" in hits and "RELIANCE.BO" in hits                      # a search shows both listings
    assert "^BSESN" in ins.FNO_UNDERLYINGS and "TCS.BO" in ins.FNO_UNDERLYINGS     # futures and options on the Sensex and BSE shares


def test_bse_listing_falls_back_to_the_nse_saved_prices():
    from core import market_data
    nse, bse = market_data.load_offline("TCS.NS"), market_data.load_offline("TCS.BO")
    assert nse is not None and bse is not None and bse.index[-1] == nse.index[-1]
    assert market_data.load_offline("^BSESN") is not None


def test_search_box_suggestions_cover_the_whole_nse_and_bse():
    from core import companies, universe
    assert len(universe.OPTIONS) > 5000 and len(set(universe.OPTIONS)) == len(universe.OPTIONS)
    assert universe.OPTIONS[:2] == ["RELIANCE.NS", "RELIANCE.BO"]                   # popular companies come first
    labels = [companies.label(s).lower() for s in universe.OPTIONS]
    assert any("suzlon" in x for x in labels) and any("bse:" in x for x in labels) and any("tata" in x for x in labels)
    assert sum(s.endswith(".BO") for s in universe.OPTIONS) > 2000 and sum(s.endswith(".NS") for s in universe.OPTIONS) > 1500
