import numpy as np
import pandas as pd

from core import ratios as R


def test_none_when_too_short():
    assert R.summary(pd.Series([0.01] * 5)) is None


def test_steady_returns_have_no_sharpe():
    s = R.summary(pd.Series([0.001] * 200))
    assert s["sharpe"] is None and s["max_drawdown"] == 0


def test_known_drawdown_and_total_return():
    r = pd.Series([0.1, -0.5, 0.1] + [0.0] * 60)
    s = R.summary(r)
    assert abs(s["max_drawdown"] - (-0.5)) < 1e-9
    assert abs(s["total_return"] - (1.1 * 0.5 * 1.1 - 1)) < 1e-9


def test_beta_of_double_market_is_two_and_alpha_zero():
    rng = np.random.default_rng(0)
    idx = pd.bdate_range("2022-01-01", periods=500)
    m = pd.Series(rng.normal(0.0004, 0.01, 500), index=idx)
    s = R.summary(2 * m, m, risk_free=0.0)
    assert abs(s["beta"] - 2) < 1e-9 and abs(s["alpha"]) < 1e-9
    assert abs(s["correlation"] - 1) < 1e-9


def test_describe_never_crashes_and_handles_missing():
    s = R.summary(pd.Series(np.random.default_rng(1).normal(0.0005, 0.01, 400)))
    for key in ["cagr", "volatility", "max_drawdown", "var95", "sharpe", "sortino", "calmar",
                "treynor", "beta", "alpha", "information", "correlation", "win_rate"]:
        value, text = R.describe(key, s)
        assert isinstance(value, str) and isinstance(text, str)
    assert R.describe("beta", s)[0] == "n/a"     # no benchmark given


def test_colour_scales_put_good_and_bad_in_the_right_place():
    from core import ratios
    assert ratios.rate("sharpe", 2.5)["label"] == "Excellent" and ratios.rate("sharpe", -1)["label"] == "Poor"
    assert ratios.rate("volatility", 0.12)["pos"] > ratios.rate("volatility", 0.45)["pos"]      # low volatility is the green end
    assert ratios.rate("max_drawdown", -0.05)["label"] == "Excellent" and ratios.rate("max_drawdown", -0.55)["label"] == "Poor"
    assert ratios.rate("beta", 1.4)["label"] == "Swings more than the market" and ratios.rate("beta", 1.4)["better"] == "neutral"
    assert ratios.rate("sharpe", None) is None and ratios.rate("nonsense", 1) is None
    for key in ratios.SCALES:
        assert 0 <= ratios.rate(key, 99)["pos"] <= 1 and 0 <= ratios.rate(key, -99)["pos"] <= 1
