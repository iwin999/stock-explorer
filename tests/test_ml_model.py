"""The machine-learning estimate: no peeking, a sensible probability, a saved and honestly-tested model, and the panel pieces."""
import numpy as np
import pandas as pd

from core import daily_check as dc
from core import daily_visuals as vis
from core import ml_model as ml
from tests.test_cmt_strategies import _prices

from datetime import datetime


def test_features_use_only_data_up_to_each_day():
    hist, bench = _prices(drift=0.001)
    a = ml.features_frame(hist, bench)
    h2 = hist.copy()
    h2.iloc[-1, h2.columns.get_loc("Close")] *= 1.3
    h2.iloc[-1, h2.columns.get_loc("High")] *= 1.3
    b = ml.features_frame(h2, bench)
    assert a.iloc[:-1].fillna(9).equals(b.iloc[:-1].fillna(9)) and list(a.columns) == ml.FEATURES


def test_logistic_regression_learns_a_simple_pattern():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(4000, 3))
    y = (X[:, 0] + 0.3 * rng.normal(size=4000) > 0).astype(float)
    Xs, mean, std = ml.standardise(X)
    w, b = ml.fit(Xs, y)
    assert w[0] > 0.5 and abs(w[1]) < 0.2 and abs(w[2]) < 0.2


def test_the_saved_model_is_honest_and_gives_a_probability():
    model = ml.load_model()
    assert model and model["features"] == ml.FEATURES and model["companies"] > 100
    held = model["tested"]["last 30% of dates (held back)"]
    assert 0.4 < held["accuracy"] < 0.6                                      # no claim of a magic edge
    hist, bench = _prices(drift=0.002)
    out = ml.estimate(hist, bench, model)
    assert 0 < out["p_up"] < 1 and out["lean"] in ("Up", "Down", "None") and len(out["top"]) == 3
    assert ml.estimate(hist.iloc[:100], bench, model) is None


def test_the_dashboard_panel_has_six_indicators_with_a_zscore_and_no_votes_tag_and_a_learn_strip():
    hist, bench = _prices(drift=0.002)
    plan = dc.plan(hist, datetime(2026, 10, 14, 13, 0), live_price=float(hist["Close"].iloc[-1]), market_open=True)
    plain = dc.evaluate(plan["basis"], plan)
    styled = dc.evaluate(plan["basis"], plan, scales=True)
    assert "Z-score" not in [v["name"] for v in plain["votes"]]               # the real site's Daily check is unchanged
    names = {v["name"]: v for v in styled["votes"]}
    assert "Z-score" in names and names["Z-score"]["gauge"]["kind"] == "grade"
    from core.terminal_ui import PANEL_INDICATORS
    assert all(n in names for n in PANEL_INDICATORS) and len(PANEL_INDICATORS) == 6
    card = vis.terminal_card(names["RSI (speed)"])
    assert "VOTES" not in card and "context" not in card and "title=" in card
    strip = vis.learn_strip()
    assert strip.count('class="lh"') == len(vis.HINTS) >= 14 and "Fusion stage" in strip and "ML model" in strip


def test_the_prediction_bar_shows_the_ml_box_next_to_the_call():
    hist, bench = _prices(drift=0.002)
    plan = dc.plan(hist, datetime(2026, 10, 14, 13, 0), live_price=float(hist["Close"].iloc[-1]), market_open=True)
    result = dc.evaluate(plan["basis"], plan)
    est = ml.estimate(hist, bench)
    html = vis.prediction_panel(result, "Live", est)
    assert "ML model reading" in html and "modelled chance of a higher close" in html and "pp-pbar" in html
    assert "ML model reading" not in vis.prediction_panel(result, "Live")
