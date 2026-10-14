"""The "Daily check" tab: yesterday's indicators, today's trend call, and how today is going against it."""
import pandas as pd
import streamlit as st

from core import daily_check as dc
from core.charts import daily_check_chart, show as show_chart
from core.errors import guard
from core.formatting import format_inr
from core.live import REFRESH_SECONDS, live_quote
from core.market_hours import is_market_open, now_ist
from core.ui import plain_english

COLOUR = {"Up": "#1f9d73", "Down": "#d6453d", "Sideways": "#6b7785"}
VOTE_WORD = {1: ("Up", "#1f9d73"), -1: ("Down", "#d6453d"), 0: ("Neutral", "#6b7785")}


def evaluate_now(symbol, hist, offline=False):
    """(result, plan) for a company using the latest price; result is None when the history is too short."""
    now = now_ist().replace(tzinfo=None)
    open_now = is_market_open() and not offline
    quote = None if offline else live_quote(symbol)
    info = dc.plan(hist, now, live_price=quote["price"] if quote else None, market_open=open_now)
    return dc.evaluate(info["basis"], info), info


def _badge(text, colour):
    return f'<span style="background:{colour};color:#fff;padding:0.15rem 0.7rem;border-radius:999px;font-weight:700">{text}</span>'


def render(symbol, name, hist, offline=False):
    st.header("Daily check")
    st.markdown("**In short:** using only the data up to yesterday, the indicators below vote on which way today's price will "
                "lean. Then you can watch today's real price and see whether the call held up.")
    st.caption("A rule of thumb for learning, not a forecast and not advice. A single day proves nothing, so the track record "
               "further down shows how this rule has done over the last 60 trading days.")
    if offline:
        st.warning("Live prices are not available, so saved data is used and today's comparison may be out of date.")
    every = REFRESH_SECONDS if is_market_open() and not offline else None
    st.fragment(run_every=every)(_check)(symbol, name, hist, offline)
    result, info = evaluate_now(symbol, hist, offline)
    if result is None:
        return
    _track(info["complete"])
    plain_english(
        "- Each **indicator** looks at yesterday's data and votes **Up**, **Down** or **Neutral**.\n"
        "- The votes are added: **2 or more Up** means the call is Up, **2 or more Down** means Down, otherwise Sideways.\n"
        "- The **expected range** is yesterday's close plus or minus a typical day's swing (about two days in three end inside it).\n"
        "- A move smaller than a third of a typical swing counts as **sideways**, so tiny wobbles are not called up or down.\n"
        "- The **track record** replays the same rule on past days using only what was known the day before. If it is not clearly "
        "better than always guessing the usual outcome, that is the honest answer: day-to-day moves are very hard to call.")


@guard()
def _check(symbol, name, hist, offline):
    result, info = evaluate_now(symbol, hist, offline)
    if result is None:
        st.info("There is not enough price history for this company to run the check.")
        return
    target = result["target"]
    st.subheader(f"{name}: {'today' if target == now_ist().date() else target.strftime('%d %b %Y')}")
    if info["note"]:
        st.info(info["note"])

    # 1. the indicators, as of the day before
    st.markdown(f"**1. What the indicators said** (data up to {result['basis_date']:%A %d %b}, close {format_inr(result['prev_close'])})")
    rows = "".join(
        f"<tr><td><b>{n}</b></td><td>{reading}</td><td>{_badge(*VOTE_WORD[v])}</td><td>{why}</td></tr>"
        for n, reading, v, why in result["votes"])
    st.markdown(f'<table style="width:100%;border-collapse:collapse"><tr><th align="left">Indicator</th><th align="left">Reading</th>'
                f'<th align="left">Vote</th><th align="left">Why it matters</th></tr>{rows}</table>', unsafe_allow_html=True)

    # 2. the call
    p = result["prediction"]
    st.markdown(f"**2. The call for {'today' if target == now_ist().date() else 'that day'}:** {_badge(p, COLOUR[p])} "
                f"&nbsp; ({result['score']:+d} on a scale of {-result['n']} to {result['n']}, from {result['n']} indicators)",
                unsafe_allow_html=True)
    low, high = result["range"]
    st.caption(f"Expected range: {format_inr(low)} to {format_inr(high)} (yesterday's close plus or minus a typical day's swing of "
               f"{result['daily_vol'] * 100:.1f}%).")

    # 3. against reality
    st.markdown("**3. How it is going**")
    if result["actual"] is None:
        st.info("Today's price is not available yet. Come back once the market is open.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Price now" if result["status"] == "live" else "Price", format_inr(result["actual"]),
                  f"{result['change'] * 100:+.2f}% vs yesterday")
        c2.metric("What happened", result["actual_direction"])
        c3.metric("The call was", "Right" if result["matched"] else "Wrong")
        st.markdown(dc.headline(result))
        st.caption(("Inside" if result["in_range"] else "Outside") + " the expected range. "
                   + ("The market is open, so this can still change." if result["status"] == "live" else ""))

    show_chart(daily_check_chart(info["basis"]["Close"], result), key=f"dailychart_{symbol}")


@guard()
def _track(complete):
    st.markdown("**4. Track record (the last 60 trading days)**")
    rec = dc.track_record(complete)
    if rec is None:
        st.caption("Not enough history for a track record.")
        return
    c1, c2 = st.columns(2)
    c1.metric("This rule was right", f"{rec['hits']} of {rec['n']} days", f"{rec['accuracy'] * 100:.0f}%", delta_color="off")
    c2.metric("Always guessing the usual outcome", f"{rec['baseline'] * 100:.0f}%", "no-skill yardstick", delta_color="off")
    if rec["accuracy"] > rec["baseline"] + 0.05:
        st.success("Over this window the rule did better than the no-skill yardstick. That can still be luck, so treat it lightly.")
    else:
        st.warning("Over this window the rule was not clearly better than the no-skill yardstick. That is normal: calling a single "
                   "day's direction is very hard, and no indicator does it reliably.")
    table = pd.DataFrame([{"Date": r["date"].strftime("%d %b"), "Called": r["predicted"], "What happened": r["actual"],
                           "Move": f"{r['change'] * 100:+.2f}%", "Result": "Right" if r["matched"] else "Wrong"}
                          for r in reversed(rec["rows"][-10:])])
    st.caption("The last 10 days:")
    st.dataframe(table, hide_index=True, width="stretch")
