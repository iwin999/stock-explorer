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
     "text": "Type the name of a company here, like Tata, Reliance or Infosys, then press Enter. Or tap the box to see a list. "
             "Tapping a company opens its page."},
    {"page": "Home", "target": "tour_summary", "card": "bottom", "title": "Your practice money",
     "text": "This is your pretend portfolio. Green means you are up, red means you are down. Nothing here is real money, so "
             "you can learn without any risk."},
    {"page": "Home", "target": "tour_picks", "card": "top", "title": "Popular companies",
     "text": "Not sure where to start? These are well-known companies and how they moved today. Tap one to look at it."},
    {"page": "Company", "target": "tour_chart", "card": "bottom", "title": "The price over time",
     "text": "This line shows what the price did. Change 1 month, 6 months or 1 year with the buttons. A line going up "
             "means the price rose."},
    {"page": "Company", "target": "tour_verdict", "card": "bottom", "title": "How is it doing?",
     "text": "A few plain words about the company: is the price climbing or falling, is it calm or jumpy. It describes the "
             "past. It does not predict the future."},
    {"page": "Company", "target": "tour_trade", "card": "top", "title": "Buy or sell",
     "text": "Choose Buy or Sell, pick how much money, and press the button. You will see exactly what happens before you "
             "confirm. It uses practice money only."},
    {"page": "Portfolio", "target": "tour_holdings", "card": "bottom", "title": "What you own",
     "text": "Everything you have bought is listed here, with your gain or loss. Tap Sell next to anything to sell it."},
    {"page": "Portfolio", "target": "tour_leader", "card": "top", "title": "The leaderboard",
     "text": "See how everyone is doing. It ranks by percentage gain, so a smart small portfolio can beat a big one."},
    {"page": "Learn", "target": "tour_bot", "card": "top", "title": "Ask anything",
     "text": "Stuck on a word like 'dividend' or 'volatility'? Ask the helper. It explains in simple words, and you can "
             "change how simple it should be."},
    {"page": "Home", "target": "bottomnav", "card": "top", "title": "The menu",
     "text": "These four buttons take you around: Home, Company, Portfolio and Learn. You can take this tour again from "
             "the Learn page. Enjoy!"},
]


def target_css(target, dark=False):
    """CSS that lifts one box above the dark layer and outlines it."""
    box = "#1e222d" if dark else "#ffffff"
    position = "" if target == "bottomnav" else "position: relative;"
    return (f".st-key-{target} {{ {position} z-index: 1000 !important; background: {box} !important; border-radius: 14px;"
            f" box-shadow: 0 0 0 4px #2962ff, 0 0 0 200vmax rgba(0,0,0,0.72); }}")


def css(step, dark=False):
    """Everything the page needs for tour step number `step`."""
    s = STEPS[step]
    card_box = "#1e222d" if dark else "#ffffff"
    card_text = "#d1d4dc" if dark else "#1b2430"
    side = "top: 3.6rem;" if s["card"] == "top" else "bottom: 5.4rem;"
    return f"""<style>
{target_css(s['target'], dark)}
.st-key-tourblock {{ position: fixed; inset: 0; z-index: 999; width: 100vw; height: 100vh; }}
.st-key-tourblock * {{ opacity: 0; }}
.st-key-tourcard {{ position: fixed; {side} left: 50%; transform: translateX(-50%); width: min(94vw, 520px); z-index: 1002;
  background: {card_box}; color: {card_text}; border: 2px solid #2962ff; border-radius: 16px; padding: 0.9rem 1rem 0.7rem 1rem;
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
    return step if step is not None and 0 <= step < len(STEPS) else None


def _go(step, set_page):
    st.session_state["tour_step"] = step
    set_page(STEPS[step]["page"])


def start(set_page):
    _go(0, set_page)


def next_step(set_page, finish):
    step = st.session_state.get("tour_step", 0) + 1
    if step >= len(STEPS):
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
    s = STEPS[step]
    st.markdown(css(step, dark), unsafe_allow_html=True)
    with st.container(key="tourblock"):
        st.markdown("&nbsp;")
    with st.container(key="tourcard"):
        st.caption(f"Step {step + 1} of {len(STEPS)}")
        st.markdown(f"**{s['title']}**")
        st.write(s["text"])
        left, middle, right = st.columns([1, 1, 1.3])
        left.button("Back", key="tour_back", width="stretch", disabled=step == 0, on_click=back, args=(set_page,))
        middle.button("Skip", key="tour_skip", width="stretch", on_click=stop, args=(finish,))
        last = step == len(STEPS) - 1
        right.button("Done" if last else "Next", key="tour_next", type="primary", width="stretch",
                     on_click=next_step, args=(set_page, finish))
    scroll_script(s["target"])
