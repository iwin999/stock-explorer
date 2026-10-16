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
.pb { background:var(--tm-panel,#fff); border:1px solid var(--tm-line,#dfe3ea); border-radius:12px; padding:.8rem 1.5rem .7rem 1.5rem; box-shadow:0 1px 3px rgba(16,24,40,.07); }
.pb-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:.35rem; }
.pb-title { font-size:.72rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:var(--tm-muted,#6b7785); }
.pb-status { font-size:.78rem; color:var(--tm-muted,#6b7785); }
.pb-foot { margin-top:.9rem; padding-top:.8rem; border-top:1px solid var(--tm-line,#dfe3ea); font-size:.8rem; line-height:1.5; color:var(--tm-muted,#6b7785); }
.sc-row { display:grid; grid-template-columns:repeat(5,1fr); gap:.7rem; margin-top:.9rem; padding-top:.8rem; border-top:1px solid var(--tm-line,#dfe3ea); }
.sc { border:1px solid var(--tm-line,#dfe3ea); border-radius:10px; padding:.55rem .75rem .5rem .75rem; min-width:0; }
.sc-h { display:flex; justify-content:space-between; align-items:center; gap:.4rem; } .sc-n { font-weight:700; font-size:.92rem; line-height:1.15; }
.sc-chip { font-size:.72rem !important; padding:.08rem .55rem !important; }
.sc-src { font-size:.68rem; letter-spacing:.06em; text-transform:uppercase; color:var(--tm-muted,#6b7785); margin:.1rem 0 .3rem 0; }
.sc-r { font-size:.86rem; font-weight:600; line-height:1.25; } .sc-w { font-size:.78rem; color:var(--tm-muted,#6b7785); line-height:1.3; margin-top:.2rem; }
.sc-t { font-size:.72rem; color:var(--tm-muted,#6b7785); margin-top:.35rem; padding-top:.3rem; border-top:1px dashed var(--tm-line,#dfe3ea); }
.pb-note { margin-top:.7rem; font-size:.8rem; line-height:1.45; color:var(--tm-muted,#6b7785); }
@media (max-width:1100px){ .sc-row { grid-template-columns:repeat(2,1fr); } }
.pb-row { display:grid; grid-template-columns:1fr 1fr .9fr 2.4fr; align-items:center; }
.pb-cell { padding:0 1.6rem; border-left:1px solid var(--tm-line,#dfe3ea); line-height:1.2; min-width:0; }
.pb-cell:first-child { padding-left:0; border-left:0; }
.pb-l { font-size:.68rem; letter-spacing:.08em; text-transform:uppercase; color:var(--tm-muted,#6b7785); margin-bottom:.15rem; }
.pb-v { font-size:1.55rem; font-weight:700; white-space:nowrap; } .pb-g { font-size:.95rem; margin-right:.2rem; }
.pb-s { font-size:.88rem; color:var(--tm-muted,#6b7785); margin-top:.1rem; white-space:nowrap; }
.pb-dots { display:flex; gap:.25rem; margin-top:.25rem; } .pb-dots .dc-dot { width:.7rem; height:.7rem; }
.pb-chip { display:inline-block; white-space:nowrap; color:#fff; font-weight:700; font-size:1.05rem; padding:.2rem .8rem; border-radius:99px; }
.pb .dc-range { margin:.9rem .2rem 1.35rem .2rem; height:2rem; }
@media (max-width:900px){ .pb-row { grid-template-columns:1fr 1fr; row-gap:.6rem; } }
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


def range_bar(low, high, prev_close, price, price_label="Now"):
    """A horizontal bar: the expected range (blue band), yesterday's close (tick) and today's price (round pin)."""
    lo = min(low, price if price else low) * 0.998
    hi = max(high, price if price else high) * 1.002
    span = (hi - lo) or 1.0
    at = lambda x: f"{(x - lo) / span * 100:.1f}%"
    pin = ""
    if price:
        inside = low <= price <= high
        crowded = abs((price - prev_close) / span) < 0.14             # keep the two labels apart when the prices are close
        pin = (f'<div class="dc-pin" style="left:{at(price)};background:{UP_C if inside else DOWN_C}"></div>'
               f'<div class="dc-lbl{"" if crowded else " b"}" style="left:{at(price)};{"top:-1.15rem;" if crowded else ""}">{e(price_label)} {price:,.2f}</div>')
    return (f'<div class="dc-range"><div class="dc-track"></div>'
            f'<div class="dc-band" style="left:{at(low)};width:{(high - low) / span * 100:.1f}%"></div>'
            f'<div class="dc-tick" style="left:{at(prev_close)}"></div>'
            f'<div class="dc-lbl" style="left:{at(low)}">{low:,.0f}</div><div class="dc-lbl" style="left:{at(high)}">{high:,.0f}</div>'
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
    "RSI (speed)": "A score from 0 to 100 of how fast the price has been rising or falling. Above 70 it has run up quickly; below 30 it has fallen quickly. Shown for context; it does not vote.",
    "MACD (momentum)": "Compares a quick and a slow average of the price. Above its signal line the momentum is rising; below it, fading. Shown for context; it does not vote.",
    "Trend strength (ADX)": "How strong a trend is, whichever way it points. Above 20 is a real trend. The pointer shows whether buyers or sellers are in the lead. Shown for context; it does not vote.",
    "Supertrend": "A line that trails the price and flips when the trend reverses. Price above the line is an uptrend, below it a downtrend. Shown for context; it does not vote.",
    "Ichimoku cloud": "A shaded zone built from past highs and lows that acts as support and resistance. Price above the cloud is bullish, below it bearish. Shown for context; it does not vote.",
    "Volume": "Today's trading activity compared with the usual level. Busy trading makes a move more believable. Shown for context; it does not vote.",
}


def terminal_card(entry):
    """A compact indicator card for the Terminal view's right panel. Hover it for the description."""
    name = VOTE_NAME[entry["vote"]]
    word = ("Neutral" if name == "Sideways" else name) if entry["voting"] else entry["reading"]
    tip = EXPLAIN.get(entry["name"], entry["why"])
    badge = "VOTES" if entry["voting"] else "context"
    return (f'<div class="dc-card tm{"" if entry["voting"] else " ctx"}" title="{e(tip)}">'
            f'<div class="dc-name"><span>{e(entry["name"])} <small style="opacity:.55;font-weight:500">{badge} &#9432;</small></span>'
            f'<span class="dc-chip" style="background:{COLOUR[name]}">{GLYPH[name]} {e(word)}</span></div>'
            f'{scale_html(entry["gauge"])}</div>')


def strategy_tiles(entries, stats=None):
    """One tile per CMT strategy: its name and source, its vote, what it sees, and how it fared in testing."""
    tiles = []
    for en in entries:
        name = VOTE_NAME[en["vote"]]
        word = "n/a" if not en.get("available", True) else ("Neutral" if name == "Sideways" else name)
        colour = FLAT_C if not en.get("available", True) else COLOUR[name]
        tested = ""
        rec = (stats or {}).get("strategies", {}).get(en["name"])
        if rec:
            d1 = rec["next day"]["last 30% of dates"]["accuracy"] * 100
            d20 = rec["next 20 days"]["last 30% of dates"]["accuracy"] * 100
            tested = f'<div class="sc-t">Tested: right {d1:.0f}% next day, {d20:.0f}% over 20 days</div>'
        tiles.append(f'<div class="sc"><div class="sc-h"><span class="sc-n">{e(en["name"])}</span>'
                     f'<span class="pb-chip sc-chip" style="background:{colour}">{GLYPH[name] if en.get("available", True) else ""} {word}</span></div>'
                     f'<div class="sc-src">{e(en.get("source", ""))}</div><div class="sc-r">{e(en["reading"])}</div>'
                     f'<div class="sc-w">{e(en["why"])}</div>{tested}</div>')
    return '<div class="sc-row">' + "".join(tiles) + "</div>"


def prediction_bar(result, status_text="", footer="", strategies="", note=""):
    """The prediction comparison as one tidy bar: THE CALL | WHAT HAPPENED | RESULT | EXPECTED RANGE, all on one line."""
    p = result["prediction"]
    voters = [v for v in result["votes"] if v["voting"]]
    ups = sum(1 for v in voters if v["vote"] > 0)
    downs = sum(1 for v in voters if v["vote"] < 0)
    dots = "".join(f'<span class="dc-dot" title="{e(v["name"])}: {VOTE_NAME[v["vote"]]}" style="background:{COLOUR[VOTE_NAME[v["vote"]]]}"></span>'
                   for v in voters)
    call = (f'<div class="pb-cell"><div class="pb-l">The call</div><div class="pb-v" style="color:{COLOUR[p]}"><span class="pb-g">{GLYPH[p]}</span>{p}</div>'
            f'<div class="pb-s">{ups} up &middot; {downs} down &middot; {len(voters) - ups - downs} neutral</div><div class="pb-dots">{dots}</div></div>')
    if result["actual"] is None:
        what = ('<div class="pb-cell"><div class="pb-l">What happened</div><div class="pb-v" style="color:#868993">Not yet</div>'
                '<div class="pb-s">Waiting for today\'s price</div></div>')
        outcome = '<div class="pb-cell"><div class="pb-l">Result</div><div class="pb-v" style="color:#868993">&ndash;</div></div>'
        low, high = result["range"]
        rng = (f'<div class="pb-cell"><div class="pb-l">Expected range</div>'
               f'{range_bar(low, high, result["prev_close"], None)}</div>')
    else:
        a = result["actual_direction"]
        what = (f'<div class="pb-cell"><div class="pb-l">What happened</div><div class="pb-v" style="color:{COLOUR[a]}"><span class="pb-g">{GLYPH[a]}</span>{a}</div>'
                f'<div class="pb-s">{result["change"] * 100:+.2f}% &middot; Rs {result["actual"]:,.2f}</div></div>')
        ok = result["matched"]
        outcome = (f'<div class="pb-cell"><div class="pb-l">Result</div><span class="pb-chip" style="background:{UP_C if ok else DOWN_C}">'
                   f'{"&#10003; Right" if ok else "&#10007; Wrong"}</span>'
                   f'<div class="pb-s">{"Inside" if result["in_range"] else "Outside"} the range</div></div>')
        low, high = result["range"]
        rng = (f'<div class="pb-cell"><div class="pb-l">Expected range</div>'
               f'{range_bar(low, high, result["prev_close"], result["actual"], "Now" if result["status"] == "live" else "Close")}</div>')
    head = f'<div class="pb-head"><span class="pb-title">Prediction comparison for today</span><span class="pb-status">{e(status_text)}</span></div>'
    foot = f'<div class="pb-foot">{footer}</div>' if footer else ""
    note_html = f'<div class="pb-note">{note}</div>' if note else ""
    return f'<div class="pb">{head}<div class="pb-row">{call}{what}{outcome}{rng}</div>{strategies}{note_html}{foot}</div>'
