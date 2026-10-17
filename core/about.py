"""The About page: opened by the small circled "i" at the top right of every page.

All the wording lives here so it is easy to edit. The creator's first name, extra thanks and a one-line reason can also be
set in the app's secrets without touching the code:

    [about]
    creator = "Asha"
    reason = "I wanted markets to feel less intimidating."
    thanks_extra = "...and my friends who tested it."
"""
import base64
import os

import streamlit as st

from core import errors as er

SITE_NAME = "Stock Explorer"

# ---- the creator (edit here, or override with [about] in the app's secrets) ----
CREATOR_NAME = "Freya Shah"
CREATOR_CLASS = "P/2977"
CREATOR_SCHOOL = "Mayo College Girls School"
CREDENTIALS = [
    ("CMT Level I", "Passed"),
    ("CMT Level II", "Passed"),
    ("CMT Level III", "Appearing"),
]
EPAT_BATCH = "EPAT (Batch-72)"

CMT_EXPLAINER = """\
**CMT: Chartered Market Technician**

The global professional designation in **technical analysis**, awarded by the **CMT Association** after three examinations. It is \
the credential portfolio managers, traders, strategists and risk professionals hold when their edge comes from price, volume and \
market structure rather than from fundamentals alone, and it is recognised by practitioners across the world's financial markets.

**Skills gained**
- **Level I, foundations:** trend analysis (Dow Theory, moving averages, ADX), momentum oscillators (RSI, MACD, stochastics), \
chart patterns, candlesticks, Fibonacci retracements, volume and breadth, and the logic of supply and demand.
- **Level II, application:** relative strength and sector rotation, intermarket analysis, volatility (ATR, Bollinger Bands), \
Elliott Wave and Wyckoff, systematic strategy design, back-testing, position sizing and risk management (expectancy, drawdown).
- **Level III, integration:** portfolio construction and asset allocation, behavioural finance (herding, anchoring, prospect \
theory), evaluating quantitative models (overfitting, out-of-sample testing), and **fusion analysis**, which overlays technical \
confirmation on fundamental and valuation views (the Winner's Circle used in this app).

Passing the levels while still at school is rare: the programme is normally taken by working finance professionals."""

EPAT_EXPLAINER = """\
**EPAT: Executive Programme in Algorithmic Trading**

A professional programme from **QuantInsti** that teaches how to trade with code and data. It is widely regarded as one of the \
most respected programmes in the world for algorithmic and quantitative trading: it is taught by practising traders and \
quants, it is built for working professionals, and its alumni work at trading firms, banks and funds across many countries.

**Skills gained from it**
- Python programming for finance, and working with market data
- Statistics, probability and time-series analysis
- Financial markets, derivatives (futures and options) and how orders are executed
- Designing, back-testing and optimising trading strategies without fooling yourself
- Risk and portfolio management
- Machine learning for trading
- Building and running automated, live trading systems

"**Batch 72**" is the cohort of learners Freya studied with. Like the CMT, it is usually taken by working professionals, so \
it is a serious step for a school student, and the skills behind the simulations, strategy tests and machine-learning \
estimate in this app are exactly the kind the programme teaches."""

WHAT_IT_IS = """\
**Stock Explorer** is an educational website that makes Indian (NSE and BSE) stocks easier to understand. You can look at price charts \
and signals, see a range of possible outcomes from simulations, test simple trading rules on past prices, study stocks with a \
method from the CMT Level III curriculum, and practise buying and selling with **virtual money** in shares, ETFs, bond funds, \
futures and options. Nothing here is real money, and nothing here is investment advice."""

HOW_TO_USE = """\
1. **Start:** choose a name and an amount of virtual money. Your portfolio is saved under your name, so you can come back later \
(choose *Returning user*).
2. **Pick a company** with the two boxes at the top.
3. **Overview:** the price chart, four key signals, and risk-and-return numbers.
4. **Possible outcomes:** thousands of simulated futures and what each trading rule would have done in them.
5. **Strategy tests:** four simple rules replayed over 5 years against buy-and-hold, plus a luck test.
6. **Fusion analysis:** rates each company with the Winner's Circle from the CMT Level III curriculum.
7. **Paper trading** and **Your Portfolio:** trade with virtual money, build a portfolio, and watch the leaderboard.
8. **Ask the bot:** answers questions about finance terms and how the app works.

Look for the small **?** next to any term: it explains what it is, its formula and how to read it. Most pages also have a \
**Know how** button with the full method."""

LIMITATIONS = """\
- **Not advice, not predictions.** The simulations show a range of possibilities, and back-tests describe the past. A good past \
result does not mean a good future result.
- **Prices can be late.** Share, ETF and bond-fund prices come from Yahoo Finance and can be a few minutes behind. Outside market \
hours (Monday to Friday, 9:15 AM to 3:30 PM Indian time, and on holidays) the last close is shown. The holiday list is not built in.
- **Futures and options prices are calculated,** not exchange quotes, because free data for them does not exist. Lot sizes and \
margins are simplified, and only buying options is allowed.
- **The tests are short and simple.** Strategy tests cover 5 years of prices; the fusion test covers about 3 years (free company \
results go back only about four years), only today's listed companies, and a mostly rising market. Trading costs are a simple \
percentage.
- **The fusion scores are our own simple versions.** The CMT chapter's authors use their own models, which are not published, so \
companies are ranked 0-100 against the other companies in our list.
- **The bot only knows its notes.** It answers from notes written for this site, so it can be incomplete, and it says so when \
it does not know.
- **Names have no passwords.** Anyone can open any portfolio by its name, so please use a first name or nickname.
- **Free hosting.** The site may be slow, or take a moment to wake up."""

SOURCES = """\
**Data**
- Prices of shares, ETFs, bond funds and the Nifty 50 and Sensex indices, and companies' yearly results: [Yahoo Finance](https://finance.yahoo.com), \
read with the open-source `yfinance` library. This is unofficial and may be delayed or occasionally wrong.
- Portfolios are stored in a [Supabase](https://supabase.com) database.

**Ideas and methods**
- Fusion analysis, the Winner's Circle, the technical overlay, expectancy, and trend following versus swing trading: the \
**CMT Level III curriculum, Chapter 8**: section 8.1 by David Lundgren, CMT, CFA, and section 8.5 by John J. Letizia II, CPA, \
CMT, CFTe. Explanations here are written in our own words.
- RSI (J. Welles Wilder), MACD (Gerald Appel), Bollinger Bands (John Bollinger), moving averages.
- Black-Scholes option pricing (1973) and the cost-of-carry formula for futures.
- Sharpe ratio (William Sharpe), Sortino ratio, Calmar ratio, Treynor ratio, Jensen's alpha, beta, Value at Risk.
- Monte Carlo simulation and block-bootstrap resampling.

**Software**
- Python, Streamlit, pandas, NumPy, Plotly, Requests and yfinance, all open source. Hosted on Streamlit Community Cloud.

*This is an independent student project. It is not affiliated with, or endorsed by, the NSE, the BSE, Yahoo, the CMT Association, \
Supabase or any broker.*"""


# ---- the same dialog for the second (dashboard) site: only what that site actually has ----
WHAT_IT_IS_SIMPLE = """\
**Stock Explorer** is an educational dashboard that makes Indian (NSE and BSE) stocks easier to understand. Search a company, read its \
price chart in daily, weekly or monthly candles, see a **combined model reading** made by five strategies from the CMT curriculum and a \
small machine-learning model, check the main indicators, and practise buying and selling shares with **virtual money**. Nothing here is \
real money, and nothing here is investment advice."""

HOW_TO_USE_SIMPLE = """\
1. **Start:** choose a name and an amount of virtual money. Your portfolio is saved under your name, so you can come back later \
(choose *Returning user*).
2. **Search stock:** type a company name (a small spelling slip is fine) and press Enter.
3. **Chart:** show 1, 2 or 4 charts, each in daily, weekly or monthly candles, with optional Fibonacci levels.
4. **Buy, Sell, Exit all:** practise trading with virtual money from the bar under the chart.
5. **The strategies:** a table of the five strategies (Fusion stage, Dow Theory, relative strength, Wyckoff effort vs result and \
Fibonacci confluence) and the ML model, each with a **Full view** that opens a chart and a plain explanation of what it is doing.
6. **Left side:** what you hold, what you sold, where your money is, the leaderboard, and a barometer that combines the five strategies.
7. **Right side:** six indicators: RSI, MACD, ADX, Z-score, Supertrend and Bollinger band.

Hover over the small **i** marks next to each indicator for a short explanation. The round **chat button** in the bottom-right corner opens "Ask me anything", a helper that explains terms and how the app works. The **Tour** button in the top bar walks through every part of the screen."""

LIMITATIONS_SIMPLE = """\
- **Not advice, and close to a coin toss for one day.** The model reading describes what some methods show, for learning; it is not a recommendation to buy or sell. In our tests the five CMT strategies and the \
machine-learning estimate were each right about 50% to 51% of the time on the next day, which is what chance gives. These methods are \
built for weeks and months.
- **Prices can be late.** Prices come from Yahoo Finance and can be a few minutes behind. Outside market hours (Monday to Friday, \
9:15 AM to 3:30 PM Indian time, and on holidays) the last close is shown. The holiday list is not built in.
- **Shares only.** Practice trading here covers shares, with simple virtual-money rules.
- **Names have no passwords.** Anyone can open any portfolio by its name, so please use a first name or nickname.
- **Free hosting.** The site may be slow, or take a moment to wake up."""

SOURCES_SIMPLE = """\
**Data**
- Prices of shares and the Nifty 50 and Sensex indices: [Yahoo Finance](https://finance.yahoo.com), read with the open-source `yfinance` \
library. This is unofficial and may be delayed or occasionally wrong.
- Portfolios are stored in a [Supabase](https://supabase.com) database.

**Ideas and methods**
- The five strategies: Fusion stage (the Winner's Circle trend test, **CMT Level III curriculum, Chapter 8**, in our own words), Dow Theory, \
relative strength, Wyckoff effort vs result and Fibonacci retracements.
- Indicators: RSI and ADX (J. Welles Wilder), MACD (Gerald Appel), Bollinger Bands (John Bollinger), Supertrend and the Z-score.
- The machine-learning estimate is a logistic regression trained on saved NSE price history.

**Software**
- Python, Streamlit, pandas, NumPy, Plotly, Requests and yfinance, all open source. Hosted on Streamlit Community Cloud.

*This is an independent student project. It is not affiliated with, or endorsed by, the NSE, the BSE, Yahoo, the CMT Association, \
Supabase or any broker.*"""


def _secret(name, default):
    try:
        return str(st.secrets["about"][name]).strip() or default
    except Exception:
        return default


def _initials(name):
    return "".join(w[0] for w in name.split()[:2]).upper() or "?"


def creator_story():
    reason = _secret("reason", "I wanted stock markets to feel less intimidating, especially for people who are not finance "
                               "experts.")
    return (f"{reason}\n\n"
            "Everything on this site, from the indicators to the fusion analysis, comes from what I have been learning. "
            "I built it with an AI coding assistant, which wrote the code while I chose what to build and checked that each "
            "part made sense.\n\n"
            f"If you find something that looks wrong, or have an idea, please tell the admin at "
            f"[{er.admin_email()}](mailto:{er.admin_email()}).")


MENTOR = "Mr. Prashant Kulshrestha"


def gratitude_markdown():
    extra = _secret("thanks_extra", "")
    return (f"**Thank you, {CREATOR_SCHOOL} and the IT department,** for giving me this opportunity.\n\n"
            f"**A special mention to {MENTOR}.** Thank you, sir, for your guidance. It shaped this project, and I am "
            "grateful for the time and trust you gave me.\n\n"
            "And thank you, the visitor, for taking the time to use it." + (f" {extra}" if extra else ""))


def _creator_section():
    name = _secret("creator", CREATOR_NAME)
    left, right = st.columns([1, 5])
    with left:
        st.markdown(f'<div class="monogram">{_initials(name)}</div>', unsafe_allow_html=True)
    with right:
        st.markdown(f'<div class="creator-name">{name}</div>'
                    f'<div class="creator-meta">{CREATOR_CLASS} &middot; {CREATOR_SCHOOL}</div>', unsafe_allow_html=True)

    st.markdown('<div style="height:0.8rem"></div><b>Credentials</b>', unsafe_allow_html=True)
    tip, row = st.columns([1, 9])
    with tip:
        with st.popover("?"):
            st.markdown(CMT_EXPLAINER)
    chips = "".join(f'<span class="chip {"chip-done" if status == "Passed" else "chip-next"}">{label}: {status}</span>'
                    for label, status in CREDENTIALS)
    row.markdown(chips, unsafe_allow_html=True)
    tip, row = st.columns([1, 9])
    with tip:
        with st.popover("?"):
            st.markdown(EPAT_EXPLAINER)
    row.markdown(f'<span class="chip chip-done">{EPAT_BATCH}</span>', unsafe_allow_html=True)
    st.write("")
    st.markdown(creator_story())


def _site():
    """'simple' on the second (dashboard) site, 'full' on the real site."""
    return st.session_state.get("site", "full")


@st.dialog("About Stock Explorer", width="large")
@er.guard()
def _dialog():
    simple = _site() == "simple"
    st.markdown("### What this project is")
    st.markdown(WHAT_IT_IS_SIMPLE if simple else WHAT_IT_IS)
    st.markdown("### How to use it")
    st.markdown(HOW_TO_USE_SIMPLE if simple else HOW_TO_USE)
    st.markdown("### Limitations")
    st.markdown(LIMITATIONS_SIMPLE if simple else LIMITATIONS)
    st.markdown("### Sources and credits")
    st.markdown(SOURCES_SIMPLE if simple else SOURCES)
    st.markdown("### Meet the creator")
    _creator_section()
    st.markdown("### Gratitude")
    st.markdown(gratitude_markdown())
    st.caption("Educational project. Not investment advice. No real money is involved.")


def icon():
    """The small circled 'i'. Clicking it opens the About page over the current page (no new tab)."""
    if st.button("i", key="about_btn", help="About this project"):
        _dialog()


CREST_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "mayo-crest.png")


@st.cache_resource
def _crest_html():
    """The school crest as a small inline image (empty if the file is missing)."""
    try:
        with open(CREST_PATH, "rb") as f:
            data = base64.b64encode(f.read()).decode()
    except OSError:
        return ""
    return f'<img class="brand-crest" src="data:image/png;base64,{data}" alt="Mayo College Girls School crest">'


def _dark_changed():
    """Switching the whole site dark or light also sets the price chart to match (it has its own switch to change after)."""
    st.session_state["dark_chart"] = st.session_state["dark_site"]


def title_row(title="Stock Explorer"):
    """The page title, with the Mayo College Girls School crest beside it and the About icon at the far right."""
    left, mid, right = st.columns([9, 2, 1])
    with left:
        st.markdown(f'<span class="about-row-marker"></span><div class="brand">{_crest_html()}<h1>{title}</h1></div>',
                    unsafe_allow_html=True)
    with mid:
        st.toggle("Dark mode", key="dark_site", on_change=_dark_changed)
    with right:
        icon()
