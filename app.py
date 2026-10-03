"""Stock Explorer - Streamlit app.  Run with:  streamlit run app.py

Streamlit re-runs this whole file from top to bottom every time a visitor clicks
something. That is why slow things (downloading prices) are wrapped in
st.cache_data: the second time, the answer comes from memory instantly.
"""
import zlib

import streamlit as st

from core import backtest as bt, companies, indicators as ind, simulation as sim, trading_ui
from core.charts import backtest_chart, fan_chart, outlook_gauge, price_chart, zoom_to_window
from core.formatting import format_inr
from core.market_data import get_company_name, get_history_with_source
from core.ui import callout, notice, setup_page, show_disclaimer

setup_page("Stock Explorer")


# ---------- cached data loaders ----------
@st.cache_data(ttl=600, show_spinner=False)
def load_history(symbol):
    # Returns (prices, "online"/"offline"/"none", last date). 7 years: 5 to test + 2 to warm up.
    return get_history_with_source(symbol, "7y")


@st.cache_data(ttl=86400, show_spinner=False)
def load_name(symbol):
    # Our own list already has names; only ask Yahoo for tickers we don't know.
    return companies.NAME_BY_SYMBOL.get(symbol) or get_company_name(symbol)


@st.cache_data(ttl=600, show_spinner=False)
def run_search(query):
    return companies.search(query)


# ---------- header ----------
st.title("Stock Explorer")
st.caption("Price history, key signals and a range of possible outcomes for Indian (NSE) companies.")

# ---------- company search + dropdown ----------
col_search, col_pick = st.columns(2)
with col_search:
    query = st.text_input("Search by company name", placeholder="e.g. Reliance, Tata Motors, HDFC")

if query.strip():
    results, source = run_search(query.strip())
    options = [r["symbol"] for r in results]
    if not options:
        st.warning(f"No company found for “{query}”. Try another spelling, or choose from the list.")
        options = [s for _, s, _ in companies.COMPANIES]
        hint = "All companies"
    else:
        hint = f"{len(options)} match(es)"
else:
    options = [s for _, s, _ in companies.COMPANIES]
    hint = "Or choose from the list (type to filter)"

with col_pick:
    symbol = st.selectbox(hint, options, format_func=companies.label)

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
latest, previous = float(close.iloc[-1]), float(close.iloc[-2])
change = latest - previous

st.metric(f"{name}: last close", format_inr(latest),
          f"{format_inr(change)} ({change / previous * 100:+.2f}%) vs previous day")

tab_overview, tab_outlook, tab_strategy, tab_trade = st.tabs(
    ["Overview", "Possible outcomes", "Strategy test", "Paper trading"])

# =====================================================================
# TAB 1: OVERVIEW - price chart and key signals
# =====================================================================
with tab_overview:
    st.header("Price history")
    period = st.radio("Period", ["6 months", "1 year", "2 years", "5 years"], index=1, horizontal=True)
    days = {"6 months": 126, "1 year": 252, "2 years": 504, "5 years": 1260}[period]

    fig = zoom_to_window(price_chart(hist, symbol, name), hist, days)
    st.plotly_chart(fig, width="stretch")
    st.caption("Each bar is one trading day. The amber and navy lines are the average price over the last 50 and "
               "200 days; they smooth out day-to-day noise. The grey band is the price's usual range, and it "
               "widens when the price is moving more.")

    st.header("Key signals")
    st.caption("Four commonly used measures, each explained in a sentence. They describe the past; they do not predict.")
    panel = [
        ("Recent strength (RSI)", *ind.describe_rsi(close)),
        ("Momentum (MACD)", *ind.describe_macd(close)),
        ("Trend direction", *ind.describe_trend(close)),
        ("Price swings (volatility)", *ind.describe_volatility(close.iloc[-252:])),  # last year, same window as the simulation
    ]
    for column, (title, value, meaning) in zip(st.columns(4), panel):
        with column:
            st.metric(title, value)
            st.markdown(f'<div class="meaning">{meaning}</div>', unsafe_allow_html=True)

# =====================================================================
# TAB 2: POSSIBLE OUTCOMES - Monte Carlo simulation + the gauge
# =====================================================================
with tab_outlook:
    st.header("Possible outcomes")
    st.caption("We run 2,000 simulated futures using how this stock has moved over the past year: its average "
               "direction and how much it swings from day to day. The result is a range of possibilities, "
               "not a forecast.")

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
        st.caption("These percentages are the share of the 2,000 simulated futures that ended in each way. "
                   "They reflect the past year, so a stock that has been falling will lean towards 'lower'.")

    st.plotly_chart(fan_chart(hist, paths, horizon, symbol, name), width="stretch")
    st.caption("The darker the shading, the more of the simulated futures pass through that area: the darkest holds "
               "half of them and the lightest holds 90%. Real prices can land outside it, because the "
               "simulation cannot see news, company results or sudden shocks.")

    with st.expander("How does this work?"):
        st.markdown(
            "1. We measure how much this stock moved each day over the past year, and its average direction.\n"
            "2. We create 2,000 imaginary futures. In each one, every day gets a random move of that typical size.\n"
            "3. We line up where all 2,000 ended. The middle 70% gives the range above, and the share that ended "
            "above today's price gives the gauge.\n\n"
            "This technique is called a Monte Carlo simulation. It is a way to see the range of what is possible, "
            "not to know what will happen.")

# =====================================================================
# TAB 3: STRATEGY TEST - backtest
# =====================================================================
with tab_strategy:
    st.header("Would a simple rule have beaten buy-and-hold?")
    st.caption("We replay the last 5 years starting with Rs 1,00,000. The rule: hold the stock while its 50-day "
               "average price is above its 200-day average, otherwise stay in cash. This is compared with buying "
               "on day one and never selling.")

    result = bt.run_backtest(close)
    if result is None:
        st.info("This company does not have enough price history (about 6 years) for this test.")
    else:
        st.plotly_chart(backtest_chart(result), width="stretch")
        s, b = result["stats"]["Crossover strategy"], result["stats"]["Buy and hold"]
        cols = st.columns(2)
        for column, title, stats in [(cols[0], "Moving-average rule", s), (cols[1], "Buy and hold", b)]:
            with column:
                st.subheader(title)
                st.metric("Rs 1,00,000 became", format_inr(stats["final_value"]),
                          f"{stats['total_return_pct']:+.1f}% in total")
                st.write(f"Average per year: **{stats['yearly_return_pct']:+.1f}%**  \n"
                         f"Largest fall from a peak: **{stats['worst_fall_pct']:.0f}%**")
        callout(bt.verdict(result) + f" The rule switched between stock and cash {result['trades']} times and "
                f"was invested {result['days_invested_pct']:.0f}% of the time.")
        st.caption("Simplifications: no fees or taxes, cash earns nothing, and signals are acted on the next day. "
                   "A good result in the past does not mean a good result in the future.")

# =====================================================================
# TAB 4: PAPER TRADING
# =====================================================================
with tab_trade:
    trading_ui.render(symbol, name, latest, offline=(source == "offline"))

# ---------- footer disclaimer ----------
show_disclaimer()
