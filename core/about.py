"""The About page: opened by the small circled "i" at the top right of every page.

All the wording lives here so it is easy to edit. The creator's first name, extra thanks and a one-line reason can also be
set in the app's secrets without touching the code:

    [about]
    creator = "Asha"
    reason = "I wanted markets to feel less intimidating."
    thanks_extra = "...and my friends who tested it."
"""
import streamlit as st

from core import errors as er

SITE_NAME = "Stock Explorer"

# ---- the creator (edit here, or override with [about] in the app's secrets) ----
CREATOR_NAME = "Freya Shah"
CREATOR_CLASS = "PreSC Commerce - B"
CREATOR_SCHOOL = "Mayo College Girls School"
CREDENTIALS = [
    ("CMT Level I", "Passed"),
    ("CMT Level II", "Passed"),
    ("CMT Level III", "Appearing"),
]
EPAT_BATCH = "EPAT Batch 72"

CMT_EXPLAINER = """\
**CMT: Chartered Market Technician**

A global professional qualification in **technical analysis**: reading price and volume to understand what the market is \
doing. It is awarded by the CMT Association and is taken in three levels.

- **Level I** covers the foundations: charts, indicators, and how markets behave.
- **Level II** applies them: building and testing analysis, risk management, and combining signals.
- **Level III** is the most advanced: portfolio construction, behavioural finance, and approaches such as the **fusion \
analysis** used in this app.

It is usually pursued by people already working in finance, which makes passing two levels while still at school a real \
achievement."""

EPAT_EXPLAINER = """\
**EPAT: Executive Programme in Algorithmic Trading**

A professional programme from **QuantInsti** that teaches how to trade with code and data: Python programming, statistics, \
financial markets, and how to design, test and run automated trading strategies.

"**Batch 72**" is the cohort of learners Freya studied with. Like the CMT, it is usually taken by working professionals, so \
it is a serious step for a school student, and the skills behind the simulations and strategy tests in this app are exactly \
the kind the programme teaches."""

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
- Prices of shares, ETFs, bond funds and the Nifty 50, and companies' yearly results: [Yahoo Finance](https://finance.yahoo.com), \
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

*This is an independent student project. It is not affiliated with, or endorsed by, the NSE, Yahoo, the CMT Association, \
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


def gratitude_markdown():
    extra = _secret("thanks_extra", "")
    return (f"**Thank you, {CREATOR_SCHOOL} and the IT department,** for giving me this opportunity. And thank you, the "
            "visitor, for taking the time to use it." + (f" {extra}" if extra else ""))


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
    row.markdown(f'<span class="chip chip-done">Part of {EPAT_BATCH}</span>', unsafe_allow_html=True)
    st.write("")
    st.markdown(creator_story())


@st.dialog("About Stock Explorer", width="large")
def _dialog():
    st.markdown("### What this project is")
    st.markdown(WHAT_IT_IS)
    st.markdown("### How to use it")
    st.markdown(HOW_TO_USE)
    st.markdown("### Limitations")
    st.markdown(LIMITATIONS)
    st.markdown("### Sources and credits")
    st.markdown(SOURCES)
    st.markdown("### Meet the creator")
    _creator_section()
    st.markdown("### Gratitude")
    st.markdown(gratitude_markdown())
    st.caption("Educational project. Not investment advice. No real money is involved.")


def icon():
    """The small circled 'i'. Clicking it opens the About page over the current page (no new tab)."""
    if st.button("i", key="about_btn", help="About this project"):
        _dialog()


def title_row(title="Stock Explorer"):
    """The page title with the About icon at the far right."""
    left, right = st.columns([14, 1])
    with left:
        st.markdown('<span class="about-row-marker"></span>', unsafe_allow_html=True)
        st.title(title)
    with right:
        icon()
