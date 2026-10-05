"""Stock Explorer - the page itself (app.py runs it inside a safety net).  Run with:  streamlit run app.py

Streamlit re-runs this whole file from top to bottom every time a visitor clicks
something. That is why slow things (downloading prices) are wrapped in
st.cache_data: the second time, the answer comes from memory instantly.
"""
import zlib

import numpy as np
import pandas as pd
import streamlit as st

from core import about, assistant_ui, carpet_ui, universe, market_strip, backtest as bt, fusion_ui, companies, indicators as ind, portfolio_ui, ratios, simulation as sim, trading_ui
from core.charts import (add_fibonacci, backtest_chart, fan_chart, outlook_gauge, outcome_histogram, price_chart,
                         zoom_to_window)
from core.formatting import format_inr
from core.errors import guard
from core.live import live_quote
from core.market_data import get_company_name, get_history_with_source
from core.market_hours import is_market_open, now_ist, status_message
from core.strategies import FUSION_RULE, STRATEGIES, fusion_rule_for
from core.ui import (help_bubble, ratio_scale, callout, know_how_button, metric_with_help, notice, plain_english, setup_page,
                     show_disclaimer, term_row)

setup_page("Stock Explorer")

# ---------- step 1: ask how much virtual money to practise with ----------
if not trading_ui.has_account():
    trading_ui.capital_gate()
    st.stop()


# ---------- cached data loaders ----------
@st.cache_data(ttl=600, show_spinner=False)
def load_history(symbol):
    # Returns (prices, "online"/"offline"/"none", last date). 7 years: 5 to test + 2 to warm up.
    return get_history_with_source(symbol, "7y")


@st.cache_data(ttl=86400, show_spinner=False)
def load_name(symbol):
    # Our own list already has names; only ask Yahoo for tickers we don't know.
    return companies.NAME_BY_SYMBOL.get(symbol) or get_company_name(symbol)


@st.cache_data(ttl=3600, show_spinner=False)
def load_benchmark(index_symbol):
    """The market index's history (Nifty 50 for NSE listings, Sensex for BSE): the yardstick for beta, alpha and the other market ratios."""
    return get_history_with_source(index_symbol, "7y")


@st.cache_data(ttl=600, show_spinner=False)
def run_search(query):
    return companies.search(query)


# ---------- header ----------
about.title_row("Stock Explorer")
st.caption("Price history, key signals and a range of possible outcomes for Indian companies listed on the NSE and the BSE.")
market_strip.render(lambda: trading_ui.snapshot_now(trading_ui._get_portfolio()), portfolio_ui.my_rank)
trading_ui.user_bar()
trading_ui.housekeeping()      # settle expired futures/options, close busted futures
trading_ui.show_flash()        # result of the last click, wherever it came from
trading_ui.show_events()       # e.g. 'your future expired and was settled'

# ---------- company search: one box, suggestions as you type ----------
def _use_found_company(symbol):
    """Button callback: make a company found by the live Yahoo search the chosen one."""
    st.session_state.setdefault("extra_companies", [])
    if symbol not in st.session_state["extra_companies"]:
        st.session_state["extra_companies"].append(symbol)
    st.session_state["company"] = symbol


company_options = list(st.session_state.get("extra_companies", [])) + universe.OPTIONS
if st.session_state.get("company") not in company_options:
    st.session_state["company"] = company_options[0]
symbol = st.selectbox("Search any NSE or BSE company (start typing a name)", company_options,
                      format_func=companies.label, key="company",
                      help=f"{len(universe.OPTIONS):,} companies listed on the NSE and the BSE. Type part of a name, "
                           "for example 'tata', 'suzlon' or 'bank', and pick from the suggestions.")
with st.expander("Cannot find a company? Search Yahoo Finance live"):
    live_query = st.text_input("Company name", key="live_query", placeholder="e.g. a company that listed very recently")
    if live_query.strip():
        found, _src = run_search(live_query.strip())
        if not found:
            st.warning(f"Nothing found for “{live_query}”. Try another spelling.")
        for r in found[:8]:
            c1, c2 = st.columns([5, 1])
            c1.write(companies.label(r["symbol"]) if r["symbol"] in companies.NAME_BY_SYMBOL else f"{r['name']} ({r['symbol']})")
            c2.button("Use", key=f"use_{r['symbol']}", on_click=_use_found_company, args=(r["symbol"],))

# ---------- load data ----------
name = load_name(symbol)
with st.spinner(f"Loading {name}..."):
    hist, source, last_date = load_history(symbol)

if hist is None or len(hist) < 30:
    st.error("Price data for this company could not be loaded right now. "
             "Please check the internet connection or choose another company.")
    st.stop()

if source == "offline":
    notice(f"Live prices are unavailable right now, so saved data up to {last_date:%d %b %Y} is being shown. "
           "Prices may be out of date.")

close = hist["Close"]
latest, previous = float(close.iloc[-1]), float(close.iloc[-2])  # last two daily closes (saved/cached)


@guard()
def show_headline():
    """Big price at the top. While the market is open this block refreshes itself every few seconds."""
    quote = None if source == "offline" else live_quote(symbol)
    price = quote["price"] if quote else latest
    prev_close = (quote or {}).get("previous_close") or previous
    change = price - prev_close
    st.metric(f"{name}: {'current price' if quote and is_market_open() else 'last close'}",
              format_inr(price), f"{format_inr(change)} ({change / prev_close * 100:+.2f}%) vs previous close")
    if source == "offline":
        st.caption("Saved data is being shown, so the price is not live.")
    elif is_market_open():
        st.caption(f"{status_message()}. Updating automatically. Last updated {now_ist():%H:%M:%S} IST. "
                   "Prices may be delayed by a few minutes.")
    else:
        st.caption(f"{status_message()}. Showing the last closing price.")


st.fragment(run_every=15 if (is_market_open() and source != "offline") else None)(show_headline)()


# The market index (Nifty 50 for an NSE listing, Sensex for a BSE listing), used to compare the stock against the market
bench_symbol, bench_name = companies.benchmark_for(symbol)
_bench, _, _ = load_benchmark(bench_symbol)
bench_close = _bench["Close"] if _bench is not None else None

PERIODS = {"6 months": 126, "1 year": 252, "2 years": 504, "5 years": 1260}
STRATEGY_KEYS = list(STRATEGIES)

tab_overview, tab_carpet, tab_outcomes, tab_strategy, tab_fusion, tab_trade, tab_portfolio, tab_bot = st.tabs(
    ["Overview", "Market carpet", "Possible outcomes", "Strategy tests", "Fusion analysis", "Paper trading", "Your Portfolio", "Ask the bot"],
    key="main_tabs")           # a key keeps the chosen tab selected when the page refreshes after a click

# =====================================================================
# TAB 1: OVERVIEW - price chart, key signals, risk and return ratios
# =====================================================================
with tab_overview:
    st.markdown("**In short:** the chart shows what the price did. The cards below say whether it is speeding up or slowing down, how bumpy it is, and whether the risk was worth the reward.")
    st.header("Price history")
    p1, p2, p3 = st.columns([5, 3, 1])
    period = p1.radio("Period", list(PERIODS), index=1, horizontal=True)
    show_fib = p2.checkbox("Show Fibonacci levels", key="show_fib",
                           help="Draws the classic retracement lines (23.6%, 38.2%, 50%, 61.8%, 78.6%) between the highest and lowest price in the period you are viewing.")
    with p3:
        help_bubble("fibonacci")

    fig = price_chart(hist, symbol, name)
    fib = ind.fibonacci_levels(hist, PERIODS[period]) if show_fib else None
    if show_fib:
        add_fibonacci(fig, fib)
    fig = zoom_to_window(fig, hist, PERIODS[period])
    st.plotly_chart(fig, width="stretch")
    if show_fib:
        st.info(ind.describe_fibonacci(fib) + " The dashed lines are Fibonacci levels where traders watch for a pause or turn. "
                "They depend on the period chosen and are a visual guide, not a prediction.")
    st.caption("Each bar is one trading day. The amber and navy lines are the average price over the last 50 and "
               "200 days; they smooth out day-to-day noise. The grey band is the price's usual range, and it "
               "widens when the price is moving more. The bars underneath are volume, the number of shares traded each day "
               "(green on days the price rose, red when it fell); the grey line is the usual level. Tall bars mean a busy day.")

    # ---------- key signals ----------
    st.header("Key signals")
    st.caption("Five commonly used measures. They describe the past; they do not predict. Hold your pointer over a term for two seconds to see it in plain words.")
    panel = [
        ("RSI", "rsi", *ind.describe_rsi(close)),
        ("MACD", "macd", *ind.describe_macd(close)),
        ("Trend", "trend", *ind.describe_trend(close)),
        ("Volatility", "volatility", *ind.describe_volatility(close.iloc[-252:])),  # last year, same window as the simulation
        ("Volume backing", "volume_confirmation", *ind.describe_volume(hist)),
    ]
    with st.container(key="signals_row"):          # on narrow screens the cards wrap onto a second row instead of clipping
        for column, (title, term, value, meaning) in zip(st.columns(5), panel):
            with column:
                metric_with_help(title, value, term)
                st.markdown(f'<div class="meaning">{meaning}</div>', unsafe_allow_html=True)
    plain_english(
        "**Recent strength (RSI)** is a score from 0 to 100 of how fast the price has been rising or falling lately. "
        "Above 70 the stock may have run up too fast; below 30 it may have fallen too fast.\n\n"
        "**Momentum (MACD)** compares a quick and a slow average of the price. If the quick one is higher, the price is "
        "gaining speed upward; if lower, downward.\n\n"
        "**Trend direction** looks at whether the price is above or below its 50-day and 200-day average prices.\n\n"
        "**Price swings (volatility)** is how much the price typically moves up or down over a year. "
        "A higher number means a bumpier ride.\n\n"
        "**Volume backing** asks: were lots of people behind the recent move? Volume is how many shares changed hands. "
        "A rise on busy trading is more believable than a rise on quiet trading. *Yes* means the recent move came with "
        "above-average volume, *No* means below-average, *Mixed* means about normal.")

    # ---------- risk and return ratios ----------
    st.header("Risk and return")
    st.caption(f"How much this stock earned, and how much risk it took to earn it, measured against the {bench_name}.")
    st.caption("Hold your pointer over any term for two seconds and it turns into plain words (tap it on a phone). "
               "Each bar runs from red (poor) to green (excellent); the dark pointer shows where this stock sits. "
               "Blue bars (beta, correlation) describe behaviour rather than grade it. Tap the ? for the formula.")
    ratio_period = st.radio("Measured over", ["1 year", "3 years", "5 years"], index=1, horizontal=True, key="ratio_period")
    n_days = {"1 year": 252, "3 years": 756, "5 years": 1260}[ratio_period]
    stock_returns = close.pct_change().dropna().iloc[-n_days:]
    bench_returns = bench_close.pct_change().dropna() if bench_close is not None else None
    r = ratios.summary(stock_returns, bench_returns)

    if r is None:
        st.info("There is not enough price history to calculate these ratios.")
    else:
        titles = {"cagr": "CAGR", "volatility": "Volatility", "max_drawdown": "Max drawdown",
                  "var95": "VaR (95%)", "sharpe": "Sharpe ratio", "sortino": "Sortino ratio",
                  "calmar": "Calmar ratio", "treynor": "Treynor ratio", "beta": "Beta", "alpha": "Alpha",
                  "information": "Information ratio", "correlation": "Correlation"}
        groups = [("How much it grew, and how bumpy", ["cagr", "volatility", "max_drawdown", "var95"]),
                  ("Was the risk worth it?", ["sharpe", "sortino", "calmar", "treynor"]),
                  (f"Compared with the market ({bench_name})", ["beta", "alpha", "information", "correlation"])]
        for group_name, keys in groups:
            st.subheader(group_name)
            for column, key in zip(st.columns(4), keys):
                value, meaning = ratios.describe(key, r, bench_name)
                with column:
                    metric_with_help(titles[key], value, key)
                    scale = ratio_scale(key, r.get(key))
                    st.markdown(scale or f'<div class="meaning">{meaning}</div>', unsafe_allow_html=True)
        if bench_returns is None:
            st.caption(f"{bench_name} data could not be loaded, so the comparison ratios are not available.")
        st.caption(f"A safe return of {ratios.RISK_FREE * 100:.1f}% a year (about a government bond) is assumed where a "
                   "ratio needs one. Ratios describe the past only.")
    plain_english(ratios.GLOSSARY, "What do these ratios mean? (plain English)")

# =====================================================================
# MARKET CARPET - industries at a glance, then the companies inside one industry
# =====================================================================
with tab_carpet:
    carpet_ui.render()

# =====================================================================
# TAB 2: POSSIBLE OUTCOMES - Monte Carlo on the price, and on each rule
# =====================================================================
with tab_outcomes:
    st.header("Possible outcomes")
    st.markdown("**In short:** nobody knows the future, so we imagine 2,000 of them and see where the price tends to land.")
    st.caption("We run 2,000 simulated futures using how this stock has moved over the past year: its average "
               "direction and how much it swings from day to day. The result is a range of possibilities, "
               "not a forecast. The table shows what each trading rule would have done in those same futures; "
               "open any item underneath for the details.")

    horizon = st.radio("Time ahead", [30, 60, 90], horizontal=True, format_func=lambda d: f"{d} days")
    if "sim_round" not in st.session_state:
        st.session_state.sim_round = 0
    if st.button("Re-run simulation"):
        st.session_state.sim_round += 1  # a new round gives new random numbers

    # Seed = stock + horizon + round, so the picture stays steady while it is being
    # explained, but changes when the visitor presses the button.
    seed = zlib.crc32(f"{symbol}-{horizon}-{st.session_state.sim_round}".encode())
    paths = sim.simulate(close, calendar_days=horizon, n_paths=2000, seed=seed)
    low, high = sim.likely_range(paths, 0.70)
    chances = sim.outcome_chances(paths)
    cost_pct = st.session_state.get("cost_pct", bt.DEFAULT_COST_PCT)   # set on the Strategy tests tab

    # ---------- every rule at a glance (the first thing on the page) ----------
    fusion_info = fusion_ui.company_row(symbol)                       # None if this company has no fundamentals
    fusion_passes = bool(fusion_info and (fusion_info["quality_ok"] or fusion_info["value_ok"]))
    RULES = [(k, STRATEGIES[k], None) for k in STRATEGY_KEYS]
    if fusion_info is not None:
        RULES.append(("fusion", FUSION_RULE, fusion_rule_for(fusion_passes)))

    outs = {}
    for key, rule, fn in RULES:
        if len(close) >= rule.warmup + 60:
            outs[key] = sim.strategy_outcomes(close, key, paths, cost_pct=cost_pct, rule_fn=fn)

    st.subheader("All trading rules side by side")
    st.caption("Every rule run through the same 2,000 simulated futures, next to simply holding the stock. Open any rule "
               "below the table to study it in more detail.")
    rows = []
    hold_ref = next((o["hold"] for o in outs.values()), None)
    if hold_ref is not None:
        h = np.asarray(hold_ref) * 100
        rows.append({"Rule": "Just hold the stock", "Chance of a gain": float((h > 0).mean() * 100),
                     "Typical result": float(np.median(h)), "Poor case (1 in 20)": float(np.percentile(h, 5)),
                     "Good case (1 in 20)": float(np.percentile(h, 95)), "Beats holding": None, "Status": "Always invested"})
    for key, rule, fn in RULES:
        out = outs.get(key)
        if out is None:
            rows.append({"Rule": rule.name, "Chance of a gain": None, "Typical result": None,
                         "Poor case (1 in 20)": None, "Good case (1 in 20)": None, "Beats holding": None,
                         "Status": "Not enough price history"})
            continue
        if key == "fusion" and not fusion_passes:
            status = "Fundamentals do not pass, so it stays in cash"
        elif out["invested"] < 0.02:
            status = "Waiting for a signal (in cash now)"
        else:
            status = f"Invested {out['invested'] * 100:.0f}% of the days"
        rows.append({"Rule": rule.name, "Chance of a gain": out["chance_gain"] * 100,
                     "Typical result": out["median"] * 100, "Poor case (1 in 20)": out["poor"] * 100,
                     "Good case (1 in 20)": out["good"] * 100, "Beats holding": out["chance_beats_hold"] * 100,
                     "Status": status})
    if outs:
        best_key = max(outs, key=lambda k: outs[k]["median"])
        best_name = next(r.name for k, r, _ in RULES if k == best_key)
        callout(f"Over the next {horizon} days, the rule with the best typical result is <b>{best_name}</b> "
                f"({outs[best_key]['median'] * 100:+.1f}%). That says how the rules behave in these imagined futures, "
                "not which one to use.")
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch", column_config={
        "Chance of a gain": st.column_config.NumberColumn(format="%.0f%%"),
        "Typical result": st.column_config.NumberColumn(format="%+.1f%%"),
        "Poor case (1 in 20)": st.column_config.NumberColumn(format="%+.1f%%"),
        "Good case (1 in 20)": st.column_config.NumberColumn(format="%+.1f%%"),
        "Beats holding": st.column_config.NumberColumn(format="%.0f%%")})
    st.caption("Poor case: only 1 simulated future in 20 did worse. Good case: only 1 in 20 did better. "
               "'Beats holding' is how often the rule did better than just holding. "
               + ("The fusion rule is not shown for this one because it has no company results to judge." if fusion_info is None else ""))

    st.subheader("Study one in more detail")
    st.caption("Open an item to see its chart, what it means in plain English, and exactly how it was calculated.")

    # ---------- the price itself ----------
    with st.expander("Price only: where the share price itself could end up", expanded=False):
        callout(f"Based on past behaviour, there is roughly a <b>70% chance</b> the price will be between "
                f"<b>{format_inr(low)}</b> and <b>{format_inr(high)}</b> in {horizon} days "
                f"(last close: {format_inr(latest)}).")

        gauge_col, split_col = st.columns([1.1, 1])
        with gauge_col:
            st.plotly_chart(outlook_gauge(chances["up"], horizon), width="stretch")
        with split_col:
            st.subheader("How the simulated outcomes split")
            m1, m2 = st.columns(2)
            m1.metric("Ends higher", f"{chances['up'] * 100:.0f}%")
            m2.metric("Ends lower", f"{chances['down'] * 100:.0f}%")
            m3, m4, m5 = st.columns(3)
            m3.metric("Up more than 5%", f"{chances['big_up'] * 100:.0f}%")
            m4.metric("Within 5%", f"{chances['flat'] * 100:.0f}%")
            m5.metric("Down more than 5%", f"{chances['big_down'] * 100:.0f}%")
            st.caption("These are the shares of the 2,000 simulated futures that ended each way. They reflect the "
                       "past year, so a stock that has been falling will lean towards 'lower'.")

        st.plotly_chart(fan_chart(hist, paths, horizon, symbol, name), width="stretch")
        st.caption("The darker the shading, the more of the simulated futures pass through that area: the darkest holds "
                   "half of them and the lightest holds 90%. Real prices can land outside it, because the "
                   "simulation cannot see news, company results or sudden shocks.")

        plain_english(
            "- We look at how this stock moved over the past year, then imagine 2,000 different ways the next few weeks "
            "could play out.\n"
            "- The **gauge** shows how many of those 2,000 futures ended higher than today's price.\n"
            "- The **shaded fan** shows the range the price covers across them: wider means more uncertainty.\n"
            "- It shows what is *possible*, not what *will* happen.")
        know_how_button("kh_price", "Possible outcomes for the price", (
            "**What it is.** A Monte Carlo simulation: we generate many random price paths that behave statistically like "
            "this stock has behaved, and read the results off the whole crowd of paths.\n\n"
            "**Inputs (factors).**\n"
            "- Daily log returns over the last 252 trading days.\n"
            "- Their average (the stock's drift) and standard deviation (its daily volatility).\n"
            "- Horizon: 30, 60 or 90 calendar days, converted to trading days (30 days is about 21 trading days).\n\n"
            "**Calculation.**\n"
            "1. For each of 2,000 paths and each future day, draw a random move from a bell curve with the stock's average "
            "daily return and daily volatility.\n"
            "2. Price tomorrow = price today x exp(random move). Repeat day by day.\n"
            "3. **Range sentence:** the 15th and 85th percentiles of the final prices contain the middle 70% of outcomes.\n"
            "4. **Gauge:** the share of the 2,000 paths whose final price is above today's price.\n"
            "5. **Fan chart:** percentile bands (5-95, 15-85, 25-75) of the price on each day.\n\n"
            "**Assumptions and limits.** Returns are random, bell-shaped and independent from day to day, and the past "
            "year's drift and volatility continue. Real markets have fatter tails (bigger surprises) and news. "
            "Re-run the simulation to see how much the answer moves with luck alone."))

    # ---------- each trading rule applied to the same simulated futures ----------
    for key, rule, fn in RULES:
        with st.expander(f"{rule.name}: study in more detail", expanded=False):
            st.caption(rule.headline)
            if len(close) < rule.warmup + 60:
                st.info("This company does not have enough price history for this rule.")
                continue
            out = outs[key]
            callout(f"If this rule were followed through each of the 2,000 simulated futures over the next {horizon} days, "
                    f"roughly <b>{out['chance_gain'] * 100:.0f}%</b> would end with a gain. The typical (median) result is "
                    f"<b>{out['median'] * 100:+.1f}%</b>, and in 9 cases out of 10 the result falls between "
                    f"<b>{out['poor'] * 100:+.1f}%</b> and <b>{out['good'] * 100:+.1f}%</b>.")
            if key == "fusion" and not fusion_passes:
                notice("This company's quality and valuation scores both fall below the pass mark (see the Fusion analysis "
                       "tab), so the fusion rule never buys it. That is the rule working as designed: no fundamental support, no purchase.")
            elif out["invested"] < 0.02:
                notice("The rule is currently in cash: it is not signalling a purchase, and it would only buy if the "
                       "price moved enough to trigger it. Results close to zero reflect that.")
            for col, (title, term, value) in zip(st.columns(5), [
                    ("Chance of a gain", "chance_gain", f"{out['chance_gain'] * 100:.0f}%"),
                    ("Typical result", "typical", f"{out['median'] * 100:+.1f}%"),
                    ("Poor case (1 in 20)", "poor_case", f"{out['poor'] * 100:+.1f}%"),
                    ("Good case (1 in 20)", "good_case", f"{out['good'] * 100:+.1f}%"),
                    ("Beats holding", "beats_holding", f"{out['chance_beats_hold'] * 100:.0f}%")]):
                with col:
                    metric_with_help(title, value, term)
            st.plotly_chart(outcome_histogram(out["strategy"], out["hold"], rule.name,
                                              f"How the {rule.name.lower()} would fare across 2,000 simulated futures"),
                            width="stretch")
            st.caption(f"Time spent in the stock: {out['invested'] * 100:.0f}% of the days. 'Beats holding' is the share "
                       "of simulated futures where the rule did better than simply holding the stock.")
            plain_english(
                "- We take the same 2,000 imagined futures as the price view, and let this rule trade through each one.\n"
                "- The chart counts how often each result happened: the navy bars are the rule, the grey bars are simply "
                "holding the stock.\n"
                "- A tall bar to the right of the dashed line means gains were common; to the left means losses were.\n\n"
                + rule.plain)
            know_how_button(f"kh_out_{key}", f"{rule.name} on possible futures", (
                "**What it is.** The price simulation from the *Price only* view, with a trading rule applied to every path.\n\n"
                "**Method.**\n"
                "1. Simulate 2,000 price paths for the chosen horizon (same method and random numbers as the price view).\n"
                "2. Join each path onto the last 400 real trading days so the rule's averages are already warmed up.\n"
                "3. Run the rule day by day on every path. Positions decided at a day's close are earned the **next** day.\n"
                f"4. Subtract a trading cost of {cost_pct:.2f}% of the portfolio each time the position changes "
                "(change it on the Strategy tests tab).\n"
                "5. Compound the daily results into each path's return, and compare with simply holding.\n\n"
                "**Reading the numbers.** Chance of a gain = share of paths with a positive return. Typical = median. "
                "Poor / good case = 5th / 95th percentile. Beats holding = share of paths where rule return > holding return.\n\n"
                "---\n\n" + rule.know_how))

# =====================================================================
# TAB 3: STRATEGY TESTS - each rule replayed over the past 5 years
# =====================================================================
with tab_strategy:
    st.header("Strategy tests")
    st.markdown("**In short:** if you had followed a simple rule for the last 5 years, would you have done better than just holding?")
    st.caption("Replay the last 5 years starting with Rs 1,00,000 and see how a rule would have fared against simply "
               "buying and holding. Past results do not predict future results.")
    cost_pct = st.number_input("Trading cost each time the rule switches (%)", min_value=0.0, max_value=2.0,
                               value=bt.DEFAULT_COST_PCT, step=0.05, format="%.2f", key="cost_pct",
                               help="Brokerage, taxes and the gap between buy and sell prices, as a percentage of the portfolio.")

    test_tabs = st.tabs([f"{STRATEGIES[k].name}" for k in STRATEGY_KEYS] + ["Monte Carlo test"])

    ROW_LABELS = [("Ending value of Rs 1,00,000", "ending_value"), ("Total return", "total_return"),
                  ("CAGR", "cagr"), ("Max drawdown", "max_drawdown"),
                  ("Volatility", "volatility"), ("Sharpe ratio", "sharpe"), ("Sortino ratio", "sortino"),
                  ("Calmar ratio", "calmar"), ("Treynor ratio", "treynor"), ("Beta", "beta")]

    results = {}
    for tab, key in zip(test_tabs, STRATEGY_KEYS):
        rule = STRATEGIES[key]
        results[key] = bt.run_backtest(close, key, cost_pct=cost_pct, benchmark=bench_close)
        result = results[key]
        with tab:
            st.caption(rule.headline + (f"  Style: {rule.style}." if rule.style else ""))
            if result is None:
                st.info("This company does not have enough price history (about 6 years) for this test.")
                continue
            callout(bt.verdict(result) + f" The rule switched between stock and cash {result['trades']} times and "
                    f"was invested {result['days_invested_pct']:.0f}% of the time.")
            st.plotly_chart(backtest_chart(result), width="stretch")

            s, b = result["stats"]["Strategy"], result["stats"]["Buy and hold"]
            c1, c2 = st.columns(2)
            c1.metric(f"{rule.name}: Rs 1,00,000 became", format_inr(s["final_value"]),
                      f"{s['total_return'] * 100:+.1f}% in total")
            c2.metric("Buy and hold: Rs 1,00,000 became", format_inr(b["final_value"]),
                      f"{b['total_return'] * 100:+.1f}% in total")

            term_row("Measure", None, rule.name, "Buy and hold", header=True)
            for label, k in ROW_LABELS:
                if k == "ending_value":
                    sv, bv = format_inr(s["final_value"], 0), format_inr(b["final_value"], 0)   # no paise: keeps phone columns tidy
                elif k in ("total_return", "cagr", "max_drawdown", "volatility"):
                    signed = k in ("total_return", "cagr")
                    sv, bv = ratios.pct(s[k], sign=signed), ratios.pct(b[k], sign=signed)
                else:
                    sv, bv = ratios.describe(k, s)[0], ratios.describe(k, b)[0]
                term_row(label, k, sv, bv)
            # trade-by-trade results and the expectancy formula (CMT Level III, 8.1)
            e = s.get("expectancy")
            if e:
                term_row("Number of trades", None, str(e["trades"]), "1 (held throughout)")
                term_row("Win rate (per trade)", "win_rate", ratios.pct(e["win_rate"], 0), "n/a")
                term_row("Average win", "avg_win", ratios.pct(e["avg_win"], sign=True), "n/a")
                term_row("Average loss", "avg_loss", ratios.pct(-e["avg_loss"]), "n/a")
                term_row("Expectancy per trade", "expectancy", ratios.pct(e["expectancy"], sign=True), "n/a")
            st.caption(f"Costs of {cost_pct:.2f}% are charged on every switch. Cash earns nothing. Signals are acted on the "
                       "next day. A good result in the past does not mean a good result in the future.")

            plain_english(
                "- Imagine you had Rs 1,00,000 five years ago and followed this rule every day, versus buying once and never selling.\n"
                "- The chart shows how each would have grown. Green triangles are the days the rule bought; red ones are the days it sold.\n"
                "- The table below the chart shows more than just the final amount: the **worst fall** and the **Sharpe, Sortino and "
                "Calmar** ratios tell you how bumpy the ride was for the return earned.\n"
                "- **Expectancy** is what a typical trade earned: (win rate x average win) minus (loss rate x average loss). "
                "A rule can lose most of its trades and still win overall if the wins are big (trend following), or win most trades "
                "with small gains (swing trading).\n\n" + rule.plain +
                "\n\nSee *What do these ratios mean?* on the Overview tab for the plain-English meaning of every ratio.")
            know_how_button(f"kh_bt_{key}", rule.name, (
                "**What it is.** A backtest: replaying the past to see what a rule would have done.\n\n"
                "**Method.**\n"
                "1. Download 7 years of daily prices (5 years are measured; 2 years let the rule's averages warm up).\n"
                "2. Work out the rule's position (stock or cash) for every day, using only information available at that day's close.\n"
                f"3. Earn each day's price change only if the stock was held, using the position decided the **previous** day. "
                f"Subtract {cost_pct:.2f}% of the portfolio each time the position changes (including buying in on day one).\n"
                "4. Compound the daily results from Rs 1,00,000. Buy-and-hold is the same, with one purchase on day one.\n"
                "5. Ratios use the daily results: Sharpe = (average daily return above the safe rate) / (daily volatility) x sqrt(252); "
                "Sortino uses only the downside volatility; Calmar = yearly return / worst fall; Treynor and Beta compare with the market index (the Nifty 50, or the Sensex for a BSE listing).\n\n"
                "**Assumptions and limits.** No taxes beyond the cost set above; cash earns nothing; trades fill at the next close; "
                "one stock, one period, and a rule that has not been tuned (which avoids overfitting, but also means no claim about the future).\n\n"
                "---\n\n" + rule.know_how))

    # ---------- Monte Carlo test: how much of the 5-year result was luck? ----------
    with test_tabs[-1]:
        st.caption("A robustness check: shuffle the last 5 years into thousands of alternative histories to see how "
                   "much a result depends on luck.")
        pick = st.selectbox("Rule to test", STRATEGY_KEYS, format_func=lambda k: STRATEGIES[k].name, key="mc_pick")
        base = results.get(pick)
        if base is None:
            st.info("This company does not have enough price history for this test.")
        else:
            if "mc_round" not in st.session_state:
                st.session_state.mc_round = 0
            if st.button("Shuffle again", key="mc_again"):
                st.session_state.mc_round += 1
            mc_seed = zlib.crc32(f"{symbol}-{pick}-{st.session_state.mc_round}".encode())
            mc = bt.bootstrap_test(base["daily"]["Strategy"], base["daily"]["Buy and hold"], seed=mc_seed)
            sf, hf = mc["strategy_final"], mc["hold_final"]
            callout(f"Across 2,000 reshuffled versions of the last 5 years, the {STRATEGIES[pick].name.lower()} ended with a loss "
                    f"in <b>{(sf < 0).mean() * 100:.0f}%</b> of them, with a typical result of "
                    f"<b>{float(np.median(sf)) * 100:+.0f}%</b>. It beat buy-and-hold in "
                    f"<b>{(sf > hf).mean() * 100:.0f}%</b> of them.")
            for col, (title, term, value) in zip(st.columns(5), [
                    ("Chance of a loss", "chance_loss", f"{(sf < 0).mean() * 100:.0f}%"),
                    ("Typical result", "typical", f"{np.median(sf) * 100:+.0f}%"),
                    ("Poor case (1 in 20)", "poor_case", f"{np.percentile(sf, 5) * 100:+.0f}%"),
                    ("Good case (1 in 20)", "good_case", f"{np.percentile(sf, 95) * 100:+.0f}%"),
                    ("Beats holding", "beats_holding", f"{(sf > hf).mean() * 100:.0f}%")]):
                with col:
                    metric_with_help(title, value, term)
            st.plotly_chart(outcome_histogram(sf, hf, STRATEGIES[pick].name,
                                              "5-year results across 2,000 reshuffled histories", "5-year return"),
                            width="stretch")
            st.caption(f"Worst fall from a peak: typically {np.median(mc['strategy_worst']) * 100:.0f}%, and "
                       f"{np.percentile(mc['strategy_worst'], 5) * 100:.0f}% or worse in 1 history out of 20 (buy-and-hold: "
                       f"{np.median(mc['hold_worst']) * 100:.0f}% typical).")
            plain_english(
                "- The real 5 years happened only once, in one order. A good result could be partly luck.\n"
                "- So we cut those 5 years into short chunks and shuffle them into 2,000 different histories, "
                "as if the same days had come in a different order.\n"
                "- If the rule does well in most of the shuffled histories, its result is more believable. "
                "If it only worked in the real one, it may have been luck.")
            know_how_button("kh_mc", "Monte Carlo strategy test", (
                "**What it is.** A *bootstrap* Monte Carlo test of a backtest. It asks how robust the 5-year result is.\n\n"
                "**Method.**\n"
                "1. Take the rule's daily results over the last 5 years (after trading costs) and buy-and-hold's daily results.\n"
                "2. Cut each series into blocks of 10 consecutive days. Blocks keep short-term patterns (such as streaks) intact.\n"
                "3. Build 2,000 alternative 5-year histories by drawing blocks at random with replacement.\n"
                "4. The **same** draws are applied to the rule and to buy-and-hold, so the comparison is fair.\n"
                "5. For each history, compound the daily results to get the total return and the worst fall from a peak.\n"
                "6. Report the share of histories with a loss, the median and 5th/95th percentile results, and how often the rule beat holding.\n\n"
                "**Assumptions and limits.** It assumes the days in the sample are a fair picture of what can happen, so it "
                "cannot show events that never occurred in these 5 years. It tests luck, not whether the rule will work in future."))

# =====================================================================
# TAB 4: FUSION ANALYSIS (CMT Level III, Chapter 8)
# =====================================================================
with tab_fusion:
    fusion_ui.render(symbol, name)

# =====================================================================
# TAB 5: PAPER TRADING (stocks, ETFs, bonds, futures, options)
# =====================================================================
with tab_trade:
    trading_ui.render(symbol, name, latest, offline=(source == "offline"))

# =====================================================================
# TAB 6: YOUR PORTFOLIO - build, track and compare portfolios
# =====================================================================
with tab_portfolio:
    portfolio_ui.render()

# =====================================================================
# TAB 7: ASK THE BOT - answers from the site's own notes (free, no outside service)
# =====================================================================
with tab_bot:
    _pf = trading_ui._get_portfolio()
    assistant_ui.render({
        "company": name, "symbol": symbol, "last_close": latest,
        "signals": [(title, value, meaning) for title, _term, value, meaning in panel],
        "portfolio": {"cash": _pf.balance, "holdings": {s_: h["quantity"] for s_, h in _pf.holdings.items()},
                      "derivatives": len(_pf.derivatives)},
        "fusion": fusion_ui.company_row(symbol),
    })

# ---------- footer disclaimer ----------
show_disclaimer()
