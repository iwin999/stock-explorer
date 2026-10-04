import numpy as np
import pandas as pd
import pytest

from core import fundamentals as fd, fusion as fu


def series(values, start="2022-01-03"):
    return pd.Series(values, index=pd.bdate_range(start, periods=len(values)))


# ---------------- the chapter's rules ----------------
def test_winners_circle_groups_follow_the_venn_diagram():
    assert fu.group_of(True, True, True) == 1        # trending + both qualities
    assert fu.group_of(True, True, False) == 2       # trending + one quality
    assert fu.group_of(True, False, True) == 2
    assert fu.group_of(True, False, False) == 3      # trending, neither
    for q in (True, False):
        for v in (True, False):
            assert fu.group_of(False, q, v) == 4     # not trending = watchlist, whatever the fundamentals


def test_technical_overlay_confirms_delays_or_rejects():
    assert fu.verdict_for(1, True, True)[0] == "Confirm" and fu.verdict_for(1, True, True)[2] is False
    assert fu.verdict_for(3, False, False)[2] is True                      # trend without fundamentals = divergence
    label, _, divergence = fu.verdict_for(4, True, True)
    assert label.startswith("Delay") and divergence is True                # good fundamentals, no trend yet
    label, _, divergence = fu.verdict_for(4, False, False)
    assert label.startswith("Reject") and divergence is False


def test_trend_stage_and_circle():
    rising = series(np.linspace(100, 300, 400))
    falling = series(np.linspace(300, 100, 400))
    flat_bench = series(np.full(400, 100.0))
    up = fu.technical_table(rising, flat_bench).iloc[-1]
    assert up["stage"] == 3 and bool(up["in_circle"]) is True
    down = fu.technical_table(falling, flat_bench).iloc[-1]
    assert down["stage"] == 0 and bool(down["in_circle"]) is False
    strong_bench = series(np.linspace(100, 900, 400))                       # the market rises faster than the stock
    assert bool(fu.technical_table(rising, strong_bench).iloc[-1]["in_circle"]) is False   # not outperforming


def test_results_are_only_used_after_they_were_public():
    record = {"financial": False, "annual": {
        "2024-03-31": {"revenue": 100.0, "net_income": 10.0, "operating_income": 20.0, "eps": 1.0, "equity": 50.0, "debt": 25.0, "shares": 10.0},
        "2025-03-31": {"revenue": 120.0, "net_income": 15.0, "operating_income": 30.0, "eps": 1.5, "equity": 60.0, "debt": 30.0, "shares": 10.0}}}
    assert fu.fundamentals_asof(record, "2025-06-01", 30.0) is None or fu.fundamentals_asof(record, "2025-06-01", 30.0)["as_of_year"] == "2024-03-31"
    early = fu.fundamentals_asof(record, "2025-05-15", 30.0)      # 45 days after year end: FY2025 not public yet
    assert early is None or early["as_of_year"] != "2025-03-31"
    later = fu.fundamentals_asof(record, "2025-06-20", 30.0)      # 81 days after year end: public
    assert later["as_of_year"] == "2025-03-31"
    assert later["revenue_growth"] == pytest.approx(0.2) and later["earnings_growth"] == pytest.approx(0.5)
    assert later["op_margin"] == pytest.approx(0.25) and later["roe"] == pytest.approx(0.25)
    assert later["debt_equity"] == pytest.approx(0.5) and later["pe"] == pytest.approx(20.0) and later["pb"] == pytest.approx(5.0)


def test_special_cases_losses_and_banks():
    base = {"revenue": 100.0, "net_income": -5.0, "operating_income": 1.0, "eps": -0.5, "equity": 50.0, "debt": 25.0, "shares": 10.0}
    loss = fu.fundamentals_asof({"financial": False, "annual": {"2025-03-31": base}}, "2025-09-01", 30.0)
    assert loss["pe"] == np.inf                                            # loss-making = worst valuation
    bank = fu.fundamentals_asof({"financial": True, "annual": {"2025-03-31": base}}, "2025-09-01", 30.0)
    assert np.isnan(bank["debt_equity"])                                   # debt ratios are skipped for lenders


def test_scores_rank_better_companies_higher():
    table = pd.DataFrame({
        "revenue_growth": [0.30, 0.10, -0.05], "earnings_growth": [0.40, 0.10, -0.20], "roe": [0.25, 0.12, 0.02],
        "op_margin": [0.30, 0.15, 0.05], "debt_equity": [0.1, 0.8, 2.0], "pe": [10.0, 25.0, 60.0], "pb": [1.5, 3.0, 9.0]},
        index=["GOOD", "MID", "WEAK"])
    out = fu.score_fundamentals(table)
    assert out.loc["GOOD", "F"] > out.loc["MID", "F"] > out.loc["WEAK", "F"]
    assert out.loc["GOOD", "V"] > out.loc["MID", "V"] > out.loc["WEAK", "V"]      # cheaper = better valuation score
    assert out["F"].between(0, 100).all()


def test_expectancy_matches_the_formula():
    trades = [0.10, 0.10, -0.05, -0.05, -0.05]                  # 40% win rate, +10% wins, -5% losses
    e = fu.expectancy(trades)
    assert e["win_rate"] == pytest.approx(0.4) and e["avg_win"] == pytest.approx(0.10) and e["avg_loss"] == pytest.approx(0.05)
    assert e["expectancy"] == pytest.approx(0.4 * 0.10 - 0.6 * 0.05)
    assert fu.expectancy([]) is None


# ---------------- on the real saved data ----------------
@pytest.fixture(scope="module")
def real():
    funds = fd.load()
    if len(funds["companies"]) < 100:
        pytest.skip("fundamentals file not downloaded")
    prices, bench = fu.load_universe()
    if bench is None or len(prices) < 100:
        pytest.skip("price files not downloaded")
    return funds, prices, bench, fu.build_technicals(prices, bench)


def test_real_data_classification_is_consistent(real):
    funds, prices, bench, tech = real
    table = fu.classify(pd.Timestamp("2026-09-30"), tech, funds)
    judged = table[table["group"].notna()]
    assert len(judged) >= 80
    g1 = judged[judged["group"] == 1]
    assert g1["in_circle"].all() and (g1["F"] >= 50).all() and (g1["V"] >= 50).all()
    assert not judged[judged["group"] == 4]["in_circle"].any()
    assert (judged[judged["group"] == 3]["quality_ok"] == False).all()          # noqa: E712


def test_real_backtest_never_trades_before_the_signal_is_known(real):
    funds, prices, bench, tech = real
    res = fu.run_fusion_backtest(prices, bench, tech, funds)
    assert res is not None and res["rebalances"] >= 30
    assert res["start"] >= pd.Timestamp("2023-06-01")                          # no fundamentals exist before this
    closes = pd.DataFrame(prices).sort_index().ffill()
    for signal_day, trade_day in zip(fu.month_starts(closes.index, res["execution_dates"][0] - pd.Timedelta(days=5), closes.index[-1])[:5],
                                     res["execution_dates"][:5]):
        assert trade_day > signal_day                                          # traded the day AFTER the rating
    assert set(res["curves"].columns) == {"Group 1 only", "Groups 1 and 2", "All companies (equal weight)", "Nifty 50"}
    assert (res["curves"].iloc[0] > 90000).all() and res["avg_holdings"]["Group 1 only"] > 0
