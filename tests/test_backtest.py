import numpy as np
import pandas as pd

from core import backtest as bt


def prices(values, start="2018-01-01"):
    return pd.Series(values, index=pd.bdate_range(start, periods=len(values)))


def test_steady_uptrend_matches_buy_and_hold():
    close = prices(np.linspace(100, 400, 2000))
    r = bt.run_backtest(close, cost_pct=0)
    s, b = r["stats"]["Strategy"], r["stats"]["Buy and hold"]
    assert abs(s["total_return"] - b["total_return"]) < 0.01     # always invested
    assert r["trades"] == 0


def test_not_enough_history_returns_none():
    assert bt.run_backtest(prices(np.linspace(100, 200, 300))) is None


def test_crash_is_avoided_by_the_rule():
    close = prices(np.concatenate([np.linspace(100, 300, 1200), np.linspace(300, 100, 400), np.full(400, 100.0)]))
    r = bt.run_backtest(close, years=5, cost_pct=0)
    assert r["sells"].size >= 1
    assert r["stats"]["Strategy"]["max_drawdown"] > r["stats"]["Buy and hold"]["max_drawdown"]


def test_no_lookahead():
    close = prices(np.concatenate([np.full(1500, 100.0), [100.0, 100.0], np.linspace(100, 300, 200)]))
    r = bt.run_backtest(close, years=5, cost_pct=0)
    assert r["equity"]["Strategy"].iloc[-1] < r["equity"]["Buy and hold"].iloc[-1]


def test_costs_reduce_results():
    close = prices(np.concatenate([np.linspace(100, 300, 1200), np.linspace(300, 100, 400), np.full(400, 100.0)]))
    free = bt.run_backtest(close, cost_pct=0)["stats"]["Strategy"]["final_value"]
    costly = bt.run_backtest(close, cost_pct=1.0)["stats"]["Strategy"]["final_value"]
    assert costly < free


def test_every_strategy_runs_on_real_looking_data():
    rng = np.random.default_rng(3)
    close = prices(100 * np.exp(np.cumsum(rng.normal(0.0003, 0.015, 2000))))
    for key in ["ma_cross", "rsi", "macd", "bollinger"]:
        r = bt.run_backtest(close, key)
        assert r is not None and r["stats"]["Strategy"]["final_value"] > 0
        assert "percentage points" in bt.verdict(r)


def test_bootstrap_shapes_and_fairness():
    rng = np.random.default_rng(1)
    r = rng.normal(0.0005, 0.01, 1000)
    out = bt.bootstrap_test(r, r, n_paths=500, seed=2)
    assert out["strategy_final"].shape == (500,)
    assert np.allclose(out["strategy_final"], out["hold_final"])      # same returns -> same outcomes
    assert (out["strategy_worst"] <= 0).all()
    again = bt.bootstrap_test(r, r, n_paths=500, seed=2)
    assert np.array_equal(out["strategy_final"], again["strategy_final"])
