import numpy as np
import pandas as pd

from core import indicators as ind, strategies as st


def prices():
    rng = np.random.default_rng(7)
    return pd.Series(100 * np.exp(np.cumsum(rng.normal(0.0004, 0.015, 600))))


def test_numpy_indicators_match_the_pandas_ones():
    c = prices()
    x = c.to_numpy()[None, :]
    pairs = [(st._sma(x, 50)[0], ind.sma(c, 50)),
             (st._rsi(x)[0], ind.rsi(c)),
             (st._ema(x, 12)[0] - st._ema(x, 26)[0], ind.macd(c)[0]),
             (st._bollinger(x)[2][0], ind.bollinger(c)[2]),
             (st._bollinger(x)[1][0], ind.bollinger(c)[1])]
    for mine, theirs in pairs:
        theirs = theirs.to_numpy()
        both = ~np.isnan(mine) & ~np.isnan(theirs)
        assert both.sum() > 400 and np.allclose(mine[both], theirs[both])
        assert (np.isnan(mine) == np.isnan(theirs)).all()


def test_rules_return_zero_one_arrays_for_many_paths_at_once():
    paths = np.vstack([prices().to_numpy(), prices().to_numpy() * 1.5])
    for rule in st.STRATEGIES.values():
        pos = rule.fn(paths)
        assert pos.shape == paths.shape and set(np.unique(pos)) <= {0, 1}
        assert np.array_equal(pos[0], rule.fn(paths[:1])[0])       # paths don't affect each other


def test_every_strategy_has_explanations():
    for rule in st.STRATEGIES.values():
        assert rule.plain.strip() and rule.know_how.strip() and rule.headline.strip()
