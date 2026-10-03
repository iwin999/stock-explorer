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


def test_flat_prices_give_flat_paths():
    paths = sim.simulate(pd.Series([100.0] * 300), seed=1)
    assert np.allclose(paths, 100)
