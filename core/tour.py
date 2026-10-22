"""The guided tour of the simple site: the page dims, one feature at a time is lit up, and a bubble says what it is for.

How it works (no JavaScript needed for the look): while a step is active, a CSS rule lifts the chosen box above a dark
layer and draws a blue outline around it; a see-through layer blocks clicks on everything else; and a card with
Back / Next / Skip sits above the bottom menu or under the top bar. A tiny script scrolls the lit-up box into view.
"""
import streamlit as st
import streamlit.components.v1 as components

# page = which page the step is on; target = the box lit up (a st.container key); card = where the card sits.
STEPS = [
    {"page": "Home", "target": "tour_search", "card": "bottom", "title": "Find any company",
     "text": "Type the name of a company, such as Tata, Reliance or Infosys, then press Enter. A small spelling slip is fine, and the closest "
             "matches are listed best first. You can also tap the box to browse the list. Tapping a company opens its page, with its price "
             "chart and readings."},
    {"page": "Home", "target": "tour_summary", "card": "bottom", "title": "Your practice money",
     "text": "This is your pretend portfolio: what your cash and everything you own is worth, and how much you have gained or lost since you "
             "started. Green means you are up and red means you are down. The prices are real but the money is not, so nobody can lose "
             "anything while they learn."},
    {"page": "Home", "target": "tour_picks", "card": "top", "title": "Popular companies",
     "text": "Not sure where to start? These are well-known companies, with how their price moved today. Tap one to open it. Looking at a few "
             "different companies is the quickest way to see how prices behave."},
    {"page": "Company", "target": "tour_chart", "card": "bottom", "title": "The price over time",
     "text": "This line is the history of the price. Use the buttons to look at 1 month, 6 months or 1 year. A line that climbs means the "
             "price rose over that time, and a line that falls means it dropped. Zooming out shows the bigger trend, and zooming in shows "
             "the recent moves."},
    {"page": "Company", "target": "tour_verdict", "card": "bottom", "title": "How is it doing?",
     "text": "A few plain sentences about the company: is the price climbing or falling, and is it calm or jumpy. They are worked out from past "
             "prices, so they describe what has already happened. They cannot tell you what happens next."},
    {"page": "Company", "target": "tour_trade", "card": "top", "title": "Buy or sell",
     "text": "Choose Buy or Sell, pick how much money to use, and press the button. Before you confirm, the page tells you exactly how many "
             "shares you would get and what it costs. It uses practice money only, and you can sell later to see how you did."},
    {"page": "Portfolio", "target": "tour_holdings", "card": "bottom", "title": "What you own",
     "text": "Every share you have bought is listed here, with how many you hold, what you paid on average, and your profit or loss on it. Tap "
             "Sell next to anything to sell it. Your gain or loss changes as the price moves."},
    {"page": "Portfolio", "target": "tour_leader", "card": "top", "title": "The leaderboard",
     "text": "See how everyone is doing. People are ranked by percentage gain, which is how much their money has grown since they started, so "
             "a smart small portfolio can beat a big one."},
    {"page": "Learn", "target": "tour_bot", "card": "top", "title": "Ask anything",
     "text": "Stuck on a word like dividend or volatility? Ask the helper. It explains in simple words, and you can change how simple it "
             "should be, from very simple to adult language. It only teaches; it never gives investment advice."},
    {"page": "Home", "target": "ask_bubble", "card": "top", "title": "Ask me anything",
     "text": "This round chat button stays in the corner on every page. Tap it and type a question, or pick a starter: what a word means, "
             "how a chart works, how to use the site. It answers from notes written for this site, in simple words, and it never gives "
             "investment advice."},
    {"page": "Home", "target": "guide_btn", "card": "top", "title": "Read the guide",
     "text": "This small document button above the chat button opens the presenter's guide, a PDF that explains every part of the site twice: "
             "once in simple words with an everyday example, and once in proper finance language. It opens in a new tab, so you do not "
             "lose your place here."},
    {"page": "Home", "target": "bottomnav", "card": "top", "title": "The menu",
     "text": "These four buttons take you around: Home, Company, Portfolio and Learn. You can take this tour again from the Learn page. "
             "Enjoy!"},
]


# The tour of the wide dashboard layout: the same idea, with the dashboard's own parts.
DASH_STEPS = [
    {"target": "tm_top", "card": "bottom", "title": "Your practice money",
     "text": "The top bar shows what your practice portfolio is worth right now, with the percentage you have gained or lost since you "
             "started. Nothing here is real money. Dark mode changes the colours for a dim room. Dashboard view switches between this wide "
             "screen and a simpler phone-style layout. Demo plays a self-running demonstration, Tour is this walk-through, and the i opens "
             "the full story of the project."},
    {"target": "tm_search", "card": "bottom", "title": "Find any company",
     "text": "Every company listed on the NSE and the BSE is in this box. Type a name, a small spelling slip is fine, and press Enter to see "
             "the closest matches, or click the box to browse the list. The whole screen then switches to that company: its price chart, its "
             "indicators and its strategy readings."},
    {"target": "tm_chartarea", "card": "bottom", "title": "The price chart",
     "text": "Each candle is one day, week or month of trading. Its body runs from the opening to the closing price, green when the price rose "
             "and red when it fell, and the thin lines show the highest and lowest prices. The bars underneath are volume, how many shares "
             "changed hands. Choose 1, 2 or 4 charts side by side, Day, Week or Month candles, and how far back to look. Fibonacci draws the "
             "levels where prices often pause, and the Dark switch darkens just the charts."},
    {"target": "tm_trade", "card": "top", "title": "Buy, Sell and Exit all",
     "text": "These buttons let you practise trading with virtual money at real prices. Buy opens a form where you choose a share, an ETF or "
             "bond, a future or an option, and how many to buy. The form stays open after each order, so you can place the next one. Sell "
             "works once you hold something, and Exit all sells everything at once. Nothing is charged and nothing is real."},
    {"target": "tm_ind", "card": "bottom", "title": "Six indicators",
     "text": "Each gauge answers one question about the chart: how fast the price has moved (RSI), whether momentum is building (MACD), how "
             "strong the trend is (ADX), how stretched the price is (Z-score), whether volume is backing the move (On-Balance Volume), and "
             "where the price sits in its usual range (Bollinger band). Red leans down, green leans up, and the pointer shows where it "
             "stands. Hover over a name for a plain-words explanation. They are clues, and they can disagree."},
    {"target": "tm_baro", "card": "top", "title": "The combined strategy reading",
     "text": "Five strategies from the CMT curriculum each vote Up, Down or Neutral for this company, and the dial adds up the votes. A "
             "needle on the left means most of them read down, on the right most read up, and in the middle they disagree. It describes "
             "what the charts show today. It is not a forecast."},
    {"target": "tm_lists", "card": "top", "title": "What you hold",
     "text": "Everything you have bought, and the recent sales you have made. For each holding you see how many shares you own and your profit "
             "or loss on it, in rupees and in percent. The ring below splits your money between shares, ETFs, bonds, futures, options and "
             "cash."},
    {"target": "tm_board", "card": "top", "title": "The leaderboard",
     "text": "Everyone is ranked by percentage return, which is how much their money has grown since they started, so a small portfolio can "
             "beat a big one. The board shows the top four and where you stand among everyone. It refreshes every half minute."},
    {"target": "tm_strat", "card": "top", "title": "The strategies behind the reading",
     "text": "Five methods from the CMT curriculum (Fusion stage, Dow Theory, relative strength, Wyckoff and Fibonacci) and a machine-learning "
             "model, each with its vote. The last column says how often each one was right on this company's own history, which is usually "
             "about half the time, no better than a coin toss, and we say so honestly. Click Full view for a chart and a plain explanation "
             "of what a strategy is doing. They describe; they do not recommend."},
    {"target": "ask_bubble", "card": "top", "title": "Ask me anything",
     "text": "This round chat button stays in the corner whatever you are doing. Click it and type a question, or pick a starter: what an "
             "indicator means, how a strategy works, how to use this screen. It answers from notes written for this site, in simple words, "
             "or in adult language if you ask. It teaches, and it never gives investment advice."},
    {"target": "guide_btn", "card": "top", "title": "Read the guide",
     "text": "This small document button above the chat button opens the presenter's guide, a PDF that explains every part of this screen twice: "
             "once in simple words with an everyday example, and once in proper finance language. It starts from what a share is and builds "
             "up, so anyone can read it from the beginning. It opens in a new tab, so you do not lose your place here."},
]


def _accent(dark):
    """The calm blue used for the outline and the card border (a soft steel blue, never a bright one)."""
    return "#8fa8d4" if dark else "#2f5597"


def steps():
    """The steps of the tour that is running: the dashboard's or the phone layout's."""
    return DASH_STEPS if st.session_state.get("tour_kind") == "dash" else STEPS


def target_css(target, dark=False):
    """CSS that lifts one box above the dark layer and outlines it."""
    accent = _accent(dark)
    box = "#1e222d" if dark else "#ffffff"
    position = "" if target in ("bottomnav", "ask_bubble", "guide_btn") else "position: relative;"          # these stay fixed to the screen
    radius = "50%" if target in ("ask_bubble", "guide_btn") else "14px"
    return (f".st-key-{target} {{ {position} z-index: 1000 !important; background: {box} !important; border-radius: {radius};"
            f" box-shadow: 0 0 0 3px {accent}, 0 0 0 200vmax rgba(0,0,0,0.72) !important; }}")


def css(step, dark=False):
    """Everything the page needs for tour step number `step`."""
    s = steps()[step]
    accent = _accent(dark)
    card_box = "#1e222d" if dark else "#ffffff"
    card_text = "#d1d4dc" if dark else "#1b2430"
    bottom = "1.5rem" if st.session_state.get("tour_kind") == "dash" else "5.4rem"        # the phone layout has a menu along the bottom
    side = "top: 3.6rem;" if s["card"] == "top" else f"bottom: {bottom};"
    return f"""<style>
{target_css(s['target'], dark)}
.st-key-tourblock {{ position: fixed; inset: 0; z-index: 999; width: 100vw; height: 100vh; }}
.st-key-tourblock * {{ opacity: 0; }}
.st-key-tourcard {{ position: fixed; {side} left: 50%; transform: translateX(-50%); width: min(94vw, 520px); z-index: 1002;
  background: {card_box}; color: {card_text}; border: 2px solid {accent}; border-radius: 16px; padding: 0.9rem 1rem 0.7rem 1rem;
  box-shadow: 0 8px 30px rgba(0,0,0,0.45); }}
.st-key-tourcard [data-testid="stMarkdownContainer"]:not(button *) p, .st-key-tourcard [data-testid="stCaptionContainer"] {{ color: {card_text}; }}
.st-key-tourcard [data-testid="stHorizontalBlock"] {{ flex-wrap: nowrap !important; gap: 0.4rem !important; }}
.st-key-tourcard [data-testid="stColumn"] {{ min-width: 0 !important; }}
.st-key-tourcard [data-testid="stVerticalBlock"] {{ gap: 0.4rem; }}
.st-key-tourcard button {{ min-height: 2.6rem; }}
</style>"""


def scroll_script(target):
    """Scrolls the lit-up box to the middle of the screen (best effort; the tour still works if the browser refuses)."""
    components.html(
        "<script>try{const el=window.parent.document.querySelector('.st-key-" + target + "');"
        "if(el){el.scrollIntoView({block:'center',behavior:'smooth'});}}catch(e){}</script>", height=0)


# ---------------- state ----------------
def active():
    """The current step number, or None when no tour is running."""
    step = st.session_state.get("tour_step")
    return step if step is not None and 0 <= step < len(steps()) else None


def _go(step, set_page):
    st.session_state["tour_step"] = step
    page = steps()[step].get("page")
    if page:
        set_page(page)


def start(set_page, kind="phone"):
    """Begin the tour of the phone layout (kind="phone") or of the wide dashboard (kind="dash")."""
    st.session_state["tour_kind"] = kind
    _go(0, set_page)


def next_step(set_page, finish):
    step = st.session_state.get("tour_step", 0) + 1
    if step >= len(steps()):
        stop(finish)
    else:
        _go(step, set_page)


def back(set_page):
    _go(max(0, st.session_state.get("tour_step", 0) - 1), set_page)


def stop(finish):
    st.session_state["tour_step"] = None
    finish()


def render(set_page, finish, dark=False):
    """Draw the dimming layer, the outline and the card for the running step (call after the page has been drawn)."""
    step = active()
    if step is None:
        return
    s = steps()[step]
    st.markdown(css(step, dark), unsafe_allow_html=True)
    with st.container(key="tourblock"):
        st.markdown("&nbsp;")
    with st.container(key="tourcard"):
        st.caption(f"Step {step + 1} of {len(steps())}")
        st.markdown(f"**{s['title']}**")
        st.write(s["text"])
        left, middle, right = st.columns([1, 1, 1.3])
        left.button("Back", key="tour_back", width="stretch", disabled=step == 0, on_click=back, args=(set_page,))
        middle.button("Skip", key="tour_skip", width="stretch", on_click=stop, args=(finish,))
        last = step == len(steps()) - 1
        right.button("Done" if last else "Next", key="tour_next", type="primary", width="stretch",
                     on_click=next_step, args=(set_page, finish))
    scroll_script(s["target"])
