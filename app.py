"""Stock Explorer - Streamlit app.  Run with:  streamlit run app.py

Streamlit re-runs this whole file from top to bottom every time a visitor clicks
something. That is why slow things (downloading prices) are wrapped in
st.cache_data: the second time, the answer comes from memory instantly.
"""
import zlib

import streamlit as st

from core import backtest as bt, companies, indicators as ind, simulation as sim
from core.charts import backtest_chart, fan_chart, price_chart
from core import trading_ui
from core.formatting import format_inr
from core.market_data import get_company_name, get_history_with_source
from core.ui import setup_page, show_disclaimer

setup_page("Stock Explorer")


# ---------- cached data loaders (cache for 1 hour) ----------
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
show_disclaimer()
st.title("📈 Stock Explorer")
st.caption("Pick an Indian (NSE) company to see its price chart and what the indicators say.")

# ---------- feature 1: search + dropdown ----------
col_search, col_pick = st.columns(2)
with col_search:
    query = st.text_input("Type a company name", placeholder="e.g. Reliance, tata motors, HDFC")

if query.strip():
    results, source = run_search(query.strip())
    options = [r["symbol"] for r in results]
    if not options:
        st.warning(f"I couldn't find “{query}”. Try another spelling, or pick from the list.")
        options = [s for _, s, _ in companies.COMPANIES]
        hint = "Browse all companies"
    else:
        hint = f"{len(options)} match(es) from {source}"
else:
    options = [s for _, s, _ in companies.COMPANIES]
    hint = "Or pick from the list (you can type to filter)"

with col_pick:
    symbol = st.selectbox(hint, options, format_func=companies.label)

# ---------- load data ----------
name = load_name(symbol)
with st.spinner(f"Loading {name}..."):
    hist, source, last_date = load_history(symbol)

if hist is None or len(hist) < 30:
    st.error("😕 I couldn't load price data for this company right now. "
             "Please check the internet connection or choose another company.")
    st.stop()

if source == "offline":
    st.warning(f"📴 Live prices are unavailable right now, so you are seeing **saved data** up to {last_date:%d %b %Y}. "
               "Prices may be out of date.")

close = hist["Close"]
latest, previous = float(close.iloc[-1]), float(close.iloc[-2])
change = latest - previous

# ---------- headline price ----------

st.metric(f"{name} - latest close", format_inr(latest),
          f"{format_inr(change)} ({change / previous * 100:+.2f}%) today")

tab_analyse, tab_trade = st.tabs(["📊 Analyse", "💰 Paper trading"])

with tab_analyse:
    # ---------- feature 2: chart ----------
    st.header("Price chart")
    period = st.radio("Show", ["6 months", "1 year", "2 years", "5 years"], index=1, horizontal=True)
    days = {"6 months": 126, "1 year": 252, "2 years": 504, "5 years": 1260}[period]

    fig = price_chart(hist, symbol, name)
    # Calculate the averages on ALL the data, but only *zoom* to the chosen window.
    fig.update_xaxes(range=[hist.index[-min(days, len(hist))], hist.index[-1]])
    st.plotly_chart(fig, width="stretch")
    st.caption("Orange/purple lines are the 50- and 200-day average prices. The grey band (Bollinger Bands) "
               "widens when the price is swinging a lot.")

    # ---------- feature 3: indicator panel ----------
    st.header("What do the indicators say?")
    panel = [
        ("RSI (14-day)", *ind.describe_rsi(close)),
        ("MACD", *ind.describe_macd(close)),
        ("Trend", *ind.describe_trend(close)),
        ("Volatility (yearly)", *ind.describe_volatility(close)),
    ]
    for column, (title, value, meaning) in zip(st.columns(4), panel):
        with column:
            st.metric(title, value)
            st.markdown(f'<div class="meaning">{meaning}</div>', unsafe_allow_html=True)

    # ---------- feature 4: "what might happen" (Monte Carlo) ----------
    st.header("What might happen?")
    st.caption("A simulation of 2,000 possible futures. It is **not a prediction** - nobody can predict markets.")

    horizon = st.select_slider("Look ahead", options=[30, 60, 90], value=30, format_func=lambda d: f"{d} days")
    if "sim_round" not in st.session_state:
        st.session_state.sim_round = 0
    if st.button("🎲 Run the simulation again"):
        st.session_state.sim_round += 1  # a new round gives new random numbers

    # Seed = stock + horizon + round, so the picture stays steady while explaining it,
    # but changes when the visitor presses the button.
    seed = zlib.crc32(f"{symbol}-{horizon}-{st.session_state.sim_round}".encode())  # stable number from text
    paths = sim.simulate(close, calendar_days=horizon, n_paths=2000, seed=seed)
    low, high = sim.likely_range(paths, 0.70)

    st.success(f"Based on past behaviour, there's roughly a **70% chance** the price is between "
               f"**{format_inr(low)}** and **{format_inr(high)}** in {horizon} days "
               f"(it is {format_inr(latest)} today).")
    st.plotly_chart(fan_chart(hist, paths, horizon, symbol, name), width="stretch")
    st.caption("How to read it: the darkest shaded area holds half of the simulated futures, the lightest holds 90%. "
               "The simulation only copies how bumpy the price was over the last year. It cannot see news, "
               "results, or crashes, so real prices can land outside the shaded area.")

    # ---------- feature 5: simple backtest ----------
    st.header("Would a simple rule have beaten buy-and-hold?")
    st.caption("We replay the last 5 years with Rs 1,00,000. **Rule:** hold the stock while its 50-day average is above "
               "its 200-day average, otherwise sit in cash. **Compared with:** buying on day one and never selling.")

    result = bt.run_backtest(close)
    if result is None:
        st.info("This company doesn't have enough price history (about 6 years) for the backtest.")
    else:
        st.plotly_chart(backtest_chart(result), width="stretch")
        s, b = result["stats"]["Crossover strategy"], result["stats"]["Buy and hold"]
        cols = st.columns(2)
        for column, title, stats in [(cols[0], "50/200 crossover rule", s), (cols[1], "Buy and hold", b)]:
            with column:
                st.subheader(title)
                st.metric("Rs 1,00,000 became", format_inr(stats["final_value"]),
                          f"{stats['total_return_pct']:+.1f}% in total")
                st.write(f"Average per year: **{stats['yearly_return_pct']:+.1f}%**  \n"
                         f"Worst fall from a peak: **{stats['worst_fall_pct']:.0f}%**")
        st.info(bt.verdict(result) + f" The rule made {result['trades']} buy/sell switches and was in the stock "
                f"{result['days_invested_pct']:.0f}% of the time.")
        st.caption("Simplifications: no fees or taxes, cash earns nothing, and signals are acted on the next day. "
                   "A good past result does not mean a good future result.")

with tab_trade:
    trading_ui.render(symbol, name, latest, offline=(source == "offline"))

# ---------- footer disclaimer (also shown at the bottom) ----------
st.divider()
show_disclaimer()
