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
.ss-grid { display:grid; grid-template-columns:1.5fr .8fr 1.7fr 1.9fr .8fr; gap:.8rem; align-items:center; padding:.75rem .7rem; }
.ss-head { font-size:.85rem; font-weight:600; color:var(--tm-muted,#6b7785); border-bottom:1px solid var(--tm-line,#dfe3ea); padding-top:.4rem; padding-bottom:.4rem; }
.ss-det { border-bottom:1px solid var(--tm-line,#dfe3ea); } .ss-det:last-of-type { border-bottom:0; }
.ss-det > summary { list-style:none; cursor:pointer; font-size:1rem; } .ss-det > summary::-webkit-details-marker { display:none; }
.ss-det > summary:hover { background:rgba(128,128,128,.06); }
.ss-open { font-weight:700; color:#2962ff; white-space:nowrap; } .ss-open::after { content:" \\25BE"; } .ss-det[open] .ss-open::after { content:" \\25B4"; }
.ss-view { padding:.4rem .7rem 1.2rem .7rem; } .ss-view svg { width:100%; height:auto; display:block; color:var(--tm-ink,#1d3557); }
.ss-view ul { margin:.6rem 0 0 1.1rem; padding:0; font-size:.98rem; line-height:1.6; } .ss-view li b { font-weight:700; }
.ss-key { display:flex; flex-wrap:wrap; gap:.4rem 1.2rem; font-size:.85rem; color:var(--tm-muted,#6b7785); margin:.4rem 0 0 0; } .ss-key i { display:inline-block; width:1.1rem; height:.28rem; border-radius:3px; margin-right:.35rem; vertical-align:middle; }
@media (max-width:1100px){ .ss-grid { grid-template-columns:1.4fr .8fr .8fr; } .ss-grid > :nth-child(3), .ss-grid > :nth-child(4) { display:none; } }
.fg-box.open { max-height:none; overflow:visible; }
.fg-box { max-height:330px; overflow-y:auto; border:1px solid var(--tm-line,#dfe3ea); border-radius:10px; padding:1rem 1.2rem; margin-top:.8rem; background:rgba(128,128,128,.04); }
.fg-title { font-weight:700; font-size:1.05rem; } .fg-title small { font-weight:400; color:var(--tm-muted,#6b7785); margin-left:.5rem; font-size:.85rem; }
.fg-here { margin:.7rem 0; padding:.6rem .85rem; border-left:4px solid #2962ff; background:rgba(41,98,255,.07); border-radius:0 8px 8px 0; font-size:.95rem; line-height:1.5; }
.fg-h { font-weight:700; margin:1rem 0 .3rem 0; font-size:.95rem; } .fg-box ul { margin:.2rem 0 0 1.1rem; padding:0; font-size:.93rem; line-height:1.55; }
.fg-note { font-size:.88rem; color:var(--tm-muted,#6b7785); margin-top:.5rem; line-height:1.5; }
.fg-cards { display:grid; grid-template-columns:repeat(2,1fr); gap:.7rem; }
.fg-card { border:1px solid var(--tm-line,#dfe3ea); border-left-width:5px; border-radius:10px; padding:.7rem .9rem; font-size:.92rem; }
.fg-card.g-up { border-left-color:#26a69a; } .fg-card.g-flat { border-left-color:#d98e04; } .fg-card.g-down { border-left-color:#ef5350; }
.fg-card.here { background:rgba(41,98,255,.07); box-shadow:0 0 0 2px #2962ff inset; }
.fg-name { font-weight:700; font-size:1rem; } .fg-tag { margin-left:.5rem; font-size:.72rem; font-weight:700; color:#2962ff; text-transform:uppercase; letter-spacing:.05em; }
.fg-rule { color:var(--tm-muted,#6b7785); margin:.15rem 0 .3rem 0; } .fg-verdict { margin-top:.4rem; font-size:.88rem; line-height:1.45; }
@media (max-width:1100px){ .fg-cards { grid-template-columns:1fr; } }
.bm { text-align:center; } .bm .up { color:var(--pp-up,#158a7e); } .bm .down { color:var(--pp-down,#d6453d); } .bm .flat { color:var(--pp-flat,#6b7785); } .bm svg { width:100%; max-width:10rem; height:auto; display:block; margin:.2rem auto 0 auto; }
.bm-word { font-size:1.45rem; font-weight:700; line-height:1.15; margin-top:.1rem; } .bm-sub { font-size:.92rem; color:var(--tm-muted,#6b7785); margin-top:.25rem; line-height:1.4; }
.bm-ends { display:flex; justify-content:space-between; font-size:.78rem; color:var(--tm-muted,#6b7785); margin:-.1rem .35rem 0 .35rem; }
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
    "ML model": "A small machine-learning model (a logistic regression) that looks at the five CMT readings and a dozen indicator readings and gives a modelled chance that the next day closes higher. It was trained on 137 NSE companies and checked on dates it had never seen. It describes what the model reads, not what will happen.",
    "Typical range": "Yesterday's close plus or minus a typical day's swing. About two days in three finish inside it. The blue marker is today's price and the tick is yesterday's close.",
    "The model reading": "The five CMT strategies each read Up, Down or Neutral from yesterday\'s data. Two or more net readings decide: Up, Down or Sideways. This is a description of what the methods show, not a recommendation.",
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
        first = f"The strategies are split ({ups} up, {downs} down), so the model reading is <b>sideways</b>."
    else:
        n = ups if p == "Up" else downs
        first = f"{n} of the {len(voters)} strategies read <b>{p.lower()}</b>, so the model reading is <b>{p.lower()}</b>."
    if result["actual"] is None:
        return first + " The market has not opened yet, so there is nothing to compare."
    a = result["actual_direction"]
    move = {"Up": "up", "Down": "down", "Sideways": "flat"}[a]
    verb = "So far today the price is" if result["status"] == "live" else "Today the price was"
    amount = f" {abs(result['change']) * 100:.2f}%" if a != "Sideways" else f" ({result['change'] * 100:+.2f}%)"
    verdict = "matches" if result["matched"] else "does not match"
    return f"{first} {verb} <b>{move}</b>{amount}, which <b>{verdict}</b> that reading{' so far' if result['status'] == 'live' else ''}."


def today_strip(result, status_text=""):
    """A slim live card: how today is going against the strategies' reading, and the typical range with the price on it."""
    p = result["prediction"]
    edge = {"Up": "#26a69a", "Down": "#ef5350", "Sideways": "#9aa3b2"}[p]
    live = "live" in status_text.lower()
    low, high = result["range"]
    inside = ""
    if result["actual"] is not None:
        inside = f' &middot; the price is <b>{"inside" if result["in_range"] else "outside"}</b> it'
    return (f'<div class="pp"><div class="pp-head"><div class="pp-title">Today so far</div>'
            f'<div class="pp-live{" on" if live else ""}"><i></i>{e(status_text)}</div></div>'
            f'<div class="pp-say" style="border-left-color:{edge}">{_say(result)}</div>'
            f'<div class="pp-k">Typical range today: Rs {low:,.0f} to Rs {high:,.0f}{inside} '
            f'<span style="opacity:.7">(yesterday\'s close plus or minus a typical day\'s swing). Educational only, not a recommendation.</span></div>'
            f'{range_bar(low, high, result["prev_close"], result["actual"], "Now" if result["status"] == "live" else "Close")}</div>')


# ---------------- the strategies card, with a full view of each strategy ----------------
def _chart(series, markers=(), hlines=(), dates=None, width=820, height=250, volume=None):
    """A small SVG line chart. series: [(values, colour, width, dashed)]; markers: [(index, value, colour, shape)];
    hlines: [(value, colour, label)]; volume: (bars, average) drawn in a strip underneath."""
    left, right, top = 54, 14, 12
    vol_h = 54 if volume else 0
    bottom = 26 + vol_h
    pw, ph = width - left - right, height - top - bottom
    vals = [v for ser, *_ in series for v in ser if v is not None] + [v for _, v, *_ in markers] + [v for v, *_ in hlines]
    lo, hi = min(vals), max(vals)
    pad = (hi - lo) * 0.06 or 1.0
    lo, hi = lo - pad, hi + pad
    n = max(len(ser) for ser, *_ in series)
    x = lambda i: left + i / max(n - 1, 1) * pw
    y = lambda v: top + (1 - (v - lo) / (hi - lo)) * ph
    out = [f'<svg viewBox="0 0 {width} {height}" role="img">']
    for k in range(4):                                             # grid and price labels
        v = lo + (hi - lo) * k / 3
        out.append(f'<line x1="{left}" x2="{width - right}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="currentColor" opacity=".12"/>'
                   f'<text x="{left - 6}" y="{y(v) + 4:.1f}" text-anchor="end" font-size="11" fill="currentColor" opacity=".6">{v:,.0f}</text>')
    for value, colour, label in hlines:
        out.append(f'<line x1="{left}" x2="{width - right}" y1="{y(value):.1f}" y2="{y(value):.1f}" stroke="{colour}" stroke-width="1.4" stroke-dasharray="5 4"/>'
                   f'<text x="{width - right - 4}" y="{y(value) - 4:.1f}" text-anchor="end" font-size="11" fill="{colour}" font-weight="700">{e(label)}</text>')
    for ser, colour, w, dashed in series:
        pts = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(ser) if v is not None)
        if pts:
            dash = ' stroke-dasharray="6 4"' if dashed else ""
            out.append(f'<polyline points="{pts}" fill="none" stroke="{colour}" stroke-width="{w}" stroke-linejoin="round"{dash}/>')
    for i, v, colour, shape in markers:
        if shape == "up":
            out.append(f'<path d="M {x(i):.1f} {y(v) - 8:.1f} l 6 11 h -12 z" fill="{colour}"/>')
        elif shape == "down":
            out.append(f'<path d="M {x(i):.1f} {y(v) + 8:.1f} l 6 -11 h -12 z" fill="{colour}"/>')
        else:
            out.append(f'<circle cx="{x(i):.1f}" cy="{y(v):.1f}" r="5" fill="{colour}" stroke="#fff" stroke-width="1.5"/>')
    if volume:
        bars, avg = volume
        vtop, vh = height - bottom + 14, vol_h - 14
        vmax = max(v for v in bars if v is not None) or 1
        bw = max(pw / n - 1, 1)
        for i, v in enumerate(bars):
            if v:
                out.append(f'<rect x="{x(i) - bw / 2:.1f}" y="{vtop + vh - v / vmax * vh:.1f}" width="{bw:.1f}" height="{v / vmax * vh:.1f}" fill="#868993" opacity=".55"/>')
        pts = " ".join(f"{x(i):.1f},{vtop + vh - v / vmax * vh:.1f}" for i, v in enumerate(avg) if v is not None)
        if pts:
            out.append(f'<polyline points="{pts}" fill="none" stroke="#d98e04" stroke-width="1.6"/>')
        out.append(f'<text x="{left - 6}" y="{vtop + 10:.1f}" text-anchor="end" font-size="11" fill="currentColor" opacity=".6">Volume</text>')
    if dates:
        for i in (0, len(dates) // 2, len(dates) - 1):
            anchor = "start" if i == 0 else "end" if i == len(dates) - 1 else "middle"
            out.append(f'<text x="{x(i):.1f}" y="{height - 6}" text-anchor="{anchor}" font-size="11" fill="currentColor" opacity=".6">{dates[i]:%d %b %Y}</text>')
    out.append("</svg>")
    return "".join(out)


def _key(items):
    return '<div class="ss-key">' + "".join(f'<span><i style="background:{c}"></i>{e(t)}</span>' for t, c in items) + "</div>"


def _tick(ok):
    return '<b class="up">&#10003;</b>' if ok else '<b class="down">&#10007;</b>'


def strategy_view(name, v, fusion=None):
    """The full view of one strategy: a chart of what it looks at, a key, and a few plain lines on what it is doing today."""
    ink, amber, blue, teal, red = "#5b6573", "#d98e04", "#2962ff", UP_C, DOWN_C
    d = v["dates"]
    if name == "Fusion stage":
        f = v["fusion"]
        chart = _chart([(v["close"], ink, 2.2, False), (v["sma50"], amber, 1.8, False), (v["sma200"], blue, 1.8, False)], dates=d)
        key = _key([("Price", ink), ("50-day average", amber), ("200-day average", blue)])
        return chart + key + fusion_guide(fusion, f)
    elif name == "Dow Theory":
        hi, lo = v["dow_high"], v["dow_low"]
        marks = [(i, val, red, "down") for i, val in hi] + [(i, val, teal, "up") for i, val in lo]
        chart = _chart([(v["close"], ink, 2.0, False)], markers=marks, dates=d)
        key = _key([("Price", ink), ("Swing high", red), ("Swing low", teal)])
        last = v["dow_last"]
        pts = []
        if len(last["highs"]) == 2 and len(last["lows"]) == 2:
            (h1, h2), (l1, l2) = last["highs"], last["lows"]
            pts.append(f"{_tick(h2 > h1)} The last two swing highs: Rs {h1:,.0f} then Rs {h2:,.0f} ({'higher' if h2 > h1 else 'lower'}).")
            pts.append(f"{_tick(l2 > l1)} The last two swing lows: Rs {l1:,.0f} then Rs {l2:,.0f} ({'higher' if l2 > l1 else 'lower'}).")
        pts.append("Higher highs <b>and</b> higher lows confirm an uptrend; lower highs and lower lows confirm a downtrend; a mix means no confirmed trend.")
    elif name == "Relative strength":
        if "rs" not in v:
            return "<p>The market index is not available for this company.</p>"
        chart = _chart([(v["rs"], blue, 2.2, False), (v["rs_ma50"], amber, 1.8, False)], hlines=[(100, "#868993", "start = 100")], dates=d)
        key = _key([("Stock divided by the index (start = 100)", blue), ("Its 50-day average", amber)])
        chg = v.get("rs_chg63")
        pts = [(f"Over the last 3 months the stock has moved <b>{chg * 100:+.1f}%</b> {'ahead of' if chg > 0 else 'behind'} the index." if chg is not None else ""),
               "A rising line means the stock is <b>beating</b> the market; a falling line means it is <b>lagging</b>. The vote is Up when the line is above its 50-day average and has risen over three months."]
        pts = [p for p in pts if p]
    elif name == "Wyckoff effort vs result":
        if "volume" not in v:
            return "<p>This company has no usable trading volume, so the Wyckoff reading is not available.</p>"
        chart = _chart([(v["close"], ink, 2.0, False)], dates=d, height=300, volume=(v["volume"], v["vol_ma20"]))
        key = _key([("Price", ink), ("Daily volume", "#868993"), ("20-day average volume", amber)])
        w = v["wy"]
        pts = [f"<b>Effort:</b> yesterday's volume was <b>{w['effort']:.1f}x</b> the usual level.",
               f"<b>Result:</b> the price moved <b>{w['move'] * 100:+.2f}%</b>, which is <b>{w['result']:.1f}x</b> a typical day's range.",
               "Big effort with a big result follows the move. Big effort with little result is a stall: near the lows that suggests sellers are being absorbed, near the highs it suggests buyers are exhausted."]
    else:                                                          # Fibonacci confluence
        fb = v["fib"]
        lines = [(fb["hi"], "#868993", f"swing high {fb['hi']:,.0f}"), (fb["lo"], "#868993", f"swing low {fb['lo']:,.0f}")] + \
                [(price, c, f"{lv * 100:.1f}%") for (lv, price), c in zip(fb["levels"], (amber, "#6b7785", red))]
        chart = _chart([(v["close"], ink, 2.2, False)], markers=[(len(v["close"]) - 1, v["close"][-1], blue, "dot")], hlines=lines, dates=d)
        key = _key([("Price (blue dot = yesterday's close)", ink), ("Fibonacci levels", amber)])
        pts = [f"The last six months went <b>{'up' if fb['rising'] else 'down'}</b>, from Rs {(fb['lo'] if fb['rising'] else fb['hi']):,.0f} to Rs {(fb['hi'] if fb['rising'] else fb['lo']):,.0f}.",
               f"The price has {'pulled back' if fb['rising'] else 'bounced'} <b>{fb['depth'] * 100:.0f}%</b> of that move.",
               "Prices often pause at 38.2%, 50% and 61.8%. A pullback to one of them in an uptrend is read as support (Up); a bounce to one in a downtrend is read as resistance (Down)."]
    return chart + key + "<ul>" + "".join(f"<li>{p}</li>" for p in pts) + "</ul>"


# The four Winner's Circle groups (CMT Level III, Chapter 8), with plain English names instead of numbers
GROUPS = [
    ("Winner's Circle", "Trend and momentum, quality and valuation all pass.",
     ["Passes the trend and momentum test.", "Passes the quality-of-fundamentals test.", "Passes the valuation test."],
     "Confirm. The market's trend backs up the fundamentals and the valuation. Aim for many of these.", "up"),
    ("Strong contender", "Trend and momentum pass, plus one of quality or valuation.",
     ["Passes the trend and momentum test.", "Passes the quality test OR the valuation test, but not both."],
     "Confirm, with a caveat. The trend is confirmed and one of fundamentals or valuation supports it; keep an eye on the other. Some of these.", "up"),
    ("Momentum only", "Trend and momentum pass, but neither quality nor valuation does.",
     ["Passes the trend and momentum test.", "Fails the quality test.", "Fails the valuation test."],
     "Divergence: trend without fundamentals. When the two disagree, give risk management more weight: smaller positions, tighter stops, reassess. Few of these.", "flat"),
    ("Watchlist", "The price trend and momentum have not (yet) confirmed.",
     ["Fails the trend and momentum test (whatever the fundamentals say)."],
     "If quality and valuation both look fine: Delay, wait for the trend to confirm. Otherwise: Reject for now. Avoid these.", "down"),
]


def fusion_guide(row, f, scroll=False):
    """A scrollable box with everything that decides which of the four groups a company is in, and where this one stands now."""
    here = None
    if row:
        here = int(row["group"]) - 1
    checks = [f.get("above200"), f.get("s50_over_s200"), f.get("rising200"),
              (f.get("ret6") is not None and f["ret6"] > 0), (f.get("ret6") is not None and f.get("bench6") is not None and f["ret6"] > f["bench6"])]
    passed = sum(1 for c in checks if c)
    if row:
        status = (f'<div class="fg-here"><b>This company today: {e(GROUPS[here][0])}.</b> Trend stage: {e(row["stage_name"])}. '
                  f'Quality {"passes" if row["quality_ok"] else "does not pass"}; valuation {"passes" if row["value_ok"] else "does not pass"}.</div>')
    else:
        status = (f'<div class="fg-here"><b>This company today:</b> company results are not available for it, so only the price trend can be '
                  f'checked: {passed} of the 5 trend and momentum checks pass.</div>')
    trend = ('<div class="fg-h">The gate: trend and momentum (all must pass for the top three groups)</div><ul>'
             '<li><b>Clear uptrend:</b> the price is above its 200-day average, the 50-day average is above the 200-day average, and the 200-day average is rising (higher than 20 days ago).</li>'
             '<li><b>Positive momentum:</b> the six-month return is above zero.</li>'
             '<li><b>Outperformance:</b> the six-month return is ahead of the Nifty 50 (Sensex for a BSE listing).</li></ul>'
             '<div class="fg-note">The trend stage itself has four English names, from how many of the three uptrend checks pass: '
             '<b>Clear uptrend</b> (3), <b>Base of an uptrend</b> (2), <b>Base of a downtrend</b> (1) and <b>Clear downtrend</b> (0).</div>')
    tests = ('<div class="fg-h">The two other tests (each a 0 to 100 score against the other companies; 50 or more passes)</div><ul>'
             '<li><b>Quality of fundamentals:</b> the average of growth (revenue growth and earnings growth), returns (return on equity and operating margin) and low debt-to-equity.</li>'
             '<li><b>Valuation:</b> the average rank of a low price-to-earnings ratio and a low price-to-book ratio.</li></ul>')
    cards = ""
    for i, (name, rule, reqs, verdict, tone) in enumerate(GROUPS):
        mark = '<span class="fg-tag">this company</span>' if i == here else ""
        cards += (f'<div class="fg-card g-{tone}{" here" if i == here else ""}"><div class="fg-name">{e(name)}{mark}</div><div class="fg-rule">{e(rule)}</div>'
                  f'<ul>{"".join(f"<li>{e(r)}</li>" for r in reqs)}</ul><div class="fg-verdict">{e(verdict)}</div></div>')
    return (f'<div class="fg-box{"" if scroll else " open"}" tabindex="0"><div class="fg-title">The four groups of the Winner\'s Circle<small>CMT Level III, Chapter 8</small></div>'
            f'{status}{trend}{tests}<div class="fg-h">The four groups</div><div class="fg-cards">{cards}</div></div>')


def strategy_rows(result, stats=None, ml=None):
    """The rows of the strategies table: [{name, word, cls, reading, tested}] for the five strategies, then the ML model."""
    cls = {"Up": "up", "Down": "down", "Sideways": "flat"}
    out = []
    for en in result["votes"]:
        avail = en.get("available", True)
        name = VOTE_NAME[en["vote"]]
        rec = (stats or {}).get("strategies", {}).get(en["name"])
        tested = (f'{rec["next day"]["last 30% of dates"]["accuracy"] * 100:.0f}% next day &middot; '
                  f'{rec["next 20 days"]["last 30% of dates"]["accuracy"] * 100:.0f}% over 20 days') if rec else ""
        out.append({"name": en["name"], "word": "n/a" if not avail else f"{GLYPH[name]} " + ("Neutral" if name == "Sideways" else name),
                    "cls": cls[name] if avail else "flat", "reading": en["reading"], "tested": tested})
    if ml:
        held = ml["tested"].get("last 30% of dates (held back)", {})
        lean = ml["lean"]
        word = {"Up": f"{GLYPH['Up']} Up", "Down": f"{GLYPH['Down']} Down", "None": "No clear view"}[lean]
        tested = (f'{held["accuracy"] * 100:.0f}% overall &middot; {held["confident_accuracy"] * 100:.0f}% when confident' if held.get("confident_accuracy") else "")
        out.append({"name": "ML model", "word": word, "cls": {"Up": "up", "Down": "down", "None": "flat"}[lean],
                    "reading": f'{ml["p_up"] * 100:.0f}% modelled chance of a higher close', "tested": tested})
    return out


def ml_view(ml):
    """The full view of the ML model: today's reading, what pushed it, and how it was built and tested, in plain words."""
    p = ml["p_up"]
    lean = {"Up": "leans up", "Down": "leans down", "None": "has no clear view"}[ml["lean"]]
    contrib = ml["contrib"][:8]
    big = max(abs(v) for _, v in contrib) or 1.0
    width, row_h, label_w, mid = 820, 30, 230, 540
    rows = []
    for i, (label, v) in enumerate(contrib):
        y = 8 + i * row_h
        w = abs(v) / big * 190
        x = mid if v >= 0 else mid - w
        colour = UP_C if v >= 0 else DOWN_C
        rows.append(f'<text x="{label_w - 8}" y="{y + 15}" text-anchor="end" font-size="13" fill="currentColor">{e(label)}</text>'
                    f'<rect x="{x:.1f}" y="{y + 3}" width="{max(w, 2):.1f}" height="17" rx="3" fill="{colour}" opacity=".85"/>'
                    f'<text x="{(x + w + 6) if v >= 0 else (x - 6):.1f}" y="{y + 16}" text-anchor="{"start" if v >= 0 else "end"}" font-size="12" fill="currentColor" opacity=".7">'
                    f'{"pushes up" if v >= 0 else "pushes down"}</text>')
    height = 8 + len(contrib) * row_h + 24
    svg = (f'<svg viewBox="0 0 {width} {height}" role="img"><line x1="{mid}" x2="{mid}" y1="2" y2="{height - 20}" stroke="currentColor" opacity=".35"/>'
           f'{"".join(rows)}<text x="{mid - 6}" y="{height - 4}" text-anchor="end" font-size="12" fill="currentColor" opacity=".6">towards a lower close</text>'
           f'<text x="{mid + 6}" y="{height - 4}" font-size="12" fill="currentColor" opacity=".6">towards a higher close</text></svg>')
    bar = (f'<div class="pp-pbar" style="margin:1rem 0 .3rem 0"><i style="width:{p * 100:.0f}%"></i><u></u></div>'
           f'<div class="pp-d">{p * 100:.0f}% modelled chance that the next close is higher (the model says it needs 54% or more to lean up, 46% or less to lean down).</div>')
    t = ml["tested"].get("last 30% of dates (held back)", {})
    m = ml.get("model", {})
    held = (f'<li><b>Overall:</b> right {t["accuracy"] * 100:.1f}% of the time on dates it never saw. Simply guessing "up" every day scores {t["always_up"] * 100:.1f}%, so over all days it adds almost nothing.</li>'
            f'<li><b>On its confident days</b> (about {t["confident_days"] / t["days"] * 100:.0f}% of days): right {t["confident_accuracy"] * 100:.1f}% of the time over {t["confident_days"]:,} stock-days. '
            'Those days bunch together on market-wide days, so treat it lightly.</li>') if t else ""
    return (f'<p>Today this model <b>{lean}</b>.</p>{bar}<div class="fg-h">What pushed today\'s reading</div>{svg}'
            '<div class="fg-h">How it works</div><ul>'
            '<li><b>The type of model:</b> a logistic regression, a simple and explainable model (not deep learning). It adds up weighted inputs and turns the total into a chance between 0% and 100%.</li>'
            '<li><b>Its 18 inputs</b>, all from yesterday and earlier: the five strategy readings (Fusion stage, Dow Theory, relative strength, Wyckoff, Fibonacci), '
            'RSI, Stochastic RSI, the position in the Bollinger band, the Z-score, MACD, ADX direction and strength, Supertrend, yesterday\'s move, the last 5 days, '
            'where yesterday closed in its range, volume against usual, volatility and the distance from the 200-day average.</li>'
            '<li><b>The question it answers:</b> will the next day close higher than today?</li></ul>'
            '<div class="fg-h">How it was built and tested</div><ul>'
            f'<li><b>Training data:</b> the saved daily prices of {m.get("companies", "many")} NSE companies, 2019 to 2026, about {m.get("rows", 0):,} company-days, all pooled into one model.</li>'
            f'<li><b>The test was fair:</b> it learned only from the first 70% of the dates (up to {m.get("split_date", "")}). The last 30% were kept back and used only to check it.</li>'
            f'{held}</ul>'
            '<div class="fg-h">What to keep in mind</div><ul>'
            '<li>It uses prices and volume only: no news, no company results, no sentiment.</li>'
            '<li>It was trained once and is not updated automatically. The company list is today\'s, so companies that failed are missing.</li>'
            '<li>It describes what a model reads from past patterns. It is not a recommendation to buy or sell.</li></ul>')


def barometer(score, n, ups, downs, neutral):
    """A half-circle barometer for the combined reading of the strategies: five bands from 'Down' (red) through 'Neutral' (grey) to
    'Up' (green), with a needle at the net vote (-n to +n)."""
    import math
    cx, cy, r = 60, 58, 46
    pos = (score + n) / (2 * n) if n else 0.5
    bands = ["#ef5350", "#f4958f", "#c4c9d2", "#85cfc6", "#26a69a"]
    def arc(p0, p1):
        a0, a1 = math.pi * (1 - p0), math.pi * (1 - p1)
        x0, y0, x1, y1 = cx + r * math.cos(a0), cy - r * math.sin(a0), cx + r * math.cos(a1), cy - r * math.sin(a1)
        return f"M {x0:.2f} {y0:.2f} A {r} {r} 0 0 1 {x1:.2f} {y1:.2f}"
    segs = "".join(f'<path d="{arc(i / 5 + 0.006, (i + 1) / 5 - 0.006)}" stroke="{c}" stroke-width="11" fill="none"/>' for i, c in enumerate(bands))
    ang = math.pi * (1 - min(max(pos, 0.0), 1.0))
    nx, ny = cx + (r - 9) * math.cos(ang), cy - (r - 9) * math.sin(ang)
    needle = (f'<line x1="{cx}" y1="{cy}" x2="{nx:.2f}" y2="{ny:.2f}" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>'
              f'<circle cx="{cx}" cy="{cy}" r="5" fill="currentColor"/>')
    if score >= 3:
        word, cls = "Strongly up", "up"
    elif score >= 1:
        word, cls = "Leans up", "up"
    elif score <= -3:
        word, cls = "Strongly down", "down"
    elif score <= -1:
        word, cls = "Leans down", "down"
    else:
        word, cls = "Balanced", "flat"
    return (f'<div class="bm"><svg viewBox="0 0 120 66" role="img" aria-label="Combined strategy reading: {word}">{segs}{needle}</svg>'
            f'<div class="bm-ends"><span>Down</span><span>Neutral</span><span>Up</span></div>'
            f'<div class="bm-word"><span class="{cls}">{word}</span></div>'
            f'<div class="bm-sub">{downs} of {n} strategies read down, {ups} up, {neutral} neutral</div></div>')
