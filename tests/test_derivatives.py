import math
from datetime import date, datetime

import pandas as pd

from core import derivatives as d
from core.derivatives import IST


def test_put_call_parity():
    S, K, T, sig = 100.0, 105.0, 0.25, 0.3
    c, p = d.option_price(S, K, T, sig, "CALL"), d.option_price(S, K, T, sig, "PUT")
    assert abs((c - p) - (S - K * math.exp(-d.RISK_FREE * T))) < 1e-9


def test_option_prices_behave_sensibly():
    S, T, sig = 100.0, 0.25, 0.3
    assert d.option_price(S, 90, T, sig, "CALL") > d.option_price(S, 110, T, sig, "CALL")     # lower strike, dearer call
    assert d.option_price(S, 100, T, 0.5, "CALL") > d.option_price(S, 100, T, 0.2, "CALL")    # more volatility, dearer
    assert d.option_price(S, 100, 0.5, sig, "PUT") > d.option_price(S, 100, 0.1, sig, "PUT")  # more time, dearer
    assert d.option_price(120, 100, 0.0, sig, "CALL") == 20 and d.option_price(80, 100, 0.0, sig, "CALL") == 0
    assert d.option_price(80, 100, 0.0, sig, "PUT") == 20


def test_futures_price_grows_with_time():
    assert d.future_price(100, 0) == 100
    assert abs(d.future_price(100, 1) - 100 * math.exp(d.RISK_FREE)) < 1e-9


def test_lot_size_makes_contract_about_two_lakh():
    for spot in [50, 450, 1167, 2800, 22400, 54000]:
        value = spot * d.lot_size(spot)
        assert 0.4 * d.CONTRACT_VALUE < value < 2.5 * d.CONTRACT_VALUE


def test_expiry_is_last_tuesday_and_skips_past_dates():
    assert d.last_tuesday(2026, 10) == date(2026, 10, 27) and d.last_tuesday(2026, 10).weekday() == 1
    now = datetime(2026, 10, 3, 12, 0, tzinfo=IST)
    first = d.expiry_dates(now, 3)
    assert first[0] == date(2026, 10, 27) and len(first) == 3 and first == sorted(first)
    after = datetime(2026, 10, 27, 16, 0, tzinfo=IST)           # after the October expiry closed
    assert d.expiry_dates(after, 1)[0] == date(2026, 11, 24)
    assert d.has_expired(date(2026, 10, 27), after) and not d.has_expired(date(2026, 10, 27), now)


def test_strike_grid_centres_on_price():
    strikes, atm = d.strike_grid(1167.7)
    assert atm in strikes and strikes == sorted(strikes) and len(strikes) == 17
    assert abs(atm - 1167.7) <= d.strike_step(1167.7)


def test_volatility_is_clipped():
    flat = pd.Series([100.0] * 300)
    assert d.volatility_for_pricing(flat) == 0.12
