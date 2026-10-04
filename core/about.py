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

WHAT_IT_IS = """\
**Stock Explorer** is an educational website that makes Indian (NSE) stocks easier to understand. You can look at price charts \
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


def creator_markdown():
    name = _secret("creator", "")
    reason = _secret("reason", "I wanted stock markets to feel less intimidating, especially for people who are not finance "
                               "experts.")
    hello = f"Hello, I'm {name}, the creator of {SITE_NAME}." if name else f"Hello! I'm the student who created {SITE_NAME}."
    return (f"{hello} {reason}\n\n"
            "I am studying for the **CMT (Chartered Market Technician) designation**: I have passed Level II and am preparing "
            "for Level III. The ideas on this site, from the indicators to the fusion analysis, come from what I have been "
            "learning. I built it with an AI coding assistant, which wrote the code while I chose what to build and checked "
            "that each part made sense.\n\n"
            "If you find something that looks wrong, or have an idea, please tell the admin at "
            f"[{er.admin_email()}](mailto:{er.admin_email()}).")


def gratitude_markdown():
    extra = _secret("thanks_extra", "")
    return ("**Thank you.** To my school and my teachers, for giving me the opportunity to build this and show it at the "
            "exhibition, and for your encouragement and guidance along the way. To my family, for their patience and support. "
            "To the CMT community for the learning that inspired this project, and to everyone who shares open-source software "
            "and data. And thank you to every visitor for trying it." + (f" {extra}" if extra else ""))


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
    st.markdown(creator_markdown())
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
