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
.pb { background:var(--tm-panel,#fff); border:1px solid var(--tm-line,#dfe3ea); border-radius:14px; padding:1.1rem 1.6rem 1rem 1.6rem; box-shadow:0 1px 3px rgba(16,24,40,.07); }
.pb-head { display:flex; justify-content:space-between; align-items:flex-start; gap:1rem; margin-bottom:.9rem; }
.pb-title { font-size:1.15rem; font-weight:700; color:var(--tm-ink,#1d3557); line-height:1.2; }
.pb-sub { font-size:.85rem; color:var(--tm-muted,#6b7785); margin-top:.15rem; }
.pb-pill { display:inline-flex; align-items:center; gap:.45rem; font-size:.8rem; font-weight:600; padding:.25rem .8rem; border-radius:99px; border:1px solid var(--tm-line,#dfe3ea); color:var(--tm-muted,#6b7785); white-space:nowrap; }
.pb-pill i { width:.5rem; height:.5rem; border-radius:50%; background:#868993; display:inline-block; } .pb-pill.live { color:#1f8f84; border-color:rgba(38,166,154,.35); background:rgba(38,166,154,.08); }
.pb-pill.live i { background:#26a69a; box-shadow:0 0 0 0 rgba(38,166,154,.6); animation:pbpulse 1.8s infinite; }
@keyframes pbpulse { 70% { box-shadow:0 0 0 .45rem rgba(38,166,154,0); } 100% { box-shadow:0 0 0 0 rgba(38,166,154,0); } }
.pb-main { display:grid; grid-template-columns:1fr 1fr 1.7fr; gap:.9rem; }
.pb-box { border:1px solid var(--tm-line,#dfe3ea); border-radius:12px; padding:.85rem 1.1rem; min-width:0; background:rgba(128,128,128,.035); }
.pb-l { font-size:.7rem; letter-spacing:.09em; text-transform:uppercase; color:var(--tm-muted,#6b7785); font-weight:600; margin-bottom:.45rem; }
.pb-big { display:flex; align-items:center; gap:.8rem; }
.pb-badge { width:3.1rem; height:3.1rem; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:1.35rem; flex:0 0 auto; }
.pb-word { font-size:1.9rem; font-weight:800; line-height:1; letter-spacing:.01em; }
.pb-line { font-size:.88rem; color:var(--tm-muted,#6b7785); margin-top:.35rem; }
.pb-meter { display:flex; gap:.25rem; margin-top:.7rem; } .pb-meter span { flex:1; height:.4rem; border-radius:99px; }
.pb-meterl { font-size:.78rem; color:var(--tm-muted,#6b7785); margin-top:.35rem; }
.pb-verdict { display:inline-flex; align-items:center; gap:.4rem; font-weight:700; font-size:.92rem; padding:.28rem .8rem; border-radius:99px; margin-top:.55rem; }
.pb-rng { display:flex; justify-content:space-between; font-size:.9rem; font-weight:600; margin-bottom:.1rem; } .pb-rng span:last-child { text-align:right; }
.pb-box .dc-range { margin:1.1rem .2rem 1.5rem .2rem; height:2rem; }
.sc-head { font-size:.7rem; letter-spacing:.09em; text-transform:uppercase; color:var(--tm-muted,#6b7785); font-weight:600; margin:1.1rem 0 .5rem 0; }
.sc-row { display:grid; grid-template-columns:repeat(5,1fr); gap:.75rem; }
.sc { border:1px solid var(--tm-line,#dfe3ea); border-left-width:4px; border-radius:10px; padding:.65rem .85rem .6rem .85rem; min-width:0; cursor:help; }
.sc-top { display:flex; justify-content:space-between; align-items:baseline; gap:.5rem; } .sc-n { font-weight:700; font-size:.95rem; line-height:1.2; }
.sc-v { font-size:.78rem; font-weight:800; letter-spacing:.04em; text-transform:uppercase; white-space:nowrap; }
.sc-src { font-size:.68rem; letter-spacing:.07em; text-transform:uppercase; color:var(--tm-muted,#6b7785); margin:.15rem 0 .4rem 0; }
.sc-r { font-size:.92rem; font-weight:600; line-height:1.3; min-height:2.4em; }
.sc-t { font-size:.74rem; color:var(--tm-muted,#6b7785); margin-top:.45rem; }
.pb-note { margin-top:.9rem; font-size:.84rem; line-height:1.5; color:var(--tm-muted,#6b7785); }
.pb-foot { margin-top:.8rem; padding-top:.7rem; border-top:1px solid var(--tm-line,#dfe3ea); font-size:.76rem; line-height:1.5; color:var(--tm-muted,#6b7785); }
.lh-row { display:flex; flex-wrap:wrap; gap:.45rem .5rem; }
.lh { position:relative; display:inline-flex; align-items:center; gap:.35rem; border:1px solid var(--tm-line,#dfe3ea); border-radius:99px; padding:.2rem .65rem; font-size:.82rem; cursor:help; color:var(--tm-ink,#1d3557); }
.lh b { display:inline-flex; width:1.05rem; height:1.05rem; border-radius:50%; background:rgba(128,128,128,.22); align-items:center; justify-content:center; font-size:.7rem; }
.lh .tip { visibility:hidden; opacity:0; transition:opacity .15s; position:absolute; bottom:calc(100% + .5rem); left:0; z-index:50; width:21rem; max-width:80vw; background:#1e222d; color:#e6e9ef; border-radius:10px; padding:.7rem .85rem; font-size:.82rem; line-height:1.45; box-shadow:0 6px 24px rgba(0,0,0,.35); text-align:left; }
.lh .tip b { display:inline; width:auto; height:auto; background:none; font-size:.85rem; color:#fff; }
.lh:hover .tip { visibility:visible; opacity:1; }
.lh:nth-child(n+8) .tip { left:auto; right:0; }
.pb-main.four { grid-template-columns:1fr 1fr 1fr 1.7fr; }
@media (max-width:1100px){ .sc-row { grid-template-columns:repeat(2,1fr); } .pb-main { grid-template-columns:1fr; } }
.pb { position:relative; overflow:hidden; }
.pb::before { content:""; position:absolute; left:0; right:0; top:0; height:3px; background:linear-gradient(90deg,#26a69a,#2962ff 55%,#ef5350); }
.pb-head { padding-bottom:.8rem; border-bottom:1px dashed var(--tm-line,#dfe3ea); background-image:radial-gradient(rgba(128,128,128,.16) 1px, transparent 1px); background-size:14px 14px; margin:-.3rem -1.6rem .9rem -1.6rem; padding:.7rem 1.6rem .8rem 1.6rem; }
.pb-right { display:flex; align-items:center; gap:1rem; }
.mono, .pb-word, .pb-line, .pb-meterl, .pb-rng, .sc-v, .sc-t, .pb-verdict, .pb-sub, .pb-pill, .pb-l { font-family:ui-monospace,"SF Mono","JetBrains Mono",Menlo,Consolas,monospace; }
.pb-l { letter-spacing:.14em; font-size:.66rem; } .pb-l b { color:#2962ff; margin-right:.4rem; font-weight:700; }
.pb-box { background:linear-gradient(180deg,rgba(128,128,128,.06),rgba(128,128,128,.02)); }
.led-row { display:flex; gap:.5rem; margin-top:.75rem; } .led { width:.8rem; height:.8rem; border-radius:50%; display:inline-block; }
.pb-gauge { display:block; width:100%; max-width:11rem; margin:.1rem 0 -.2rem 0; }
.pb-gauge-n { font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace; font-size:1.55rem; font-weight:800; line-height:1; text-align:center; }
.pb-ml { text-align:center; }
.pb-ml .pb-l { text-align:left; } .pb-ml .pb-word { font-size:.95rem !important; font-weight:700; margin-top:.25rem; } .pb-ml .pb-meterl { text-align:center; }
.sc { background:linear-gradient(90deg,var(--sc-glow,transparent),transparent 40%); }
.sc-v { font-size:.74rem; } .sc-t { letter-spacing:.01em; }
.spark { display:block; }
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


def _tint(colour, alpha=0.12):
    r, g, b = int(colour[1:3], 16), int(colour[3:5], 16), int(colour[5:7], 16)
    return f"rgba({r},{g},{b},{alpha})"


def strategy_tiles(entries, stats=None):
    """One tile per CMT strategy: a coloured edge and vote word, its name and source, what it sees, and how it fared in testing.
    Hover a tile for the longer explanation."""
    tiles = []
    for en in entries:
        avail = en.get("available", True)
        name = VOTE_NAME[en["vote"]]
        colour = COLOUR[name] if avail else FLAT_C
        word = "n/a" if not avail else (f"{GLYPH[name]} " + ("Neutral" if name == "Sideways" else name))
        tested, tip = "", en["why"]
        rec = (stats or {}).get("strategies", {}).get(en["name"])
        if rec:
            d1 = rec["next day"]["last 30% of dates"]["accuracy"] * 100
            d20 = rec["next 20 days"]["last 30% of dates"]["accuracy"] * 100
            tested = f'<div class="sc-t">Back-test: {d1:.0f}% next day &middot; {d20:.0f}% in 20 days</div>'
            tip += f" Back-tested on past data: right {d1:.0f}% of the time for the next day and {d20:.0f}% over the next 20 days."
        tiles.append(f'<div class="sc" style="border-left-color:{colour};--sc-glow:{_tint(colour, .10)}" title="{e(tip)}"><div class="sc-top"><span class="sc-n">{e(en["name"])}</span>'
                     f'<span class="sc-v" style="color:{colour}">{word}</span></div><div class="sc-src">{e(en.get("source", ""))}</div>'
                     f'<div class="sc-r">{e(en["reading"])}</div>{tested}</div>')
    return '<div class="sc-head">The five strategies behind the call (hover a tile to read why)</div><div class="sc-row">' + "".join(tiles) + "</div>"


def _arc(cx, cy, r, p0, p1):
    """An SVG arc along the top half of a circle from fraction p0 to p1 of the way round (0 = far left, 1 = far right)."""
    import math
    a0, a1 = math.pi * (1 - p0), math.pi * (1 - p1)
    x0, y0, x1, y1 = cx + r * math.cos(a0), cy - r * math.sin(a0), cx + r * math.cos(a1), cy - r * math.sin(a1)
    return f"M {x0:.2f} {y0:.2f} A {r} {r} 0 0 1 {x1:.2f} {y1:.2f}"


def gauge_svg(p_up, colour):
    """A semicircle dial: red below 46%, grey between 46% and 54%, green above 54%, with a needle at the model's chance of 'up'."""
    import math
    cx, cy, r = 50, 50, 38
    ang = math.pi * (1 - min(max(p_up, 0.0), 1.0))
    nx, ny = cx + (r - 6) * math.cos(ang), cy - (r - 6) * math.sin(ang)
    seg = lambda p0, p1, c: f'<path d="{_arc(cx, cy, r, p0, p1)}" stroke="{c}" stroke-width="7" fill="none"/>'
    return (f'<svg class="pb-gauge" viewBox="0 0 100 58" aria-hidden="true">{seg(0.0, 0.46, DOWN_C)}{seg(0.46, 0.54, "#868993")}{seg(0.54, 1.0, UP_C)}'
            f'<line x1="{cx}" y1="{cy}" x2="{nx:.2f}" y2="{ny:.2f}" stroke="{colour}" stroke-width="2.2" stroke-linecap="round"/>'
            f'<circle cx="{cx}" cy="{cy}" r="3.4" fill="{colour}"/></svg>')


def spark_svg(values, colour, width=150, height=34):
    """A tiny price line for the header, with a dot on the last price."""
    vals = [float(v) for v in values]
    if len(vals) < 3:
        return ""
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1.0
    pts = [(i / (len(vals) - 1) * (width - 6) + 3, height - 4 - (v - lo) / span * (height - 8)) for i, v in enumerate(vals)]
    path = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return (f'<svg class="spark" width="{width}" height="{height}" viewBox="0 0 {width} {height}" aria-hidden="true">'
            f'<polyline points="{path}" fill="none" stroke="{colour}" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round" opacity=".9"/>'
            f'<circle cx="{pts[-1][0]:.1f}" cy="{pts[-1][1]:.1f}" r="3" fill="{colour}"/></svg>')


def prediction_bar(result, status_text="", footer="", strategies="", note="", ml=None, learn="", spark=None):
    """The prediction panel, in a tech-console style: a header with a tiny price line and a live pill, four numbered boxes (the call
    with one LED per strategy, the ML dial, what happened, the expected range), the strategy tiles, the hint chips and the footer."""
    p = result["prediction"]
    voters = [v for v in result["votes"] if v["voting"]]
    ups = sum(1 for v in voters if v["vote"] > 0)
    downs = sum(1 for v in voters if v["vote"] < 0)
    neutral = len(voters) - ups - downs
    colour = COLOUR[p]
    leds = "".join(f'<i class="led" title="{e(v["name"])}: {VOTE_NAME[v["vote"]]}" style="background:{COLOUR[VOTE_NAME[v["vote"]]]};'
                   f'box-shadow:0 0 7px {COLOUR[VOTE_NAME[v["vote"]]]}"></i>' for v in voters)
    call = (f'<div class="pb-box"><div class="pb-l"><b>01</b>THE CALL</div><div class="pb-big"><div class="pb-badge" style="background:{_tint(colour, .16)};color:{colour}">{GLYPH[p]}</div>'
            f'<div><div class="pb-word" style="color:{colour}">{p.upper()}</div></div></div><div class="led-row">{leds}</div>'
            f'<div class="pb-meterl">{ups} up &middot; {downs} down &middot; {neutral} neutral</div></div>')
    ml_html = ""
    if ml:
        lean = ml["lean"]
        mcol = COLOUR.get(lean, FLAT_C)
        word = {"Up": "LEANS UP", "Down": "LEANS DOWN", "None": "NO CLEAR VIEW"}[lean]
        held = ml["tested"].get("last 30% of dates (held back)", {})
        conf = held.get("confident_accuracy")
        drivers = ", ".join(f"{n} ({'up' if v > 0 else 'down'})" for n, v in ml["top"])
        tested = (f'held-back test: {held["accuracy"] * 100:.0f}% overall, {conf * 100:.0f}% when confident' if conf else "")
        ml_html = (f'<div class="pb-box pb-ml" title="Biggest influences today: {e(drivers)}.">'
                   f'<div class="pb-l"><b>02</b>ML ESTIMATE</div>{gauge_svg(ml["p_up"], mcol)}'
                   f'<div class="pb-gauge-n" style="color:{mcol}">{ml["p_up"] * 100:.1f}%</div>'
                   f'<div class="pb-word" style="color:{mcol}">{word}</div><div class="pb-meterl">chance of closing higher<br>{e(tested)}</div></div>')
    n_what, n_rng = ("03", "04") if ml else ("02", "03")
    low, high = result["range"]
    if result["actual"] is None:
        what = (f'<div class="pb-box"><div class="pb-l"><b>{n_what}</b>OUTCOME</div><div class="pb-big"><div class="pb-badge" style="background:rgba(128,128,128,.12);color:#868993">&hellip;</div>'
                '<div><div class="pb-word" style="color:#868993">NOT YET</div></div></div><div class="pb-line">waiting for today\'s price</div></div>')
        rng = (f'<div class="pb-box"><div class="pb-l"><b>{n_rng}</b>EXPECTED RANGE</div><div class="pb-rng"><span>Rs {low:,.0f}</span><span>Rs {high:,.0f}</span></div>'
               f'{range_bar(low, high, result["prev_close"], None, ends=False)}</div>')
    else:
        a = result["actual_direction"]
        ac = COLOUR[a]
        ok = result["matched"]
        vc = UP_C if ok else DOWN_C
        what = (f'<div class="pb-box"><div class="pb-l"><b>{n_what}</b>OUTCOME</div><div class="pb-big"><div class="pb-badge" style="background:{_tint(ac, .16)};color:{ac}">{GLYPH[a]}</div>'
                f'<div><div class="pb-word" style="color:{ac}">{a.upper()}</div></div></div>'
                f'<div class="pb-line">{result["change"] * 100:+.2f}% &middot; Rs {result["actual"]:,.2f}</div>'
                f'<span class="pb-verdict" style="background:{_tint(vc, .14)};color:{vc}">{"&#10003; CALL RIGHT" if ok else "&#10007; CALL WRONG"}</span></div>')
        inside = "inside" if result["in_range"] else "outside"
        rng = (f'<div class="pb-box"><div class="pb-l"><b>{n_rng}</b>EXPECTED RANGE &middot; {inside}</div><div class="pb-rng"><span>Rs {low:,.0f}</span><span>Rs {high:,.0f}</span></div>'
               f'{range_bar(low, high, result["prev_close"], result["actual"], "Now" if result["status"] == "live" else "Close", ends=False)}</div>')
    live = "live" in status_text.lower()
    pill = f'<span class="pb-pill{" live" if live else ""}"><i></i>{e(status_text.upper())}</span>' if status_text else ""
    sk = spark_svg(spark, colour) if spark is not None and len(spark) else ""
    head = (f'<div class="pb-head"><div><div class="pb-title">Today\'s prediction</div><div class="pb-sub">data to {result["basis_date"]:%a %d %b} &middot; close Rs {result["prev_close"]:,.2f}</div></div>'
            f'<div class="pb-right">{sk}{pill}</div></div>')
    note_html = f'<div class="pb-note">{note}</div>' if note else ""
    foot = f'<div class="pb-foot">{footer}</div>' if footer else ""
    return f'<div class="pb">{head}<div class="pb-main{" four" if ml_html else ""}">{call}{ml_html}{what}{rng}</div>{strategies}{learn}{note_html}{foot}</div>'


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
