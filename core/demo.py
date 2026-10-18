"""A self-playing demo of the dashboard, for the people presenting it.

Pressing the Demo button starts a loop that drives the real screen by itself: it searches a company, switches the Day, Week and Month
candles, turns on the Fibonacci lines, shows four charts at once, lights up the indicators, the dial and the strategies, opens a
strategy's Full view, makes a practice buy, and points at the chat button, with a big plain-words caption (and, if switched on, a spoken
voice) for every step. Then it carries on with another company until somebody touches the screen, which stops it at once.

The setting DEMO_SPEED (an environment variable, 1 by default; 0.35 plays about three times faster) is only for testing.

Nothing the demo does touches a visitor's own portfolio: it works on a throwaway pretend account that is never saved, and the visitor's
own account, company and chart settings are put back exactly as they were when it stops.

How it fits in: terminal_ui.run() calls apply() before it draws anything (so the demo can set the company and the chart controls),
after_price() once the price is known (for the practice buy), full_view_name() when it draws the strategies table, and render() at the
end (the caption card, the spotlight, the timer that moves to the next step, and the voice).
"""
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
PRACTICE_BUY = 10000.0                                              # rupees of pretend money spent in the demo buy

NORMAL = {"mtf_layout": "1 chart", "mtf_tf": "Daily", "period_seg": "1 year", "show_fib": False}

STEPS = [
    {"say": "Welcome! This is a practice stock market. The prices are real, but the money is pretend, so nobody can lose anything.",
     "set": dict(NORMAL), "target": {"sel": ".tm-value"}, "side": "below"},
    {"say": "First we pick a company. You can type any company name in this box. Let us look at {name}.",
     "set": {"company": "{symbol}"}, "target": {"sel": ".st-key-tm_search [data-testid=\"stSelectbox\"]"}, "side": "below"},
    {"say": "This is its price chart. Each bar is one day. A green bar means the price went up that day, and a red bar means it went down.",
     "set": {"mtf_tf": "Daily"}, "target": {"sel": ".st-key-tm_chartarea [data-testid=\"stPlotlyChart\"]"}, "side": "inside_bottom"},
    {"say": "Now we zoom out. Each bar is one whole week. The ups and downs look smoother.",
     "set": {"mtf_tf": "Weekly"}, "target": {"sel": ".st-key-tm_chartbar button", "text": "^Week$"}, "side": "below"},
    {"say": "Zoom out again. Now each bar is one month. This is the big picture of where the price has been heading.",
     "set": {"mtf_tf": "Monthly"}, "target": {"sel": ".st-key-tm_chartbar button", "text": "^Month$"}, "side": "below"},
    {"say": "Back to days. We switched on the Fibonacci lines. They mark places where a price often pauses, like a ball resting on a staircase.",
     "set": {"mtf_tf": "Daily", "show_fib": True}, "target": {"sel": ".st-key-tm_chartbar [data-testid=\"stCheckbox\"]", "text": "Fibonacci"}, "side": "below"},
    {"say": "We can look at four charts at once, each in a different timeframe, so the big picture and the small details sit side by side.",
     "set": {"show_fib": False, "mtf_layout": "4 charts"}, "target": {"sel": ".st-key-tm_chartbar button", "text": "^4$"}, "side": "below"},
    {"say": "Back to one chart. These six gauges read the chart for us. Red leans down, green leans up, and the pointer shows where it stands.",
     "set": {"mtf_layout": "1 chart"}, "target": {"key": "tm_ind"}, "side": "left"},
    {"say": "This dial adds up the votes of five strategies from a professional exam. It says whether the reading leans up or down. It is a clue, not a promise.",
     "set": {}, "target": {"key": "tm_baro"}, "side": "right"},
    {"say": "Here are the five strategies and a machine-learning model, each with its vote. In our tests they were right about half the time, the same as a coin toss, and we say so honestly.",
     "set": {}, "target": {"key": "tm_strat"}, "side": "above"},
    {"say": "Let us open one. This is Dow Theory. It looks for higher highs and higher lows, like climbing a staircase.",
     "set": {}, "target": None, "full_view": "Dow Theory", "side": "bottom"},
    {"say": "Time to practise! We buy some shares of {name} with pretend money.",
     "set": {}, "target": {"sel": ".st-key-tm_trade button", "text": "^Buy$"}, "buy": True, "side": "above"},
    {"say": "Look! The list of what we hold, the money ring and the portfolio value have all updated. This is how you follow your practice.",
     "set": {}, "target": {"key": "tm_lists"}, "side": "right"},
    {"say": "The leaderboard ranks everyone by how much their money has grown, so even a small portfolio can win.",
     "set": {}, "target": {"key": "tm_board"}, "side": "right"},
    {"say": "If you meet a word you do not know, tap this round button and ask the helper. It explains in simple words.",
     "set": {}, "target": {"sel": ".st-key-ask_bubble [data-testid=\"stPopoverButton\"]"}, "side": "left"},
    {"say": "That is the demo. Touch the screen to try it yourself, or press Tour for a step by step walk through. We will keep playing until you do.",
     "set": {}, "target": {"sel": ".st-key-tour_btn_top button"}, "side": "below"},
]

CSS = """<style>
.st-key-demo_card { position: fixed; left: 50%; bottom: 1.1rem; transform: translateX(-50%); width: min(94vw, 780px); z-index: 2147483000;
  background: #1d3557; color: #ffffff; border: 2px solid #8fa8d4; border-radius: 18px; padding: 0.8rem 1.2rem 0.7rem 1.2rem;
  box-shadow: 0 10px 34px rgba(0,0,0,0.5); }
.st-key-demo_card * { color: #ffffff; }
.st-key-demo_card .demo-badge { font-size: .78rem; letter-spacing: .12em; text-transform: uppercase; font-weight: 800; color: #b9ccf6; margin-bottom: .25rem; }
.st-key-demo_card .demo-say { font-size: 1.5rem; font-weight: 600; line-height: 1.32; margin-bottom: .45rem; }
.st-key-demo_card .demo-hint { font-size: .85rem; opacity: .8; }
.st-key-demo_card [data-testid="stHorizontalBlock"] { align-items: center; gap: .6rem; }
.st-key-demo_card button { background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.5); }
.st-key-demo_card button:hover { background: rgba(255,255,255,0.22); }
.st-key-demo_card [data-testid="stToggle"] label p { font-size: .95rem; }
.st-key-demo_card [data-testid="stToggle"] label > div:not([data-testid="stWidgetLabel"]) { background: rgba(255,255,255,0.35) !important; }
.st-key-demo_card [data-testid="stToggle"] label:has(input:checked) > div:not([data-testid="stWidgetLabel"]) { background: #6f9bff !important; }
.st-key-demo_card [data-testid="stCaptionContainer"] { color: #ffffff; }
.st-key-demo_dots { margin-top: .1rem; }
.st-key-demo_card.callout { width: min(92vw, 440px); }
.st-key-demo_card.callout .demo-say { font-size: 1.28rem; }
.st-key-demo_card.callout .demo-hint { display: none; }
.st-key-demo_card.callout [data-testid="stColumn"]:nth-child(3) { display: none !important; }
.st-key-demo_card.callout [data-testid="stColumn"]:nth-child(-n+2) { flex: 1 1 45% !important; width: auto !important; min-width: 0 !important; }
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


def say_text():
    symbol = current_symbol()
    return current_step()["say"].replace("{name}", _name(symbol))


def seconds_for(text):
    """How long a step stays on screen: long enough to read (and to hear) its caption."""
    speed = float(os.environ.get("DEMO_SPEED", "1") or 1)                 # 1 normally; a smaller number plays faster (for testing)
    return max(6.0, len(text) / 12.0 + 2.5) * speed


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
    st.session_state["demo_tick"] = 0
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
PARENT_JS = """
(function () {
  window.__demoClear = function () {
    var hole = document.getElementById('demo-hole');
    if (hole) { hole.remove(); }
    clearInterval(window.__demoPlaceTimer);
  };
  if (!window.__demoWatch) {
    window.__demoWatch = true;
    ['mousedown', 'keydown', 'touchstart', 'wheel'].forEach(function (ev) {
      document.addEventListener(ev, function () {
        if (!window.__demoOn || Date.now() - window.__demoSince < 1500) { return; }
        var btn = document.querySelector('.st-key-demo_stop button');
        if (btn) { window.__demoOn = false; window.__demoClear(); try { window.speechSynthesis.cancel(); } catch (e) {} btn.click(); }
      }, true);
    });
  }
  if (!window.__demoPlace) {
    // Finds the exact thing a step talks about (a key, or a CSS selector plus the text it must contain), rings just that thing and dims
    // everything else, and puts the caption card beside it with an arrow pointing at it. It keeps checking for a few seconds and on
    // every scroll, so it follows the page while it scrolls into view.
    window.__demoPlace = function (spec, side) {
      function find() {
        if (!spec) { return null; }
        var list = spec.key ? document.querySelectorAll('.st-key-' + spec.key) : document.querySelectorAll(spec.sel), re = spec.text ? new RegExp(spec.text, 'i') : null;
        for (var i = 0; i < list.length; i++) {
          if (!re || re.test((list[i].textContent || '').trim())) { return list[i]; }
        }
        return null;
      }
      var scrolled = false;
      function place() {
        var card = document.querySelector('.st-key-demo_card'), hole = document.getElementById('demo-hole'), t = find();
        if (!card) { return; }
        ['arrow-up', 'arrow-down', 'arrow-left', 'arrow-right'].forEach(function (c) { card.classList.remove(c); });
        if (!t || side === 'bottom') {
          if (hole) { hole.remove(); }
          card.classList.remove('callout');
          card.style.left = '50%'; card.style.top = 'auto'; card.style.bottom = '1.1rem'; card.style.transform = 'translateX(-50%)';
          return;
        }
        var vw = window.innerWidth, vh = window.innerHeight, r0 = t.getBoundingClientRect();
        if (!scrolled) {                                                          // bring it into view once, gently
          scrolled = true;
          if (r0.top < 90 || r0.bottom > vh - 90) { try { t.scrollIntoView({block: 'center', behavior: 'smooth'}); } catch (e) {} }
        }
        var pad = 6, r = {left: r0.left - pad, top: r0.top - pad, right: r0.right + pad, bottom: r0.bottom + pad};
        if (!hole) {
          hole = document.createElement('div'); hole.id = 'demo-hole';
          hole.style.cssText = 'position:fixed;pointer-events:none;z-index:2147482000;box-shadow:0 0 0 3px #8fa8d4, 0 0 0 9999px rgba(0,0,0,0.68);';
          document.body.appendChild(hole);
        }
        hole.style.left = r.left + 'px'; hole.style.top = r.top + 'px'; hole.style.width = (r.right - r.left) + 'px'; hole.style.height = (r.bottom - r.top) + 'px';
        var br = window.getComputedStyle(t).borderRadius; hole.style.borderRadius = (br && br !== '0px') ? br : '10px';
        card.classList.add('callout');
        var w = card.offsetWidth, h = card.offsetHeight, gap = 20, margin = 10;
        var rt = Math.max(r.top, 0), rb = Math.min(r.bottom, vh), rl = Math.max(r.left, 0), rr = Math.min(r.right, vw);
        var cx = (rl + rr) / 2, cy = (rt + rb) / 2, x, y, arrow = null;
        if (side === 'below') { x = cx - w / 2; y = rb + gap; arrow = 'up'; }
        else if (side === 'above') { x = cx - w / 2; y = rt - h - gap; arrow = 'down'; }
        else if (side === 'left') { x = rl - w - gap; y = cy - h / 2; arrow = 'right'; }
        else if (side === 'right') { x = rr + gap; y = cy - h / 2; arrow = 'left'; }
        else { x = cx - w / 2; y = rb - h - gap; }
        x = Math.min(Math.max(margin, x), vw - w - margin); y = Math.min(Math.max(margin, y), vh - h - margin);
        card.style.left = x + 'px'; card.style.top = y + 'px'; card.style.bottom = 'auto'; card.style.transform = 'none';
        if (arrow) {
          card.classList.add('arrow-' + arrow);
          var along = (arrow === 'up' || arrow === 'down') ? Math.min(Math.max(28, cx - x), w - 28) : Math.min(Math.max(28, cy - y), h - 28);
          card.style.setProperty('--ao', along + 'px');
        }
      }
      var n = 0;
      clearInterval(window.__demoPlaceTimer);
      if (window.__demoPlaceOnScroll) { window.removeEventListener('scroll', window.__demoPlaceOnScroll, true); }
      window.__demoPlaceOnScroll = place;
      window.addEventListener('scroll', place, true);
      window.addEventListener('resize', place);
      window.__demoPlaceTimer = setInterval(function () { place(); if (++n > 60) { clearInterval(window.__demoPlaceTimer); } }, 80);
      place();
    };
  }
})();
"""

PICK_VOICE_JS = """
function pickVoice(voices) {
  var FEMALE = /female|samantha|serena|karen|zira|hazel|susan|moira|victoria|kate|allison|ava|jenny|aria|libby|sonia|emma|amy|joanna|salli|kendra|kimberly|ivy|nicole|olivia|stephanie|tessa|fiona|ellen|catherine|zoe|nova|jane|michelle|natasha/i;
  var MALE = /\\bmale\\b|daniel|alex\\b|fred|tom\\b|oliver|david|mark\\b|george|ryan|guy\\b|james|arthur|gordon|rishi|thomas|matthew|brian|eric|christopher|roger|steffan|aaron|junior|bruce|ralph|albert|lee\\b|evan|liam|noah|william/i;
  var best = null, bestScore = -1;
  (voices || []).forEach(function (v) {
    var lang = (v.lang || '').replace('_', '-').toLowerCase(), name = v.name || '';
    if (lang.indexOf('en') !== 0 || lang === 'en-in') { return; }
    if (MALE.test(name) && !/female/i.test(name)) { return; }
    var score = 1;
    if (lang === 'en-us' || lang === 'en-gb') { score += 6; }
    if (FEMALE.test(name)) { score += 10; }
    if (/enhanced|premium|natural|neural|online/i.test(name)) { score += 3; }
    if (v.localService === false && /google/i.test(name)) { score += 1; }
    if (score > bestScore) { best = v; bestScore = score; }
  });
  return best;
}
"""


def _voice_script(text, speak, target=None, side="bottom"):
    """Starts the step in the main page: puts the caption card beside the part being described, speaks the caption (when the voice is on),
    and keeps watching for a real touch, click or key press, which stops the demo."""
    return """<script>
%s
(function () {
  var P = window.parent;
  try {
    if (!P.__demoWatch || !P.__demoPlace) {
      // the helpers are planted in the main page (not in this small frame, which Streamlit replaces at every step; a listener or a
      // function that belongs to a removed frame stops working)
      var s = P.document.createElement('script');
      s.textContent = %s;
      P.document.head.appendChild(s);
    }
    if (!P.__demoOn) { P.__demoOn = true; P.__demoSince = Date.now(); }
    if (P.__demoPlace) { P.__demoPlace(%s, %s); }
    var text = %s;
    function say() {
      var u = new P.SpeechSynthesisUtterance(text), v = pickVoice(P.speechSynthesis.getVoices());
      if (v) { u.voice = v; u.lang = v.lang; } else { u.lang = 'en-GB'; }
      u.rate = 0.97;
      u.pitch = 1.0;
      P.speechSynthesis.cancel();
      P.speechSynthesis.speak(u);
    }
    if (%s && P.speechSynthesis) {
      if (P.speechSynthesis.getVoices().length) { say(); } else { setTimeout(say, 700); }      // some browsers load their voices a moment late
    }
  } catch (e) {}
})();
</script>""" % (PICK_VOICE_JS, json.dumps(PARENT_JS), json.dumps(target), json.dumps(side), json.dumps(text), "true" if speak else "false")


_QUIET = """<script>
try { var P = window.parent; P.__demoOn = false; if (P.__demoClear) { P.__demoClear(); } P.speechSynthesis.cancel(); } catch (e) {}
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
    text = say_text()
    st.markdown(CSS, unsafe_allow_html=True)
    with st.container(key="demo_card"):
        st.markdown(f'<div class="demo-badge">Demo · pretend account · step {index + 1} of {len(STEPS)}</div>'
                    f'<div class="demo-say">{text}</div>', unsafe_allow_html=True)
        stop_col, voice_col, hint_col = st.columns([1.2, 1.1, 3.2], vertical_alignment="center")
        stop_col.button("Stop demo", key="demo_stop", on_click=stop, width="stretch")
        voice_col.toggle("Voice", key="demo_voice", value=True)
        hint_col.markdown('<div class="demo-hint">Touch the screen at any time to take over.</div>', unsafe_allow_html=True)
    components.html(_voice_script(text, st.session_state.get("demo_voice", True), step["target"], step.get("side", "bottom")), height=0)
    if st.session_state.get("demo_stamp_tick") != tick:          # note when this step went on screen
        st.session_state["demo_stamp_tick"] = tick
        st.session_state["demo_stamp_time"] = time.time()
    seconds = seconds_for(text)
    st.fragment(run_every=seconds)(_tick)(tick, seconds)
