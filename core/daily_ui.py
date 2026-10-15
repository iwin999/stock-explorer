"""The "Daily check" tab: yesterday's indicators, today's call, and how today is going against it (mostly pictures)."""
import pandas as pd
import streamlit as st

from core import daily_check as dc
from core import daily_visuals as vis
from core.charts import daily_check_chart, show as show_chart
from core.errors import guard
from core.formatting import format_inr
from core.live import REFRESH_SECONDS, live_quote
from core.market_hours import is_market_open, now_ist
from core.ui import plain_english


def evaluate_now(symbol, hist, offline=False, scales=False):
    """(result, plan) for a company using the latest price; result is None when the history is too short."""
    now = now_ist().replace(tzinfo=None)
    open_now = is_market_open() and not offline
    quote = None if offline else live_quote(symbol)
    info = dc.plan(hist, now, live_price=quote["price"] if quote else None, market_open=open_now)
    return dc.evaluate(info["basis"], info, scales), info


def render(symbol, name, hist, offline=False):
    st.markdown(vis.CSS, unsafe_allow_html=True)
    st.header("Daily check")
    st.caption("Yesterday's indicators vote on today's direction, then today's real price is held up against the call. "
               "A learning tool, not a forecast or advice.")
    if offline:
        st.warning("Live prices are not available, so saved data is used and today's comparison may be out of date.")
    every = REFRESH_SECONDS if is_market_open() and not offline else None
    st.fragment(run_every=every)(_check)(symbol, name, hist, offline)
    _, info = evaluate_now(symbol, hist, offline)
    _track(info["complete"])
    _explain()


@guard()
def _check(symbol, name, hist, offline):
    result, info = evaluate_now(symbol, hist, offline)
    if result is None:
        st.info("There is not enough price history for this company to run the check.")
        return
    today = now_ist().date()
    target_word = "today" if result["target"] == today else result["target"].strftime("on %d %b")
    if info["note"]:
        st.info(info["note"])
    voters = [v for v in result["votes"] if v["voting"]]
    context = [v for v in result["votes"] if not v["voting"]]

    # the call, as one picture
    st.markdown(vis.hero(result["prediction"], result["score"], voters, target_word), unsafe_allow_html=True)
    st.caption(f"Based on data up to {result['basis_date']:%A %d %b} (close {format_inr(result['prev_close'])}).")

    # the call against reality
    if result["actual"] is None:
        st.info("Today's price is not available yet. Check back once the market is open.")
    else:
        st.markdown(vis.versus(result["prediction"], result["actual_direction"], result["matched"]), unsafe_allow_html=True)
        st.markdown(vis.range_bar(result["range"][0], result["range"][1], result["prev_close"], result["actual"],
                                  "Now" if result["status"] == "live" else "Close"), unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Now" if result["status"] == "live" else "Close", format_inr(result["actual"]), f"{result['change'] * 100:+.2f}%")
        c2.metric("Expected range", f"{result['range'][0]:,.0f} to {result['range'][1]:,.0f}")
        c3.metric("Inside the range?", "Yes" if result["in_range"] else "No")
        if result["status"] == "live":
            st.caption("The market is open, so this can still change.")

    with st.expander("Price chart: the last weeks, the expected range and today's price"):
        show_chart(daily_check_chart(info["basis"]["Close"], result), key=f"dailychart_{symbol}")

    # the indicators, as cards
    st.subheader("The six indicators that vote")
    st.markdown(vis.cards(voters), unsafe_allow_html=True)
    with st.expander("More indicators, shown for context (not counted in the call)"):
        st.markdown(vis.cards(context), unsafe_allow_html=True)
        st.caption("RSI, MACD, ADX, Supertrend, Ichimoku and Volume are popular, but in our tests they did not make the call "
                   "more accurate, so they are shown but do not vote.")


@guard()
def _track(complete):
    st.subheader("How reliable has this been? (last 60 trading days)")
    rec = dc.track_record(complete)
    if rec is None:
        st.caption("Not enough history for a track record.")
        return
    if rec["call_accuracy"] is not None:
        st.markdown(vis.bars(rec["call_accuracy"] * 100, 50), unsafe_allow_html=True)
        st.caption(f"Days the rule made a clear Up or Down call and the price really moved: right on {rec['call_hits']} of {rec['call_n']}.")
    else:
        st.caption("The rule made no clear Up or Down calls in this window.")
    st.markdown(vis.strip(rec["rows"]), unsafe_allow_html=True)
    st.caption("Each square is one day: green = the call was right, red = wrong. Hover for the day.")
    if rec["call_accuracy"] is None or rec["call_n"] < 30:
        st.info("Only a handful of clear calls in this window, too few to say anything. The overall test across 138 companies "
                "(see 'How this works' below) is a better guide.")
    elif rec["call_accuracy"] > 0.5 + 0.08:
        st.success("Better than a coin toss over this window. That can still be luck over a few weeks.")
    else:
        st.warning("Close to or below a coin toss over this window. That is normal: one day's direction is very hard to call.")
    with st.expander("The last 10 days in detail"):
        table = pd.DataFrame([{"Date": r["date"].strftime("%d %b"), "Called": r["predicted"], "What happened": r["actual"],
                               "Move": f"{r['change'] * 100:+.2f}%", "Result": "Right" if r["matched"] else "Wrong"}
                              for r in reversed(rec["rows"][-10:])])
        st.dataframe(table, hide_index=True, width="stretch")


def _explain():
    plain_english(
        "- **The call:** six indicators look only at data up to yesterday and each votes Up, Down or Neutral. Two or more net "
        "Up votes means Up, two or more net Down means Down, anything else Sideways.\n"
        "- **Expected range:** yesterday's close plus or minus a typical day's swing; about two days in three end inside it.\n"
        "- **Sideways** means a move smaller than a third of a typical day's swing.\n"
        "- **How the six were chosen:** we tested 18 well-known indicators on about 200,000 company-days of NSE prices "
        "(138 companies, 2019 to 2026), choosing on the first 70% of the dates and checking on the last 30%. Most scored "
        "49% to 51% at calling the next day, which is a coin toss. The six that voting uses (trend, Bollinger band, Stochastic "
        "RSI, money flow, where the day closed, and yesterday's move) held up best, at about 51% to 52% on the days they made a clear call.\n"
        "- **What that means:** a small edge, not a crystal ball. RSI, MACD, ADX, Supertrend, Ichimoku and Volume, popular as "
        "they are, did not improve it, so they are shown for context only.\n"
        "- **Not advice.** Past patterns do not guarantee anything.", label="How this works and how the indicators were chosen")
