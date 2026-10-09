"""Dark mode: charts get a dark skin, the site gets dark CSS only when the switch is on, and nothing errors in either mode."""
import tempfile
from unittest import mock

import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest

from core import accounts as acc
from core import market_carpet as mc
from core.charts import NAVY, TERMINAL_BG, price_chart, skin

import os
APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")


def _hist():
    idx = pd.bdate_range("2024-01-01", periods=300)
    c = pd.Series(100 + np.cumsum(np.random.default_rng(1).normal(0, 1, 300)), index=idx)
    return pd.DataFrame({"Open": c, "High": c + 1, "Low": c - 1, "Close": c, "Volume": 1_000_000.0}, index=idx)


def test_dark_skin_darkens_background_and_lifts_navy_lines():
    fig = skin(price_chart(_hist(), "TEST.NS", "Test"), True)
    assert fig.layout.paper_bgcolor == TERMINAL_BG
    colours = [getattr(t.line, "color", None) for t in fig.data if hasattr(t, "line")]
    assert NAVY not in colours                      # the 200-day line is lightened so it shows on dark


def test_light_skin_changes_nothing():
    fig = price_chart(_hist(), "TEST.NS", "Test")
    before = fig.to_json()
    assert skin(fig, False).to_json() == before


def test_carpet_gets_a_dark_colour_scale():
    data = mc.load_snapshot()
    fig = skin(mc.carpet(data, "day"), True)
    assert fig.data[0].marker.colorscale[2][1] == "#2a3245"


def _signed_in():
    store = acc.FileStore(tempfile.mkdtemp())
    acc.create_account(store, "Moody", 100000)
    app = AppTest.from_file(APP, default_timeout=240)
    app.query_params["user"] = "Moody"
    return store, app


def test_site_switch_turns_dark_css_on_and_sets_the_chart_switch():
    store, app = _signed_in()
    with mock.patch("core.trading_ui.get_store", lambda: store), mock.patch("core.portfolio_ui.get_store", lambda: store):
        app.run()
        assert not app.exception
        assert not any("#0b1220 !important" in m.value for m in app.markdown)
        app.toggle(key="dark_site").set_value(True).run()
        assert not app.exception
        assert any("#0b1220 !important" in m.value for m in app.markdown)
        assert app.toggle(key="dark_chart").value is True
        app.toggle(key="dark_chart").set_value(False).run()          # the chart can then be changed on its own
        assert not app.exception and app.toggle(key="dark_site").value is True
