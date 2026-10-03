import numpy as np
import pandas as pd

from core import simulation as sim


def make_prices(sigma, n=300, seed=1):
    rng = np.random.default_rng(seed)
    return pd.Series(100 * np.exp(np.cumsum(rng.normal(0, sigma, n))))


def test_shape_and_start():
    close = make_prices(0.01)
    paths = sim.simulate(close, 30, n_paths=500, seed=1)
    assert paths.shape == (500, sim.calendar_to_trading_days(30) + 1)
    assert np.allclose(paths[:, 0], close.iloc[-1])


def test_repeatable_with_seed():
    close = make_prices(0.01)
    assert np.array_equal(sim.simulate(close, seed=5), sim.simulate(close, seed=5))
    assert not np.array_equal(sim.simulate(close, seed=5), sim.simulate(close, seed=6))


def test_calmer_stock_has_narrower_range():
    calm, wild = make_prices(0.005), make_prices(0.03)
    lc, hc = sim.likely_range(sim.simulate(calm, seed=1))
    lw, hw = sim.likely_range(sim.simulate(wild, seed=1))
    assert (hc - lc) / calm.iloc[-1] < (hw - lw) / wild.iloc[-1]


def test_range_contains_roughly_70_percent():
    paths = sim.simulate(make_prices(0.02), 30, n_paths=20000, seed=3)
    low, high = sim.likely_range(paths, 0.70)
    inside = ((paths[:, -1] >= low) & (paths[:, -1] <= high)).mean()
    assert 0.68 < inside < 0.72


def test_outcome_chances_add_up():
    paths = sim.simulate(make_prices(0.02), 30, n_paths=5000, seed=2)
    c = sim.outcome_chances(paths)
    assert abs(c["up"] + c["down"] - 1) < 1e-9
    assert abs(c["big_up"] + c["flat"] + c["big_down"] - 1) < 1e-9


def test_rising_history_tilts_chances_up_but_neutral_does_not():
    rising = pd.Series(100 * np.exp(np.cumsum(np.full(300, 0.002))))
    rising = rising * np.exp(np.random.default_rng(1).normal(0, 0.01, 300))  # add noise
    with_trend = sim.outcome_chances(sim.simulate(rising, 30, n_paths=5000, seed=1))["up"]
    neutral = sim.outcome_chances(sim.simulate(rising, 30, n_paths=5000, seed=1, include_trend=False))["up"]
    assert with_trend > 0.6 and 0.4 < neutral < 0.55


def test_flat_prices_give_flat_paths():
    paths = sim.simulate(pd.Series([100.0] * 300), seed=1)
    assert np.allclose(paths, 100)


def test_strategy_outcomes_shapes_and_sanity():
    close = make_prices(0.015, n=600)
    paths = sim.simulate(close, 30, n_paths=800, seed=3)
    for key in ["ma_cross", "rsi", "macd", "bollinger"]:
        out = sim.strategy_outcomes(close, key, paths)
        assert out["strategy"].shape == (800,) == out["hold"].shape
        assert 0 <= out["chance_gain"] <= 1 and 0 <= out["invested"] <= 1
        assert out["poor"] <= out["median"] <= out["good"]


def test_always_invested_rule_equals_holding_without_costs(monkeypatch):
    from core import strategies
    always = strategies.Strategy("always", "x", "x", lambda p: np.ones(p.shape, dtype=int), 1, "x", "x")
    monkeypatch.setitem(strategies.STRATEGIES, "always", always)
    close = make_prices(0.01, n=600)
    paths = sim.simulate(close, 30, n_paths=300, seed=4)
    out = sim.strategy_outcomes(close, "always", paths, cost_pct=0)
    assert np.allclose(out["strategy"], out["hold"])
