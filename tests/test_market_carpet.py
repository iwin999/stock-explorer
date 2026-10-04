"""The market carpet must always build, whatever shape the data from Yahoo is in."""
import copy

import pytest

from core import market_carpet as mc

BASE = mc.load_snapshot()


def _builds(data):
    for metric in mc.METRICS:
        table = mc.sector_table(data, metric)
        mc.carpet(data, metric).to_json()                         # the real chart object, serialised like Streamlit does
        if len(table):
            key = table["Key"].iloc[0]
            mc.carpet(data, metric, key).to_json()
            mc.company_table(data, key, metric)


def test_snapshot_exists_and_covers_the_industries():
    assert BASE and len(BASE["sectors"]) >= 8
    for info in BASE["sectors"].values():
        assert info["companies"] and info["listed"]["NSE"] >= 0


def test_carpet_builds_from_the_saved_snapshot():
    _builds(BASE)


@pytest.mark.parametrize("damage", ["no performance", "nan performance", "no prices", "zero size", "one industry"])
def test_carpet_survives_incomplete_data(damage):
    data = copy.deepcopy(BASE)
    companies = [c for s in data["sectors"].values() for c in s["companies"]]
    if damage == "no performance":
        for c in companies: c["day"] = c["ma50"] = c["ma200"] = None
    elif damage == "nan performance":
        for c in companies: c["day"] = float("nan")
    elif damage == "no prices":
        for c in companies: c["price"] = None
    elif damage == "zero size":
        companies[0]["cap"] = 0.0
    else:
        data["sectors"] = dict(list(data["sectors"].items())[:1])
    _builds(data)


def test_nse_and_bse_listings_of_one_company_are_not_counted_twice():
    nse = [{"symbol": "ONGC.NS", "name": "Oil and Natural Gas Corporation"}]
    bse = [{"symbol": "ONGC.BO", "name": "Oil and Natural Gas Corporatio"}, {"symbol": "TINYCO.BO", "name": "Tiny Co"}]
    merged = mc.merge_exchanges(nse, bse)
    assert [c["symbol"] for c in merged] == ["ONGC.NS", "TINYCO.BO"]


def test_weighted_performance_favours_bigger_companies():
    cs = [{"cap": 90.0, "day": 1.0}, {"cap": 10.0, "day": -9.0}, {"cap": 5.0, "day": None}]
    assert round(mc.weighted(cs, "day"), 6) == 0.0 and mc.weighted([{"cap": 1.0, "day": None}], "day") is None
