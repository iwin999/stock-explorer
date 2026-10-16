"""HTML pieces for the Daily check: a call badge, vote dots, indicator cards, the range bar and the track-record strip.
Pure functions that return HTML text (no Streamlit), so they can be tested."""
import html

from core.ui import scale_html

UP_C, DOWN_C, FLAT_C = "#26a69a", "#ef5350", "#868993"
GLYPH = {"Up": "▲", "Down": "▼", "Sideways": "▬"}
COLOUR = {"Up": UP_C, "Down": DOWN_C, "Sideways": FLAT_C}
VOTE_NAME = {1: "Up", -1: "Down", 0: "Sideways"}

CSS = """<style>
.dc-hero { display:flex; align-items:center; gap:1.1rem; padding:1rem 1.2rem; border-radius:16px; border:1px solid rgba(128,128,128,.35); margin:.4rem 0 .8rem 0; }
.dc-badge { width:4.6rem; height:4.6rem; border-radius:50%; display:flex; align-items:center; justify-content:center; color:#fff; font-size:2.1rem; flex:0 0 auto; }
.dc-call { font-size:1.9rem; font-weight:800; line-height:1.1; }
.dc-sub { opacity:.75; font-size:1rem; margin-top:.15rem; }
.dc-dots { display:flex; gap:.35rem; margin-top:.45rem; }
.dc-dot { width:1.15rem; height:1.15rem; border-radius:50%; display:inline-block; }
.dc-versus { display:grid; grid-template-columns:1fr auto 1fr; gap:.7rem; align-items:center; margin:.3rem 0 .6rem 0; }
.dc-tile { text-align:center; border-radius:14px; padding:.7rem .4rem; color:#fff; }
.dc-tile .t { font-size:.85rem; opacity:.9; } .dc-tile .v { font-size:1.6rem; font-weight:800; }
.dc-result { width:3.2rem; height:3.2rem; border-radius:50%; display:flex; align-items:center; justify-content:center; color:#fff; font-size:1.7rem; font-weight:800; }
.dc-range { position:relative; height:2.6rem; margin:1.4rem .3rem 1.8rem .3rem; }
.dc-track { position:absolute; top:1.05rem; left:0; right:0; height:.5rem; border-radius:99px; background:rgba(128,128,128,.28); }
.dc-band { position:absolute; top:.85rem; height:.9rem; border-radius:99px; background:rgba(41,98,255,.55); }
.dc-tick { position:absolute; top:.55rem; width:3px; height:1.5rem; background:#868993; }
.dc-pin { position:absolute; top:.35rem; width:1.5rem; height:1.5rem; margin-left:-.75rem; border-radius:50%; border:3px solid #fff; box-shadow:0 0 0 2px #333; }
.dc-lbl { position:absolute; top:-1.15rem; font-size:.78rem; transform:translateX(-50%); white-space:nowrap; opacity:.85; }
.dc-lbl.b { top:2.15rem; }
.dc-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(215px,1fr)); gap:.7rem; margin:.4rem 0 1rem 0; }
.dc-card { border:1px solid rgba(128,128,128,.35); border-radius:14px; padding:.7rem .85rem .2rem .85rem; }
.dc-card.ctx { opacity:.8; }
.dc-name { font-weight:700; display:flex; justify-content:space-between; align-items:center; gap:.4rem; }
.dc-chip { color:#fff; font-size:.78rem; font-weight:700; padding:.1rem .6rem; border-radius:99px; white-space:nowrap; }
.dc-why { font-size:.88rem; opacity:.75; margin:.15rem 0 .2rem 0; }
.dc-strip { display:flex; flex-wrap:wrap; gap:3px; margin:.4rem 0 .8rem 0; }
.dc-sq { width:.95rem; height:.95rem; border-radius:3px; display:inline-block; }
.dc-bars .row { display:flex; align-items:center; gap:.6rem; margin:.3rem 0; }
.dc-bars .lab { width:8.5rem; font-size:.92rem; } .dc-bars .bar { flex:1; height:1.1rem; border-radius:99px; background:rgba(128,128,128,.25); position:relative; overflow:hidden; }
.dc-bars .fill { height:100%; border-radius:99px; } .dc-bars .num { width:3.2rem; font-weight:700; text-align:right; }
.dc-bars .half { position:absolute; left:50%; top:0; bottom:0; width:2px; background:rgba(0,0,0,.45); }
.lh-row { display:flex; flex-wrap:wrap; gap:.45rem .5rem; }
.lh { position:relative; display:inline-flex; align-items:center; gap:.35rem; border:1px solid var(--tm-line,#dfe3ea); border-radius:99px; padding:.2rem .65rem; font-size:.82rem; cursor:help; color:var(--tm-ink,#1d3557); }
.lh b { display:inline-flex; width:1.05rem; height:1.05rem; border-radius:50%; background:rgba(128,128,128,.22); align-items:center; justify-content:center; font-size:.7rem; }
.lh .tip { visibility:hidden; opacity:0; transition:opacity .15s; position:absolute; bottom:calc(100% + .5rem); left:0; z-index:50; width:21rem; max-width:80vw; background:#1e222d; color:#e6e9ef; border-radius:10px; padding:.7rem .85rem; font-size:.82rem; line-height:1.45; box-shadow:0 6px 24px rgba(0,0,0,.35); text-align:left; }
.lh .tip b { display:inline; width:auto; height:auto; background:none; font-size:.85rem; color:#fff; }
.lh:hover .tip { visibility:visible; opacity:1; }
.lh:nth-child(n+8) .tip { left:auto; right:0; }
.pp { background:var(--tm-panel,#fff); border:1px solid var(--tm-line,#dfe3ea); border-radius:14px; padding:1.4rem 1.8rem 1.2rem 1.8rem; box-shadow:0 1px 3px rgba(16,24,40,.07); }
.pp .up { color:var(--pp-up,#158a7e); } .pp .down { color:var(--pp-down,#d6453d); } .pp .flat { color:var(--pp-flat,#6b7785); }
.pp-head { display:flex; justify-content:space-between; align-items:baseline; gap:1rem; }
.pp-title { font-size:1.35rem; font-weight:700; } .pp-sub { font-size:.92rem; color:var(--tm-muted,#6b7785); margin-top:.2rem; }
.pp-live { display:flex; align-items:center; gap:.45rem; font-size:.92rem; color:var(--tm-muted,#6b7785); white-space:nowrap; }
.pp-live i { width:.6rem; height:.6rem; border-radius:50%; background:#9aa3b2; display:inline-block; } .pp-live.on i { background:#26a69a; }
.pp-say { font-size:1.2rem; line-height:1.55; margin:1.1rem 0 1.2rem 0; padding:.95rem 1.2rem; border-left:5px solid #9aa3b2; background:rgba(128,128,128,.07); border-radius:0 10px 10px 0; }
.pp-stats { display:grid; grid-template-columns:repeat(3,1fr); gap:1rem; }
.pp-stat { border:1px solid var(--tm-line,#dfe3ea); border-radius:12px; padding:1rem 1.2rem; min-width:0; }
.pp-k { font-size:.9rem; color:var(--tm-muted,#6b7785); margin-bottom:.35rem; }
.pp-v { font-size:1.9rem; font-weight:700; line-height:1.1; } .pp-d { font-size:.98rem; color:var(--tm-muted,#6b7785); margin-top:.35rem; line-height:1.4; }
.pp-pbar { position:relative; height:.55rem; border-radius:99px; background:rgba(128,128,128,.22); margin:.75rem 0 .1rem 0; }
.pp-pbar i { position:absolute; left:0; top:0; bottom:0; border-radius:99px; background:#2962ff; opacity:.8; } .pp-pbar u { position:absolute; left:50%; top:-.25rem; bottom:-.25rem; width:2px; background:var(--tm-ink,#1d3557); opacity:.6; }
.pp-rangebox { border:1px solid var(--tm-line,#dfe3ea); border-radius:12px; padding:1rem 1.2rem .3rem 1.2rem; margin-top:1rem; }
.pp-rangebox .dc-range { margin:1.3rem .4rem 1.6rem .4rem; }
.pp-sec { font-size:1.05rem; font-weight:700; margin:1.5rem 0 .6rem 0; } .pp-sec small { font-weight:400; color:var(--tm-muted,#6b7785); font-size:.9rem; margin-left:.4rem; }
.pp-table { width:100%; border-collapse:collapse; } .pp-table th { text-align:left; font-size:.85rem; font-weight:600; color:var(--tm-muted,#6b7785); padding:.4rem .7rem; border-bottom:1px solid var(--tm-line,#dfe3ea); }
.pp-table td { padding:.75rem .7rem; border-bottom:1px solid var(--tm-line,#dfe3ea); font-size:1rem; vertical-align:middle; } .pp-table tr:last-child td { border-bottom:0; }
.pp-sname { font-weight:700; } .pp-vote { font-weight:700; white-space:nowrap; } .pp-test { color:var(--tm-muted,#6b7785); font-size:.92rem; }
.pp-foot { margin-top:1rem; padding-top:.8rem; border-top:1px solid var(--tm-line,#dfe3ea); font-size:.8rem; line-height:1.5; color:var(--tm-muted,#6b7785); }
@media (max-width:1100px){ .pp-stats { grid-template-columns:1fr; } .pp-table th:last-child, .pp-table td:last-child { display:none; } }
@media (max-width:640px){ .dc-hero{gap:.7rem;padding:.8rem} .dc-badge{width:3.6rem;height:3.6rem;font-size:1.6rem} .dc-call{font-size:1.5rem} .dc-bars .lab{width:6rem} }
</style>"""


def e(text):
    return html.escape(str(text))


def hero(prediction, score, voters, target_word="today"):
    """The big call badge with one dot per voting indicator (green = Up, red = Down, grey = Neutral)."""
    colour = COLOUR[prediction]
    ups = sum(1 for v in voters if v["vote"] > 0)
    downs = sum(1 for v in voters if v["vote"] < 0)
    dots = "".join(f'<span class="dc-dot" title="{e(v["name"])}: {VOTE_NAME[v["vote"]]}" '
                   f'style="background:{COLOUR[VOTE_NAME[v["vote"]]]}"></span>' for v in voters)
    word = {"Up": "Leaning UP", "Down": "Leaning DOWN", "Sideways": "Leaning SIDEWAYS"}[prediction]
    return (f'<div class="dc-hero"><div class="dc-badge" style="background:{colour}">{GLYPH[prediction]}</div><div>'
            f'<div class="dc-call" style="color:{colour}">{word} {e(target_word)}</div>'
            f'<div class="dc-sub">{ups} up &middot; {downs} down &middot; {len(voters) - ups - downs} neutral</div>'
            f'<div class="dc-dots">{dots}</div></div></div>')


def versus(prediction, actual_direction, matched):
    """Called vs Actual side by side, with a tick or a cross between them."""
    mark_c, mark = (UP_C, "&#10003;") if matched else (DOWN_C, "&#10007;")
    return (f'<div class="dc-versus"><div class="dc-tile" style="background:{COLOUR[prediction]}"><div class="t">The call</div>'
            f'<div class="v">{GLYPH[prediction]} {prediction}</div></div>'
            f'<div class="dc-result" style="background:{mark_c}">{mark}</div>'
            f'<div class="dc-tile" style="background:{COLOUR[actual_direction]}"><div class="t">What happened</div>'
            f'<div class="v">{GLYPH[actual_direction]} {actual_direction}</div></div></div>')


def range_bar(low, high, prev_close, price, price_label="Now", ends=True):
    """A horizontal bar: the expected range (blue band), yesterday's close (tick) and today's price (round pin)."""
    lo = min(low, price if price else low) * 0.998
    hi = max(high, price if price else high) * 1.002
    span = (hi - lo) or 1.0
    at = lambda x: f"{(x - lo) / span * 100:.1f}%"
    pin = ""
    if price:
        inside = low <= price <= high
        crowded = abs((price - prev_close) / span) < 0.32             # keep the two labels apart when the prices are close
        pin = (f'<div class="dc-pin" style="left:{at(price)};background:{UP_C if inside else DOWN_C}"></div>'
               f'<div class="dc-lbl{"" if crowded else " b"}" style="left:{at(price)};{"top:-1.15rem;" if crowded else ""}">{e(price_label)} {price:,.2f}</div>')
    return (f'<div class="dc-range"><div class="dc-track"></div>'
            f'<div class="dc-band" style="left:{at(low)};width:{(high - low) / span * 100:.1f}%"></div>'
            f'<div class="dc-tick" style="left:{at(prev_close)}"></div>'
            + (f'<div class="dc-lbl" style="left:{at(low)}">{low:,.0f}</div><div class="dc-lbl" style="left:{at(high)}">{high:,.0f}</div>' if ends else "") +
            f'<div class="dc-lbl b" style="left:{at(prev_close)}">Yesterday {prev_close:,.2f}</div>{pin}</div>')


def indicator_card(entry):
    name = VOTE_NAME[entry["vote"]]
    chip = f'<span class="dc-chip" style="background:{COLOUR[name]}">{GLYPH[name]} {name if entry["voting"] else entry["reading"]}</span>'
    if entry["voting"]:
        chip = f'<span class="dc-chip" style="background:{COLOUR[name]}">{GLYPH[name]} {"Neutral" if name == "Sideways" else name}</span>'
    return (f'<div class="dc-card{"" if entry["voting"] else " ctx"}"><div class="dc-name"><span>{e(entry["name"])}</span>{chip}</div>'
            f'<div class="dc-why">{e(entry["why"])}</div>{scale_html(entry["gauge"])}</div>')


def cards(entries):
    return '<div class="dc-grid">' + "".join(indicator_card(x) for x in entries) + "</div>"


def strip(rows):
    """One square per past day: green when the rule was right, red when wrong (oldest first)."""
    sq = "".join(f'<span class="dc-sq" title="{e(r["date"].strftime("%d %b"))}: called {e(r["predicted"])}, was {e(r["actual"])}" '
                 f'style="background:{UP_C if r["matched"] else DOWN_C}"></span>' for r in rows)
    return f'<div class="dc-strip">{sq}</div>'


def bars(rule_pct, coin_pct):
    """Two bars: how often the rule was right and the 50% coin-toss line."""
    def row(label, pct, colour):
        return (f'<div class="row"><div class="lab">{e(label)}</div><div class="bar"><div class="fill" style="width:{pct:.0f}%;background:{colour}"></div>'
                f'<div class="half"></div></div><div class="num">{pct:.0f}%</div></div>')
    return '<div class="dc-bars">' + row("This rule", rule_pct, "#2962ff") + row("Coin toss", coin_pct, FLAT_C) + "</div>"


# Pop-up (hover) descriptions for the Terminal view's indicator panel: what it is and how to read where it stands.
EXPLAIN = {
    "Trend": "Compares the price with its 50-day and 200-day average prices. Above both means a steady climb; below both a steady slide. The pointer shows how far the price is from its 50-day average.",
    "Bollinger band": "A band around the 20-day average that holds most price moves. Far above the band the price looks stretched and often drifts back; far below it often bounces. The pointer shows where the price sits inside the band.",
    "Stochastic RSI": "How the recent speed of price moves (RSI) compares with its own last 14 days. Near 0 is a short-term low that often snaps back; near 100 is a short-term high that often cools.",
    "Money flow (MFI)": "RSI that also counts trading volume: the balance of money flowing in and out. Below 20 means selling pressure may be exhausted; above 80 means buying may be crowded.",
    "Where it closed": "Where the last day ended between its low and its high. Closing at the very low often sees a bounce the next day; closing at the very high often sees a pause.",
    "Yesterday's move": "How much the price moved yesterday. After a sharp fall prices often rebound a little; after a sharp jump they often pull back a little.",
    "RSI (speed)": "A score from 0 to 100 of how fast the price has been rising or falling. Above 70 it has run up quickly; below 30 it has fallen quickly.",
    "MACD (momentum)": "Compares a quick and a slow average of the price. Above its signal line the momentum is rising; below it, fading.",
    "Trend strength (ADX)": "How strong a trend is, whichever way it points. Above 20 is a real trend. The pointer shows whether buyers or sellers are in the lead.",
    "Supertrend": "A line that trails the price and flips when the trend reverses. Price above the line is an uptrend, below it a downtrend.",
    "Ichimoku cloud": "A shaded zone built from past highs and lows that acts as support and resistance. Price above the cloud is bullish, below it bearish.",
    "Z-score": "How many standard deviations the price is from its own 20-day average. Above +2 the price is unusually high and often drifts back; below -2 it is unusually low and often bounces. Between is normal.",
    "Volume": "Today's trading activity compared with the usual level. Busy trading makes a move more believable.",
}


def terminal_card(entry):
    """A compact indicator card for the dashboard's right panel: its name, which way it leans, and a gauge. Hover for a description."""
    name = VOTE_NAME[entry["vote"]]
    word = {"Up": "Leans up", "Down": "Leans down", "Sideways": "Neutral"}[name]
    tip = EXPLAIN.get(entry["name"], entry["why"])
    return (f'<div class="dc-card tm" title="{e(tip)}">'
            f'<div class="dc-name"><span>{e(entry["name"])} <small style="opacity:.55;font-weight:500">&#9432;</small></span>'
            f'<span class="dc-chip" style="background:{COLOUR[name]}">{GLYPH[name]} {word}</span></div>'
            f'{scale_html(entry["gauge"])}</div>')


# Basic explanations for the "Learn the analysis" strip (hover a ? to read one)
HINTS = {
    "Fusion stage": "From CMT Level III, Chapter 8. It asks whether the price is in a clear uptrend (above a rising 200-day average, 50-day above 200-day) and also beating the market over six months. A stock that passes is in the 'Winner's Circle' trend test and tends to keep trending.",
    "Dow Theory": "From CMT Level I. An uptrend is a series of higher highs and higher lows; a downtrend is lower highs and lower lows. If both the swing highs and the swing lows agree, the trend is confirmed.",
    "Relative strength": "Compares the stock with the Nifty 50 (or Sensex). If the stock's line against the index is rising, it is beating the market, which usually signals leadership.",
    "Wyckoff effort vs result": "From the Wyckoff method. Effort is trading volume; result is how far the price moved. Big volume with a big move follows the move. Big volume with little movement means the other side is absorbing it: at lows that can be a bottom, at highs a top.",
    "Fibonacci confluence": "Prices often pause at 38.2%, 50% and 61.8% of the previous swing. A pullback in an uptrend that stops at one of those levels is a common support; a bounce in a downtrend that stops there is a common resistance.",
    "RSI": EXPLAIN["RSI (speed)"], "MACD": EXPLAIN["MACD (momentum)"], "ADX": EXPLAIN["Trend strength (ADX)"],
    "Z-score": EXPLAIN["Z-score"], "Supertrend": EXPLAIN["Supertrend"], "Bollinger band": EXPLAIN["Bollinger band"],
    "ML estimate": "A small machine-learning model (a logistic regression) that looks at the five CMT votes and a dozen indicator readings and gives the chance that the next day closes higher. It was trained on 137 NSE companies and checked on dates it had never seen. It is a second opinion, not a promise.",
    "Expected range": "Yesterday's close plus or minus a typical day's swing. About two days in three finish inside it. The blue marker is today's price and the tick is yesterday's close.",
    "The call": "The five CMT strategies each vote Up, Down or Neutral. Two or more net votes decide: Up, Down or Sideways. The coloured segments are the five votes.",
}


def learn_strip():
    """A row of small ? chips; hovering one shows a short plain-words explanation of that piece of analysis."""
    chips = "".join(f'<span class="lh">{e(n)} <b>?</b><span class="tip"><b>{e(n)}</b><br>{e(t)}</span></span>' for n, t in HINTS.items())
    return f'<div class="sc-head">Learn the analysis (hover a ? for a quick explanation)</div><div class="lh-row">{chips}</div>'


def _say(result):
    """One plain sentence: how many strategies lean which way, and how the day is going against that call."""
    p = result["prediction"]
    voters = [v for v in result["votes"] if v["voting"]]
    ups = sum(1 for v in voters if v["vote"] > 0)
    downs = sum(1 for v in voters if v["vote"] < 0)
    if p == "Sideways":
        first = f"The strategies are split ({ups} up, {downs} down), so the call is <b>sideways</b>."
    else:
        n = ups if p == "Up" else downs
        first = f"{n} of the {len(voters)} strategies point <b>{p.lower()}</b>, so the call is <b>{p.lower()}</b>."
    if result["actual"] is None:
        return first + " The market has not opened yet, so there is nothing to compare."
    a = result["actual_direction"]
    move = {"Up": "up", "Down": "down", "Sideways": "flat"}[a]
    verb = "So far today the price is" if result["status"] == "live" else "Today the price was"
    amount = f" {abs(result['change']) * 100:.2f}%" if a != "Sideways" else f" ({result['change'] * 100:+.2f}%)"
    verdict = "right" if result["matched"] else "wrong"
    return f"{first} {verb} <b>{move}</b>{amount}, so the call is <b>{verdict}</b>{' so far' if result['status'] == 'live' else ''}."


def prediction_panel(result, status_text="", footer="", stats=None, ml=None, learn=""):
    """Today's prediction in plain terms: a sentence that says what is going on, three simple cards (the call, the machine-learning
    second opinion, what happened), the expected range, and a table of the five strategies with each one's vote and back-test."""
    p = result["prediction"]
    cls = {"Up": "up", "Down": "down", "Sideways": "flat"}
    voters = [v for v in result["votes"] if v["voting"]]
    ups = sum(1 for v in voters if v["vote"] > 0)
    downs = sum(1 for v in voters if v["vote"] < 0)
    neutral = len(voters) - ups - downs
    edge = {"Up": "#26a69a", "Down": "#ef5350", "Sideways": "#9aa3b2"}[p]
    live = "live" in status_text.lower()
    head = (f'<div class="pp-head"><div><div class="pp-title">Today\'s prediction</div>'
            f'<div class="pp-sub">Using prices up to {result["basis_date"]:%A %d %b} (close Rs {result["prev_close"]:,.2f})</div></div>'
            f'<div class="pp-live{" on" if live else ""}"><i></i>{e(status_text)}</div></div>')
    say = f'<div class="pp-say" style="border-left-color:{edge}">{_say(result)}</div>'

    call = (f'<div class="pp-stat"><div class="pp-k">Our call</div><div class="pp-v {cls[p]}">{GLYPH[p]} {p}</div>'
            f'<div class="pp-d">{downs} down &middot; {ups} up &middot; {neutral} neutral<br>Two or more net votes decide.</div></div>')
    if ml:
        lean = ml["lean"]
        word = {"Up": "Leans up", "Down": "Leans down", "None": "No clear view"}[lean]
        mcls = {"Up": "up", "Down": "down", "None": "flat"}[lean]
        held = ml["tested"].get("last 30% of dates (held back)", {})
        conf = held.get("confident_accuracy")
        tested = f"Tested on unseen dates: right {held['accuracy'] * 100:.0f}% overall, {conf * 100:.0f}% when confident." if conf else ""
        drivers = ", ".join(f"{n} ({'up' if v > 0 else 'down'})" for n, v in ml["top"])
        mlc = (f'<div class="pp-stat" title="Biggest influences today: {e(drivers)}"><div class="pp-k">Machine-learning second opinion</div>'
               f'<div class="pp-v {mcls}">{word}</div><div class="pp-pbar"><i style="width:{ml["p_up"] * 100:.0f}%"></i><u></u></div>'
               f'<div class="pp-d">{ml["p_up"] * 100:.0f}% chance the price closes higher.<br>{e(tested)}</div></div>')
    else:
        mlc = ""
    if result["actual"] is None:
        out = ('<div class="pp-stat"><div class="pp-k">What happened</div><div class="pp-v flat">Not yet</div>'
               '<div class="pp-d">Waiting for today\'s price.</div></div>')
    else:
        a = result["actual_direction"]
        out = (f'<div class="pp-stat"><div class="pp-k">What happened {"so far" if result["status"] == "live" else "today"}</div>'
               f'<div class="pp-v {cls[a]}">{GLYPH[a]} {a}</div>'
               f'<div class="pp-d">{result["change"] * 100:+.2f}% &middot; Rs {result["actual"]:,.2f}<br>'
               f'The call was <b class="{"up" if result["matched"] else "down"}">{"right" if result["matched"] else "wrong"}</b>.</div></div>')
    low, high = result["range"]
    inside = ""
    if result["actual"] is not None:
        inside = f' &middot; the price is <b>{"inside" if result["in_range"] else "outside"}</b> it'
    rng = (f'<div class="pp-rangebox"><div class="pp-k">Expected range today: Rs {low:,.0f} to Rs {high:,.0f}{inside} '
           f'<span style="opacity:.7">(yesterday\'s close plus or minus a typical day\'s swing)</span></div>'
           f'{range_bar(low, high, result["prev_close"], result["actual"], "Now" if result["status"] == "live" else "Close")}</div>')
    rows = []
    for en in result["votes"]:
        avail = en.get("available", True)
        name = VOTE_NAME[en["vote"]]
        word = "n/a" if not avail else f"{GLYPH[name]} " + ("Neutral" if name == "Sideways" else name)
        rec = (stats or {}).get("strategies", {}).get(en["name"])
        tested = ""
        if rec:
            tested = (f'{rec["next day"]["last 30% of dates"]["accuracy"] * 100:.0f}% next day &middot; '
                      f'{rec["next 20 days"]["last 30% of dates"]["accuracy"] * 100:.0f}% over 20 days')
        rows.append(f'<tr title="{e(en["why"])}"><td class="pp-sname">{e(en["name"])}</td>'
                    f'<td class="pp-vote {cls[name] if avail else "flat"}">{word}</td><td>{e(en["reading"])}</td><td class="pp-test">{tested}</td></tr>')
    table = ('<div class="pp-sec">The five strategies behind the call<small>hover a row to read why</small></div>'
             '<table class="pp-table"><tr><th>Strategy</th><th>Vote</th><th>What it sees</th><th>Back-test: how often it was right</th></tr>'
             + "".join(rows) + "</table>") if rows else ""
    foot = f'<div class="pp-foot">{footer}</div>' if footer else ""
    return f'<div class="pp">{head}{say}<div class="pp-stats">{call}{mlc}{out}</div>{rng}{table}{learn}{foot}</div>'
