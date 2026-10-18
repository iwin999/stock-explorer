"""A self-playing demo of the dashboard, for the people presenting it.

Pressing the Demo button starts a loop that drives the real screen by itself: it searches a company, switches the Day, Week and Month
candles, turns on the Fibonacci lines, shows four charts at once, lights up the indicators, the dial and the strategies, opens a
strategy's Full view, makes a practice buy, and points at the chat button, with a big plain-words caption (and, if switched on, a spoken
voice) for every step. Then it carries on with another company until somebody touches the screen, which stops it at once.

The settings DEMO_SPEED (an environment variable, 1 by default; 0.35 plays about three times faster) and DEMO_START_STEP (0 by default) are only for testing.

Nothing the demo does touches a visitor's own portfolio: it works on a throwaway pretend account that is never saved, and the visitor's
own account, company and chart settings are put back exactly as they were when it stops.

How it fits in: terminal_ui.run() calls apply() before it draws anything (so the demo can set the company and the chart controls),
after_price() once the price is known (for the practice buy), full_view_name() when it draws the strategies table, and render() at the
end (the caption card, the spotlight, the timer that moves to the next step, and the voice).
"""
import copy
import json
import os
import time

import streamlit as st
import streamlit.components.v1 as components

from core import companies
from core.formatting import format_inr
from core.trading import Portfolio

MISSING = "__missing__"
COMPANIES = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "ITC.NS"]        # one per trip round the loop
CHART_KEYS = ["company", "mtf_layout", "mtf_tf", "period_seg", "show_fib", "dark_chart"]     # widget settings the demo changes and puts back
SPEEDS = ["0.75×", "1×", "1.25×", "1.5×", "2×"]                    # like a video's playback speed
PRACTICE_BUY = 10000.0                                              # rupees of pretend money spent in the demo buy

NORMAL = {"mtf_layout": "1 chart", "mtf_tf": "Daily", "period_seg": "1 year", "show_fib": False}

STEPS = [
    {"title": "Practice money, real prices",
     "say": "This number is your practice portfolio: Rs 1,00,000 of pretend money. The share prices you will see are real market prices, so you learn how real trading feels without any real risk. The number changes as the value of what you own changes.",
     "set": dict(NORMAL), "target": {"sel": ".tm-value", "fallback": "tm_top"}, "side": "below"},
    {"title": "Pick any company",
     "say": "Every company listed on the NSE and the BSE is in this box. Type a name, a small spelling slip is fine, and the whole screen switches to that company. We will look at {name}, one of India's best known companies.",
     "set": {"company": "{symbol}"}, "target": {"sel": ".st-key-tm_search [data-testid=\"stSelectbox\"]", "fallback": "tm_search"}, "side": "below"},
    {"title": "How to read the price chart",
     "say": "Each bar is one day of trading. The thick part runs from the day's opening price to its closing price. Green means the price closed higher than it opened, red means lower. The thin lines show the highest and lowest price of the day. The bars underneath show volume, which is how many shares changed hands.",
     "set": {"mtf_tf": "Daily"}, "target": {"sel": ".st-key-tm_chartarea [data-testid=\"stPlotlyChart\"]", "fallback": "tm_chartarea", "parts": [{"x": 0.72, "y": 0.1, "w": 0.26, "h": 0.5}, {"x": 0.76, "y": 0.15, "w": 0.22, "h": 0.32}]}, "side": "left"},
    {"title": "Zooming out: weeks",
     "say": "Choosing Week turns every bar into a whole week. The small daily wiggles fade away, so the direction of the trend is much easier to see. Analysts look at several timeframes because the same price can look calm in one and wild in another.",
     "set": {"mtf_tf": "Weekly"}, "target": {"sel": ".st-key-tm_chartbar button", "text": "^Week$", "fallback": "tm_chartbar"}, "side": "below"},
    {"title": "Zooming out further: months",
     "say": "Now each bar is a month. This is the long view: where the price has been heading over years, not days. A fall that looks frightening on a daily chart can turn out to be a small dip in a long climb.",
     "set": {"mtf_tf": "Monthly"}, "target": {"sel": ".st-key-tm_chartbar button", "text": "^Month$", "fallback": "tm_chartbar"}, "side": "below"},
    {"title": "Fibonacci levels",
     "say": "After a big rise or fall, prices often take back part of the move before carrying on. The Fibonacci lines mark 38.2%, 50% and 61.8% of that move, the places where traders often expect a pause. They show where support or resistance may be. They are a guide, not a prediction.",
     "set": {"mtf_tf": "Daily", "show_fib": True}, "target": {"sel": ".st-key-tm_chartbar [data-testid=\"stCheckbox\"]", "text": "Fibonacci", "fallback": "tm_chartbar"}, "side": "below"},
    {"title": "Four charts at once",
     "say": "Professionals rarely trust a single timeframe. The long chart shows the main trend and the short chart helps with timing. Pressing 4 shows four charts side by side, each in its own timeframe, so you can compare the big picture and the detail at a glance.",
     "set": {"show_fib": False, "mtf_layout": "4 charts"}, "target": {"sel": ".st-key-tm_chartbar button", "text": "^4$", "fallback": "tm_chartbar"}, "side": "below"},
    {"title": "Six indicators",
     "say": "Each gauge asks one question. How fast has the price moved, that is RSI. Is momentum building, that is MACD. Is there a strong trend, that is ADX. How stretched is the price, the Z-score. Is volume behind the move, On-Balance Volume. Where is it in its usual range, the Bollinger band. Red leans down and green leans up. They are clues, and they can disagree.",
     "set": {"mtf_layout": "1 chart"}, "target": {"key": "tm_ind"}, "side": "left"},
    {"title": "The combined reading",
     "say": "Five strategies from the CMT exam each vote Up, Down or Neutral, and the dial adds up the votes. Leans down means more of them read down than up. It describes what the charts show today. It does not tell you what will happen tomorrow.",
     "set": {}, "target": {"key": "tm_baro"}, "side": "right"},
    {"title": "Five strategies and a model",
     "say": "Fusion stage, Dow Theory, relative strength, Wyckoff and Fibonacci are methods from the professional CMT curriculum. The ML model is an estimate a computer learned from old prices. The last column is an honest test of how often each one was right on this company's own history. Around 50 percent means no better than a coin toss, and we show that on purpose.",
     "set": {}, "target": {"key": "tm_strat", "parts": [{"x": 0, "y": 0, "w": 1, "h": 0.5}, {"x": 0, "y": 0, "w": 1, "h": 0.3}]}, "side": "above"},
    {"title": "Inside a strategy: Dow Theory",
     "say": "Each strategy has a full view. Dow Theory looks at the swing points of the price, the peaks and the dips. If every peak and every dip is higher than the one before, the trend is up, like climbing stairs. If both keep getting lower, the trend is down. The triangles mark those swing points.",
     "set": {}, "target": None, "full_view": "Dow Theory", "side": "bottom"},
    {"title": "Placing a practice trade",
     "say": "Buy opens an order form where you choose a share, an ETF, a bond, a future or an option, and how many to buy. We are buying about Rs 10,000 worth of {name} with pretend money. Prices are real, nothing is charged, and you can sell whenever you like.",
     "set": {}, "target": {"sel": ".st-key-tm_trade button", "text": "^Buy$", "fallback": "tm_trade"}, "buy": True, "side": "above"},
    {"title": "Your holdings update",
     "say": "Now the list shows what we own and our profit or loss on it. The ring shows how our money is split between shares and cash. The portfolio value counts the shares at their latest price. Right after buying, the profit is about zero, because we paid the market price.",
     "set": {}, "target": {"key": "tm_lists"}, "side": "right"},
    {"title": "Who is doing best",
     "say": "Everyone is ranked by percentage return, which is how much their money has grown since they started. That is why a small portfolio can beat a big one. The board shows the top four and where you stand among everyone.",
     "set": {}, "target": {"key": "tm_board"}, "side": "right"},
    {"title": "Meet the helper",
     "say": "If you meet a word you do not know, such as RSI or futures, there is a helper for that. It is this round chat button, and it stays in the corner whatever you are doing. It answers from notes written for this site, in simple words or in adult language, and it never gives investment advice. Let us try it.",
     "set": {}, "target": {"sel": ".st-key-ask_bubble [data-testid=\"stPopoverButton\"]", "fallback": "ask_bubble"}, "act": "close_chat", "side": "left"},
    {"title": "Asking the helper a question",
     "say": "We open the helper and type a question: what does the RSI number mean? Watch it being typed, then the Ask button is pressed. The helper looks the question up in its notes.",
     "set": {}, "target": {"sel": "[data-testid=\"stPopoverBody\"]", "fallback": "ask_bubble"}, "act": "ask", "question": "What does the RSI number mean?", "side": "left"},
    {"title": "Reading the answer",
     "say": "Here is the answer, in plain words. It explains what RSI is, how it is worked out and how to read it. Under the answer it offers related questions to follow up, and you can ask for a simpler or a more detailed explanation. Everything it says comes from notes written for this site.",
     "set": {}, "target": {"sel": "[data-testid=\"stPopoverBody\"]", "fallback": "ask_bubble"}, "act": "open_chat", "side": "left"},
    {"title": "Now it is your turn",
     "say": "That was the demo. Touch the screen to try it yourself. The Tour button walks you through every part of the screen one step at a time, and the Demo button plays this again. We keep playing until you touch the screen.",
     "set": {}, "target": {"sel": ".st-key-tour_btn_top button", "fallback": "tm_top"}, "act": "close_chat", "side": "below"},
]

CSS = """<style>
.st-key-demo_card { position: fixed; left: 50%; bottom: 1.1rem; transform: translateX(-50%); width: min(94vw, 780px); z-index: 2147483000;
  background: #1d3557; color: #ffffff; border: 2px solid #8fa8d4; border-radius: 18px; padding: 0.8rem 1.2rem 0.7rem 1.2rem;
  box-shadow: 0 10px 34px rgba(0,0,0,0.5); }
.st-key-demo_card * { color: #ffffff; }
.st-key-demo_card .demo-badge { font-size: .78rem; letter-spacing: .12em; text-transform: uppercase; font-weight: 800; color: #b9ccf6; margin-bottom: .25rem; }
.st-key-demo_card .demo-title { font-size: 1.45rem; font-weight: 800; line-height: 1.2; margin-bottom: .3rem; }
.st-key-demo_card .demo-say { font-size: 1.12rem; font-weight: 500; line-height: 1.42; margin-bottom: .5rem; }
.st-key-demo_card .demo-hint { font-size: .85rem; opacity: .8; }
.st-key-demo_card [data-testid="stHorizontalBlock"] { align-items: center; gap: .6rem; }
.st-key-demo_card button { background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.5); }
.st-key-demo_card button:hover { background: rgba(255,255,255,0.22); }
.st-key-demo_card [data-testid="stToggle"] label p { font-size: .95rem; }
.st-key-demo_card [data-testid="stToggle"] label > div:not([data-testid="stWidgetLabel"]) { background: rgba(255,255,255,0.35) !important; }
.st-key-demo_card [data-testid="stToggle"] label:has(input:checked) > div:not([data-testid="stWidgetLabel"]) { background: #6f9bff !important; }
.st-key-demo_card [data-testid="stCaptionContainer"] { color: #ffffff; }
.st-key-demo_dots { margin-top: .1rem; }
.st-key-demo_card.callout { width: min(92vw, 500px); }
.st-key-demo_card.callout .demo-title { font-size: 1.3rem; }
.st-key-demo_card.callout .demo-say { font-size: 1.02rem; }
.st-key-demo_card.callout .demo-hint { display: none; }
.st-key-demo_card .demo-hint { margin-top: .35rem; }
.st-key-demo_card [data-testid="stColumn"] { min-width: 0 !important; }
.st-key-demo_card [data-testid="stButtonGroup"] { gap: .2rem; flex-wrap: nowrap; }
.st-key-demo_card [data-testid="stButtonGroup"] button { background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.35); padding: .15rem .5rem; min-height: 2rem; }
.st-key-demo_card [data-testid="stButtonGroup"] button p { font-size: .85rem; }
.st-key-demo_card [data-testid="stButtonGroup"] button[data-selected="true"], .st-key-demo_card [data-testid="stButtonGroup"] button[aria-checked="true"] { background: #6f9bff; border-color: #6f9bff; }
.st-key-demo_card[class*="arrow-"]::before, .st-key-demo_card[class*="arrow-"]::after { content: ""; position: absolute; width: 0; height: 0; border: solid transparent; }
.st-key-demo_card.arrow-up::before { top: -15px; left: var(--ao, 50%); transform: translateX(-50%); border-width: 0 13px 15px 13px; border-bottom-color: #8fa8d4; }
.st-key-demo_card.arrow-up::after { top: -11px; left: var(--ao, 50%); transform: translateX(-50%); border-width: 0 11px 13px 11px; border-bottom-color: #1d3557; }
.st-key-demo_card.arrow-down::before { bottom: -15px; left: var(--ao, 50%); transform: translateX(-50%); border-width: 15px 13px 0 13px; border-top-color: #8fa8d4; }
.st-key-demo_card.arrow-down::after { bottom: -11px; left: var(--ao, 50%); transform: translateX(-50%); border-width: 13px 11px 0 11px; border-top-color: #1d3557; }
.st-key-demo_card.arrow-left::before { left: -15px; top: var(--ao, 50%); transform: translateY(-50%); border-width: 13px 15px 13px 0; border-right-color: #8fa8d4; }
.st-key-demo_card.arrow-left::after { left: -11px; top: var(--ao, 50%); transform: translateY(-50%); border-width: 11px 13px 11px 0; border-right-color: #1d3557; }
.st-key-demo_card.arrow-right::before { right: -15px; top: var(--ao, 50%); transform: translateY(-50%); border-width: 13px 0 13px 15px; border-left-color: #8fa8d4; }
.st-key-demo_card.arrow-right::after { right: -11px; top: var(--ao, 50%); transform: translateY(-50%); border-width: 11px 0 11px 13px; border-left-color: #1d3557; }
body:has(.st-key-demo_card) .st-key-ask_bubble [data-testid="stPopoverButton"] { animation-duration: 1.6s; }
</style>"""


# ---------------- state ----------------
def on():
    return bool(st.session_state.get("demo_on"))


def _tick_number():
    return int(st.session_state.get("demo_tick", 0))


def _loop_and_step():
    n = len(STEPS)
    return _tick_number() // n, _tick_number() % n


def current_symbol():
    loop, _ = _loop_and_step()
    return COMPANIES[loop % len(COMPANIES)]


def current_step():
    return STEPS[_loop_and_step()[1]]


def _name(symbol):
    return companies.NAME_BY_SYMBOL.get(symbol, symbol)


def title_text():
    return current_step()["title"].replace("{name}", _name(current_symbol()))


def say_text():
    """What the card says under its title (and, together with the title, what the voice reads)."""
    return current_step()["say"].replace("{name}", _name(current_symbol()))


def spoken_text():
    return f"{title_text()}. {say_text()}"


def rate():
    """The playback speed the visitor chose (1 is normal, 2 is twice as fast)."""
    chosen = st.session_state.get("demo_speed") or "1×"
    try:
        return float(str(chosen).replace("×", ""))
    except ValueError:
        return 1.0


def seconds_for(text):
    """How long a step stays on screen: long enough to read (and to hear) its caption, shorter when the visitor has sped it up."""
    test_speed = float(os.environ.get("DEMO_SPEED", "1") or 1)               # 1 normally; a smaller number plays faster (for testing)
    return max(7.0, len(text) / 13.0 + 3.5) * test_speed / rate()


def _fresh_portfolio():
    pf = Portfolio(name="Demo")
    pf.tour_seen = True                  # no first-visit prompt on the pretend account
    return pf


def start():
    """Callback of the Demo button: remember what the visitor had, and switch to a throwaway pretend account."""
    if on():
        return
    st.session_state["tour_step"] = None                                           # a running tour and the demo do not mix
    st.session_state["demo_saved"] = {k: st.session_state.get(k, MISSING) for k in CHART_KEYS}
    st.session_state["demo_real_pf"] = st.session_state.get("portfolio")
    st.session_state["portfolio"] = _fresh_portfolio()
    st.session_state["demo_real_chat"] = copy.deepcopy(st.session_state.get("chat", []))          # the demo asks the helper a question; the visitor's own chat comes back after
    st.session_state["chat"] = []
    st.session_state["demo_tick"] = int(os.environ.get("DEMO_START_STEP", "0") or 0)           # 0 normally; only for testing a later step
    st.session_state["demo_applied"] = None
    st.session_state["demo_on"] = True
    st.session_state["demo_voice_cancel"] = False


def stop():
    """Callback of the Stop button (and of the first touch): put everything back exactly as the visitor had it."""
    if not on():
        return
    for key, value in (st.session_state.get("demo_saved") or {}).items():
        if value == MISSING:
            st.session_state.pop(key, None)
        else:
            st.session_state[key] = value
    real = st.session_state.pop("demo_real_pf", None)
    if real is not None:
        st.session_state["portfolio"] = real
    st.session_state["chat"] = st.session_state.pop("demo_real_chat", [])
    for key in ("demo_on", "demo_saved", "demo_tick", "demo_applied", "demo_bought", "demo_stamp_tick", "demo_stamp_time"):
        st.session_state.pop(key, None)
    st.session_state.pop("flash", None)
    st.session_state["demo_voice_cancel"] = True                                     # the page quietens the voice once


def advance():
    st.session_state["demo_tick"] = _tick_number() + 1


# ---------------- hooks used by the dashboard ----------------
def apply():
    """Call first thing in each run: when a new step has begun, set the company and the chart controls it needs."""
    if not on():
        return
    tick = _tick_number()
    if st.session_state.get("demo_applied") == tick:
        return
    loop, index = _loop_and_step()
    if index == 0:
        st.session_state["portfolio"] = _fresh_portfolio()                           # every trip round starts with a clean pretend account
        st.session_state["chat"] = []                                                # and a fresh chat
    symbol = current_symbol()
    for key, value in STEPS[index]["set"].items():
        st.session_state[key] = symbol if value == "{symbol}" else value
    st.session_state["demo_applied"] = tick


def after_price(symbol, price):
    """Call once the company's price is known: this is where the practice buy happens (once per step)."""
    if not on() or not current_step().get("buy") or st.session_state.get("demo_bought") == _tick_number():
        return
    st.session_state["demo_bought"] = _tick_number()
    from core import trading_ui as tu
    pf = tu._get_portfolio()
    quantity = max(1, int(PRACTICE_BUY // price)) if price else 1
    try:
        pf.buy(symbol, quantity, float(price))
        st.session_state["flash"] = ("ok", f"Practice buy: {quantity} shares of {_name(symbol)} at {format_inr(price)}.")
    except Exception:
        pass


def full_view_name():
    """The strategy whose Full view should be open right now, or None."""
    return current_step().get("full_view") if on() else None


# ---------------- drawing ----------------
# Picks the voice: a female American or British English one if the device has it (Samantha, Serena, Zira, Hazel, Google UK English
# Female and so on), never a male voice, an Indian-English one or any other language; the best-sounding (enhanced, premium or natural)
# version first. Written as plain text so the same function can be tested on its own.
PICK_VOICE_JS = """
function pickVoice(voices) {
  // never: novelty voices (a Mac has Bad News, Bubbles, Zarvox, Whisper and others), male voices, Indian-English and other languages
  var NOVELTY = /albert|bad news|bahh|bells|boing|bubbles|cellos|good news|jester|organ|superstar|trinoids|whisper|wobble|zarvox|grandma|grandpa|kathy|fred|junior|ralph|bruce|vicki|agnes/i;
  var MALE = /\\bmale\\b|daniel|alex\\b|tom\\b|oliver|david|mark\\b|george|ryan|guy\\b|james|arthur|gordon|rishi|thomas|matthew|brian|eric|christopher|roger|steffan|aaron|lee\\b|evan|liam|noah|william|eddy|reed|rocko|aaron|nathan|jorge|diego/i;
  // best first: clear, natural female English voices
  var LIKED = [/samantha/i, /serena/i, /google uk english female/i, /microsoft.*(aria|jenny|sonia|libby|zira|hazel|susan)/i, /\\b(ava|allison|susan|zoe|victoria|kate|stephanie|nicole|joanna|salli|amy|emma|olivia|ivy|kendra|kimberly)\\b/i,
               /flo\\b|shelley|sandy/i, /google us english/i, /karen|moira|tessa|fiona/i];
  var best = null, bestScore = -1;
  (voices || []).forEach(function (v) {
    var lang = (v.lang || '').replace('_', '-').toLowerCase(), name = v.name || '';
    if (lang.indexOf('en') !== 0 || lang === 'en-in') { return; }
    if (NOVELTY.test(name) || (MALE.test(name) && !/female/i.test(name))) { return; }
    var score = 1;
    if (lang === 'en-us' || lang === 'en-gb') { score += 6; }
    for (var i = 0; i < LIKED.length; i++) { if (LIKED[i].test(name)) { score += 40 - 4 * i; break; } }
    if (/female/i.test(name)) { score += 10; }
    if (/enhanced|premium|natural|neural/i.test(name)) { score += 20; } else if (/online/i.test(name)) { score += 3; }       // a better-sounding version beats the standard one
    if (score > bestScore) { best = v; bestScore = score; }
  });
  return best;
}
"""


def _voice_script(text, speak, target=None, side="bottom", speed=1.0, act=None, question=""):
    """The script of one step. It lives in this step's own small frame and does everything from there (no code is planted in the main
    page, which some sites forbid): it rings just the thing the step talks about and dims the rest, puts the caption card beside it with an
    arrow, speaks the caption, carries out the step's action (opening the chat helper, typing a question into it), and watches for a real
    touch, click or key press, which stops the demo. Streamlit swaps in a new frame at every step, and the new one first removes the old
    one's listeners, so only one set is ever active."""
    template = """<script>
__PICK__
(function () {
  var P = window.parent, D = P.document;
  try {
    var spec = __SPEC__, side = __SIDE__, text = __TEXT__, speak = __SPEAK__, speed = __SPEED__, action = __ACT__, question = __QUESTION__;
    var timer = null, sayTimer = null, actTimers = [], handlers = [], scrolled = false;
    function hush() { try { P.speechSynthesis.cancel(); } catch (e) {} }
    (P.__demoHandlers || []).forEach(function (h) { try { h[0].removeEventListener(h[1], h[2], h[3]); } catch (e) {} });
    P.__demoHandlers = handlers;
    function on(target, ev, fn, capture) { target.addEventListener(ev, fn, capture); handlers.push([target, ev, fn, capture]); }
    function later(fn, ms) { actTimers.push(setTimeout(fn, ms)); }
    function clearAll() {
      var hole = D.getElementById('demo-hole');
      if (hole) { hole.remove(); }
      clearInterval(timer); clearTimeout(sayTimer); actTimers.forEach(clearTimeout);
      hush();
    }
    if (!P.__demoOn) { P.__demoOn = true; P.__demoSince = Date.now(); }

    // a real touch, click or key press on the page stops the demo (but not one on the demo's own card, where the speed and the voice are
    // changed); the voice also stops when the tab is closed, left or hidden
    ['mousedown', 'keydown', 'touchstart', 'wheel'].forEach(function (ev) {
      on(D, ev, function (e) {
        if (!P.__demoOn || Date.now() - P.__demoSince < 1500 || (e && e.isTrusted === false)) { return; }
        if (e && e.target && e.target.closest && e.target.closest('.st-key-demo_card')) { return; }
        var btn = D.querySelector('.st-key-demo_stop button');
        if (btn) { P.__demoOn = false; clearAll(); btn.click(); }
      }, true);
    });
    ['pagehide', 'beforeunload', 'unload'].forEach(function (ev) { on(P, ev, hush, false); });
    on(D, 'visibilitychange', function () { if (D.hidden) { hush(); } }, false);

    // the exact thing this step talks about: a key, or a CSS selector plus the text it must contain; if that is not found, its bigger box
    function find() {
      if (!spec) { return null; }
      var list = spec.key ? D.querySelectorAll('.st-key-' + spec.key) : D.querySelectorAll(spec.sel), re = spec.text ? new RegExp(spec.text, 'i') : null;
      for (var i = 0; i < list.length; i++) {
        if (!re || re.test((list[i].textContent || '').trim())) { return list[i]; }
      }
      return spec.fallback ? D.querySelector('.st-key-' + spec.fallback) : null;
    }
    var narrow = false, roomScrolled = false;
    function scroller(el) {                                                     // the nearest part of the page that scrolls
      for (var e = el.parentElement; e; e = e.parentElement) {
        var o = P.getComputedStyle(e).overflowY;
        if ((o === 'auto' || o === 'scroll') && e.scrollHeight > e.clientHeight + 4) { return e; }
      }
      return D.scrollingElement;
    }
    // where a card of size w x h can go so that it sits completely outside the ring R (a gap away from it) and inside the screen
    function spot(side, R, w, h, vw, vh) {
      var gap = 22, m = 10, cx = (Math.max(R.left, 0) + Math.min(R.right, vw)) / 2, cy = (Math.max(R.top, 0) + Math.min(R.bottom, vh)) / 2, x, y, fits;
      function clamp(v, lo, hi) { return Math.min(Math.max(v, lo), Math.max(lo, hi)); }
      if (side === 'below') { x = clamp(cx - w / 2, m, vw - w - m); y = R.bottom + gap; fits = y + h <= vh - m; }
      else if (side === 'above') { x = clamp(cx - w / 2, m, vw - w - m); y = R.top - gap - h; fits = y >= m; }
      else if (side === 'right') { x = R.right + gap; y = clamp(cy - h / 2, m, vh - h - m); fits = x + w <= vw - m; }
      else { x = R.left - gap - w; y = clamp(cy - h / 2, m, vh - h - m); fits = x >= m; }
      return {side: side, x: x, y: y, fits: fits, cx: cx, cy: cy};
    }
    function place() {
      var card = D.querySelector('.st-key-demo_card'), hole = D.getElementById('demo-hole'), t = find();
      if (!card) { return; }
      ['arrow-up', 'arrow-down', 'arrow-left', 'arrow-right'].forEach(function (c) { card.classList.remove(c); });
      if (!t || side === 'bottom') {
        if (hole) { hole.remove(); }
        card.classList.remove('callout'); card.style.width = '';
        card.style.left = '50%%'; card.style.top = 'auto'; card.style.bottom = '1.1rem'; card.style.transform = 'translateX(-50%%)';
        return;
      }
      var vw = P.innerWidth, vh = P.innerHeight, r0 = t.getBoundingClientRect(), pad = 6;
      card.classList.add('callout');
      card.style.width = narrow ? '350px' : '';
      var w = card.offsetWidth, h = card.offsetHeight;
      // the ring: the whole thing if the card can sit beside it, otherwise the most telling part of it (for something very big)
      var rects = [{left: r0.left - pad, top: r0.top - pad, right: r0.right + pad, bottom: r0.bottom + pad}];
      (spec.parts || []).forEach(function (q) {
        rects.push({left: r0.left + q.x * r0.width - pad, top: r0.top + q.y * r0.height - pad, right: r0.left + (q.x + q.w) * r0.width + pad, bottom: r0.top + (q.y + q.h) * r0.height + pad});
      });
      if (!scrolled) {                                                          // bring the smallest ring into view once
        scrolled = true;
        var Rs = rects[rects.length - 1];
        if (Rs.top < 60 || Rs.bottom > vh - 60) {
          var mid = (Rs.top + Rs.bottom) / 2;
          try { scroller(t).scrollBy({top: (Rs.bottom - Rs.top) > vh - 180 ? Rs.top - 90 : mid - vh / 2, behavior: D.hidden ? 'auto' : 'smooth'}); } catch (e) {}
        }
      }
      var order = [side === 'inside_bottom' ? 'below' : side].concat(['below', 'above', 'right', 'left']), seen = {}, choice = null, R = null;
      order = order.filter(function (s2) { if (seen[s2]) { return false; } seen[s2] = 1; return true; });
      for (var ri = 0; ri < rects.length && !choice; ri++) {
        for (var oi = 0; oi < order.length; oi++) {
          var c = spot(order[oi], rects[ri], w, h, vw, vh);
          if (c.fits) { choice = c; R = rects[ri]; break; }
        }
      }
      if (!choice) {
        // no room beside it: first try scrolling the page a little to make room above or below it, then a narrower card
        if (!roomScrolled && rects[0].right > rects[0].left) {
          roomScrolled = true;
          var sc = scroller(t), room = h + 22 + 14, R0 = rects[rects.length - 1], delta = 0;
          if (side === 'above' || side === 'left') { delta = R0.top - room; } else { delta = R0.bottom - (vh - room); }
          try { sc.scrollBy({top: delta, behavior: D.hidden ? 'auto' : 'smooth'}); } catch (e) {}
        } else if (!narrow) { narrow = true; }
        R = rects[rects.length - 1];
        choice = spot(order[0], R, w, h, vw, vh);              // last resort for this tick: the preferred side, even if tight
      }
      if (!hole) {
        hole = D.createElement('div'); hole.id = 'demo-hole';
        hole.style.cssText = 'position:fixed;pointer-events:none;z-index:2147482000;box-shadow:0 0 0 3px #8fa8d4, 0 0 0 9999px rgba(0,0,0,0.68);';
        D.body.appendChild(hole);
      }
      hole.style.left = R.left + 'px'; hole.style.top = R.top + 'px'; hole.style.width = (R.right - R.left) + 'px'; hole.style.height = (R.bottom - R.top) + 'px';
      var br = P.getComputedStyle(t).borderRadius; hole.style.borderRadius = (br && br !== '0px') ? br : '10px';
      card.style.left = choice.x + 'px'; card.style.top = choice.y + 'px'; card.style.bottom = 'auto'; card.style.transform = 'none';
      var arrow = {below: 'up', above: 'down', right: 'left', left: 'right'}[choice.side];
      card.classList.add('arrow-' + arrow);
      var along = (arrow === 'up' || arrow === 'down') ? Math.min(Math.max(28, choice.cx - choice.x), w - 28) : Math.min(Math.max(28, choice.cy - choice.y), h - 28);
      card.style.setProperty('--ao', along + 'px');
    }
    timer = setInterval(place, 120);                                            // follows the page for as long as the step lasts
    place();

    // what the step does on the screen: open the chat helper, or open it and type a question into it and press Ask
    function bubble() { return D.querySelector('.st-key-ask_bubble [data-testid="stPopoverButton"]'); }
    function isOpen() { var b = bubble(); return !!b && b.getAttribute('aria-expanded') === 'true'; }
    function openChat() { var b = bubble(); if (b && !isOpen()) { b.click(); } }
    function closeChat() { var b = bubble(); if (b && isOpen()) { b.click(); } }
    function typeQuestion() {
      var input = D.querySelector('[data-testid="stPopoverBody"] input[type="text"]');
      if (!input) { later(typeQuestion, 400); return; }
      var setter = Object.getOwnPropertyDescriptor(P.HTMLInputElement.prototype, 'value').set, i = 0;
      input.focus();
      (function next() {
        if (!P.__demoOn) { return; }
        i++;
        setter.call(input, question.slice(0, i));
        input.dispatchEvent(new P.Event('input', {bubbles: true}));
        if (i < question.length) { later(next, 70 / speed); return; }
        later(function () {
          var ask = Array.prototype.filter.call(D.querySelectorAll('[data-testid="stPopoverBody"] button'), function (b) { return /^Ask$/.test((b.textContent || '').trim()); })[0];
          if (ask) { ask.click(); }
        }, 600 / speed);
      })();
    }
    if (action === 'close_chat') { later(closeChat, 300); }
    else if (action === 'open_chat') { later(openChat, 300); }
    else if (action === 'ask') { later(function () { openChat(); later(typeQuestion, 900); }, 1500 / speed); }

    // the voice: a browser loads its list of voices a little late (sometimes a few seconds), and speaking before then would use the
    // browser's default voice, so wait until the list is there
    function say() {
      if (!P.__demoOn || D.hidden) { return; }                                  // stopped, or the tab is in the background: stay quiet
      var v = pickVoice(P.speechSynthesis.getVoices());
      P.__demoVoiceUsed = v ? v.name : '(default)';
      P.speechSynthesis.cancel();
      // one sentence at a time: some browsers cut a long utterance off after about fifteen seconds, and short ones also sound more natural
      (text.match(/[^.!?]+[.!?]*/g) || [text]).forEach(function (part) {
        part = part.trim();
        if (!part) { return; }
        var u = new P.SpeechSynthesisUtterance(part);
        if (v) { u.voice = v; u.lang = v.lang; } else { u.lang = 'en-GB'; }
        u.rate = Math.min(2, 0.97 * speed);
        u.pitch = 1.0;
        P.speechSynthesis.speak(u);
      });
    }
    function whenVoicesReady(tries) {
      if (P.speechSynthesis.getVoices().length || tries >= 40) { say(); } else { sayTimer = setTimeout(function () { whenVoicesReady(tries + 1); }, 150); }
    }
    if (speak && P.speechSynthesis) { P.speechSynthesis.getVoices(); whenVoicesReady(0); }
  } catch (e) {}
})();
</script>"""
    return (template.replace("__PICK__", PICK_VOICE_JS).replace("__SPEC__", json.dumps(target)).replace("__SIDE__", json.dumps(side))
            .replace("__TEXT__", json.dumps(text)).replace("__SPEAK__", "true" if speak else "false").replace("__SPEED__", json.dumps(float(speed)))
            .replace("__ACT__", json.dumps(act)).replace("__QUESTION__", json.dumps(question)).replace("%%", "%"))


_QUIET = """<script>
try {
  var P = window.parent, D = P.document;
  P.__demoOn = false;
  (P.__demoHandlers || []).forEach(function (h) { try { h[0].removeEventListener(h[1], h[2], h[3]); } catch (e) {} });
  P.__demoHandlers = [];
  var hole = D.getElementById('demo-hole'); if (hole) { hole.remove(); }
  P.speechSynthesis.cancel();
} catch (e) {}
</script>"""


def _tick(seen, seconds):
    """The timer. It moves on to the next step only once this step has really been on screen for its time, so an extra rerun for some
    other reason can never skip a step."""
    if st.session_state.get("demo_stamp_tick") != seen:
        st.session_state["demo_stamp_tick"] = seen
        st.session_state["demo_stamp_time"] = time.time()
        return
    if time.time() - st.session_state.get("demo_stamp_time", 0) < seconds - 0.5:
        return
    advance()
    st.rerun()


def render(dark=False):
    """Call last: the caption card, the spotlight, the timer and the voice (or, just after a stop, the hush)."""
    if not on():
        if st.session_state.pop("demo_voice_cancel", False):
            components.html(_QUIET, height=0)
        return
    tick = _tick_number()
    loop, index = _loop_and_step()
    step = current_step()
    text = spoken_text()
    st.markdown(CSS, unsafe_allow_html=True)
    with st.container(key="demo_card"):
        st.markdown(f'<div class="demo-badge">Demo · pretend account · step {index + 1} of {len(STEPS)}</div>'
                    f'<div class="demo-title">{title_text()}</div><div class="demo-say">{say_text()}</div>', unsafe_allow_html=True)
        stop_col, voice_col, speed_col = st.columns([1.15, 0.95, 2.6], vertical_alignment="center")
        stop_col.button("Stop demo", key="demo_stop", on_click=stop, width="stretch")
        voice_col.toggle("Voice", key="demo_voice", value=True)
        speed_col.segmented_control("Speed", SPEEDS, default="1×", key="demo_speed", label_visibility="collapsed", help="Playback speed, like a video's")
        st.markdown('<div class="demo-hint">Touch the screen at any time to take over.</div>', unsafe_allow_html=True)
    components.html(_voice_script(text, st.session_state.get("demo_voice", True), step["target"], step.get("side", "bottom"), rate(),
                                  step.get("act"), step.get("question", "")), height=0)
    if st.session_state.get("demo_stamp_tick") != tick:          # note when this step went on screen
        st.session_state["demo_stamp_tick"] = tick
        st.session_state["demo_stamp_time"] = time.time()
    seconds = seconds_for(text)
    st.fragment(run_every=seconds)(_tick)(tick, seconds)
