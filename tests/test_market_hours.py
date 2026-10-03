from datetime import datetime

from core.market_hours import IST, is_market_open, status_message


def at(y, m, d, h, mi):
    return datetime(y, m, d, h, mi, tzinfo=IST)


def test_open_during_trading_hours():
    assert is_market_open(at(2026, 10, 5, 9, 15))      # Monday, opening bell
    assert is_market_open(at(2026, 10, 7, 12, 0))      # Wednesday midday
    assert status_message(at(2026, 10, 7, 12, 0)) == "Market open"


def test_closed_outside_hours_and_weekends():
    assert not is_market_open(at(2026, 10, 5, 9, 14))
    assert not is_market_open(at(2026, 10, 5, 15, 30))  # closing bell
    assert not is_market_open(at(2026, 10, 3, 11, 0))   # Saturday
    assert "Monday" in status_message(at(2026, 10, 3, 11, 0))
    assert "today" in status_message(at(2026, 10, 5, 8, 0))
    assert "tomorrow" in status_message(at(2026, 10, 5, 17, 0))
