"""Building blocks for the presenter's guide (scripts/make_presenter_guide.py): the page design and the small diagrams."""
import math
import re


def _bigger(svg, k=1.3):
    """Scale every font-size inside a drawing, so the labels stay readable when the drawing is shown small."""
    return re.sub(r'font-size="([\d.]+)"', lambda m: f'font-size="{float(m.group(1)) * k:.1f}"', svg)

NAVY, BLUE, GREEN, RED, AMBER, GREY = "#1d3557", "#3f74e6", "#26a69a", "#ef5350", "#d98e04", "#8a93a3"

CSS = """
@page { size: A4; margin: 0; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: #e9edf3; }
body { font-family: "Avenir Next", "Helvetica Neue", Helvetica, Arial, sans-serif; color: #1b2430; font-size: 12.3px; line-height: 1.46; }
#src { display: none; }
#guide-report { display: none; }
.page { width: 210mm; height: 297mm; padding: 11mm 13mm 0 13mm; background: #fff; margin: 0 auto 10px auto; position: relative; overflow: hidden;
        page-break-after: always; break-after: page; display: flex; flex-direction: column; }
@media print { html, body { background: #fff; } .page { margin: 0; } }
.page:last-of-type { page-break-after: auto; break-after: auto; }
.page .body { flex: 1 1 auto; overflow: hidden; padding-bottom: 3px; }
.head { flex: none; display: flex; justify-content: space-between; align-items: baseline; border-bottom: 2px solid #1d3557; padding-bottom: 5px; margin-bottom: 11px; }
.head .part { font-size: 9.7px; letter-spacing: .12em; text-transform: uppercase; color: #3f74e6; font-weight: 700; }
.head .site { font-size: 9.7px; color: #8a93a3; }
.foot { flex: none; display: flex; justify-content: space-between; align-items: center; font-size: 9.3px; color: #8a93a3; border-top: 1px solid #dfe3ea; height: 11mm; margin-top: 0; }
h1 { font-size: 24.2px; line-height: 1.15; margin: 0 0 5px 0; color: #1d3557; }
h2 { font-size: 17.7px; margin: 6px 0 4px 0; color: #1d3557; }
h3 { font-size: 14.0px; margin: 0 0 5px 0; color: #1d3557; }
p { margin: 0 0 6px 0; }
.lead { font-size: 13.2px; color: #3a4658; margin-bottom: 10px; }
.topic { border: 1px solid #dfe3ea; border-radius: 10px; padding: 7px 10px 7px 10px; margin-bottom: 9px; }
.topic h3 { display: flex; align-items: center; gap: 7px; }
.topic h3 .num { background: #1d3557; color: #fff; border-radius: 50%; width: 20px; height: 20px; font-size: 10.7px; display: inline-flex; align-items: center; justify-content: center; flex: none; }
.two { display: grid; grid-template-columns: 1fr 1fr; gap: 9px; }
.simple, .fin { border-radius: 8px; padding: 6px 9px 3px 9px; }
.simple { background: #eef5ff; border-left: 4px solid #3f74e6; }
.fin { background: #f4f5f8; border-left: 4px solid #1d3557; }
.chip { display: inline-block; font-size: 8.6px; font-weight: 800; letter-spacing: .09em; text-transform: uppercase; border-radius: 10px; padding: 1px 8px; margin-bottom: 4px; color: #fff; }
.chip.s { background: #3f74e6; } .chip.f { background: #1d3557; } .chip.a { background: #26a69a; }
.screen { margin-top: 6px; background: #eaf7f4; border-left: 4px solid #26a69a; border-radius: 8px; padding: 5px 9px 2px 9px; }
.screen p { margin-bottom: 3px; }
.note { background: #fff7e6; border-left: 4px solid #d98e04; border-radius: 8px; padding: 6px 10px 3px 10px; margin: 7px 0 9px 0; }
.note b.t { color: #9a6200; }
.tight .topic { margin-bottom: 7px; padding: 6px 9px; }
.cols { display: grid; grid-template-columns: 1fr 1fr; gap: 9px; margin-bottom: 0; }
.cols .two, .cols3 .two { grid-template-columns: 1fr; }
.cols3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 9px; }
.cols > .topic, .cols3 > .topic { margin-bottom: 9px; }
table { border-collapse: collapse; width: 100%; font-size: 11.0px; margin-bottom: 9px; }
th { background: #1d3557; color: #fff; text-align: left; padding: 4px 7px; font-weight: 700; }
td { border-bottom: 1px solid #dfe3ea; padding: 4px 7px; vertical-align: top; }
tr:nth-child(even) td { background: #f7f8fb; }
.up { color: #158a7e; font-weight: 700; } .down { color: #d6453d; font-weight: 700; } .flat { color: #6b7785; font-weight: 700; }
.gauge { position: relative; height: 11px; border-radius: 6px; background: linear-gradient(90deg, #ef5350 0%, #f4b04f 50%, #26a69a 100%); margin: 6px 0 3px 0; }
.gauge .ptr { position: absolute; top: -4px; width: 5px; height: 19px; background: #1b2430; border-radius: 3px; }
.gauge-ends { display: flex; justify-content: space-between; font-size: 9.7px; color: #6b7785; }
.big { font-size: 42.8px; font-weight: 800; color: #1d3557; line-height: 1.05; letter-spacing: -.01em; }
.kicker { font-size: 10.7px; letter-spacing: .18em; text-transform: uppercase; color: #3f74e6; font-weight: 800; }
.qa { border-bottom: 1px solid #e3e7ee; padding: 4px 0 4px 0; break-inside: avoid; }
.qa b { color: #1d3557; }
.gl { columns: 2; column-gap: 16px; font-size: 11.0px; }
.gl div { break-inside: avoid; margin-bottom: 4px; }
.gl b { color: #1d3557; }
.say { background: #1d3557; color: #fff; border-radius: 10px; padding: 9px 13px; font-size: 12.5px; margin-bottom: 10px; }
.say i { color: #cfe0ff; }
.small { font-size: 10.2px; color: #6b7785; }
ul, ol { margin: 3px 0 5px 18px; padding: 0; } li { margin-bottom: 3px; }
svg text { font-family: "Avenir Next", "Helvetica Neue", Helvetica, Arial, sans-serif; }
"""


def gauge(pos, left, right):
    return (f'<div class="gauge"><div class="ptr" style="left:{pos}%"></div></div>'
            f'<div class="gauge-ends"><span>{left}</span><span>{right}</span></div>')


def candle_svg():
    def candle(x, up):
        col = GREEN if up else RED
        top, bot = 50, 112
        label_t = ("Close" if up else "Open", "Open" if up else "Close")
        return (f'<line x1="{x}" y1="18" x2="{x}" y2="150" stroke="{col}" stroke-width="3"/>'
                f'<rect x="{x - 16}" y="{top}" width="32" height="{bot - top}" rx="3" fill="{col}"/>'
                f'<text x="{x + 24}" y="{top + 4}" font-size="9.5" fill="#1b2430">{label_t[0]} price</text>'
                f'<text x="{x + 24}" y="{bot + 4}" font-size="9.5" fill="#1b2430">{label_t[1]} price</text>'
                f'<text x="{x + 8}" y="16" font-size="9.5" fill="#1b2430">Highest price of the day</text>'
                f'<text x="{x + 8}" y="162" font-size="9.5" fill="#1b2430">Lowest price of the day</text>')
    return ('<svg viewBox="0 0 380 172" width="100%" role="img" aria-label="Two candlesticks">'
            + candle(60, True) + candle(250, False)
            + f'<text x="60" y="176" font-size="0"> </text></svg>')


def barometer_svg(score, n=5):
    cx, cy, r = 70, 66, 52
    pos = (score + n) / (2 * n)
    bands = ["#ef5350", "#f4958f", "#c4c9d2", "#85cfc6", "#26a69a"]

    def arc(p0, p1):
        a0, a1 = math.pi * (1 - p0), math.pi * (1 - p1)
        x0, y0, x1, y1 = cx + r * math.cos(a0), cy - r * math.sin(a0), cx + r * math.cos(a1), cy - r * math.sin(a1)
        return f"M {x0:.1f} {y0:.1f} A {r} {r} 0 0 1 {x1:.1f} {y1:.1f}"
    segs = "".join(f'<path d="{arc(i / 5 + 0.006, (i + 1) / 5 - 0.006)}" stroke="{c}" stroke-width="12" fill="none"/>' for i, c in enumerate(bands))
    ang = math.pi * (1 - pos)
    nx, ny = cx + (r - 10) * math.cos(ang), cy - (r - 10) * math.sin(ang)
    return (f'<svg viewBox="0 0 140 84" width="150" role="img" aria-label="Barometer">{segs}'
            f'<line x1="{cx}" y1="{cy}" x2="{nx:.1f}" y2="{ny:.1f}" stroke="#1b2430" stroke-width="3" stroke-linecap="round"/>'
            f'<circle cx="{cx}" cy="{cy}" r="5" fill="#1b2430"/>'
            f'<text x="6" y="82" font-size="8" fill="#6b7785">Down</text><text x="57" y="82" font-size="8" fill="#6b7785">Neutral</text>'
            f'<text x="116" y="82" font-size="8" fill="#6b7785">Up</text></svg>')


def zigzag_svg(up=True):
    pts_up = [(10, 120), (45, 70), (75, 95), (115, 45), (145, 72), (185, 20)]
    pts = pts_up if up else [(x, 140 - y) for x, y in pts_up]
    col = GREEN if up else RED
    path = " ".join(f"{x},{y}" for x, y in pts)
    marks = ""
    for i, (x, y) in enumerate(pts):
        is_high = (i % 2 == 1) if up else (i % 2 == 0)
        marks += f'<circle cx="{x}" cy="{y}" r="3.6" fill="{"#1d3557" if is_high else "#d98e04"}"/>'
    return (f'<svg viewBox="0 0 200 150" width="100%" role="img" aria-label="{"Higher highs and higher lows" if up else "Lower highs and lower lows"}">'
            f'<polyline points="{path}" fill="none" stroke="{col}" stroke-width="2.4"/>{marks}'
            f'<text x="4" y="146" font-size="8.5" fill="#6b7785">dark dot = a peak, amber dot = a dip</text></svg>')


def chart_anatomy_svg():
    n = 90
    xs = [8 + i * 3.9 for i in range(n)]
    base = [60 - i * 0.12 + 13 * math.sin(i / 7.0) + 3.5 * math.sin(i / 2.3) for i in range(n)]
    ma50 = [sum(base[max(0, i - 12):i + 1]) / len(base[max(0, i - 12):i + 1]) for i in range(n)]
    ma200 = [sum(base[max(0, i - 40):i + 1]) / len(base[max(0, i - 40):i + 1]) for i in range(n)]
    upper = [m + 11 for m in ma50]
    lower = [m - 11 for m in ma50]
    line = lambda ys, col, w: f'<polyline fill="none" stroke="{col}" stroke-width="{w}" points="' + " ".join(f"{x:.1f},{y + 14:.1f}" for x, y in zip(xs, ys)) + '"/>'
    band = ('<polygon fill="#e3e6ec" points="' + " ".join(f"{x:.1f},{y + 14:.1f}" for x, y in zip(xs, upper))
            + " " + " ".join(f"{x:.1f},{y + 14:.1f}" for x, y in reversed(list(zip(xs, lower)))) + '"/>')
    vols = "".join(f'<rect x="{x - 1.2:.1f}" y="{138 - v:.1f}" width="2.6" height="{v:.1f}" fill="{GREEN if i % 3 else RED}" opacity=".75"/>'
                   for i, (x, v) in enumerate(zip(xs, [6 + 9 * abs(math.sin(i * 1.7)) for i in range(n)])))
    legend = [("#1b2430", "The price (each point is one day)"), (AMBER, "50-day average, the recent mood"), (NAVY, "200-day average, the long-term mood"),
              ("#d5d9e1", "Grey band: the price's usual range"), (GREEN, "Volume bars: green = price rose that day, red = it fell")]
    leg = "".join(f'<rect x="8" y="{154 + i * 14}" width="14" height="6" rx="2" fill="{c}"/><text x="28" y="{160 + i * 14}" font-size="9" fill="#1b2430">{t}</text>'
                  for i, (c, t) in enumerate(legend))
    return (f'<svg viewBox="0 0 360 230" width="100%" role="img" aria-label="A price chart with its tools">{band}'
            + line(ma200, NAVY, 2) + line(ma50, AMBER, 1.8) + line(base, "#1b2430", 1.2) + vols + leg + '</svg>')


def fib_svg():
    levels = [(0, "0% top"), (23.6, "23.6%"), (38.2, "38.2%"), (50, "50%"), (61.8, "61.8%"), (78.6, "78.6%"), (100, "100% bottom")]
    top, bot = 20, 160
    lines = ""
    for pct, name in levels:
        y = top + (bot - top) * pct / 100
        heavy = pct in (38.2, 50, 61.8)
        lines += (f'<line x1="70" y1="{y:.1f}" x2="250" y2="{y:.1f}" stroke="{AMBER if heavy else "#b8c0cc"}" stroke-width="{1.6 if heavy else 1}" stroke-dasharray="{"" if heavy else "3 3"}"/>'
                  f'<text x="256" y="{y + 3:.1f}" font-size="8.5" fill="{"#9a6200" if heavy else "#6b7785"}">{name}</text>')
    path = f'<polyline points="20,175 40,150 55,160 75,100 90,115 110,20 130,45 150,70 165,60 185,92 205,84" fill="none" stroke="{NAVY}" stroke-width="2.2"/>'
    return (f'<svg viewBox="0 0 360 185" width="100%" role="img" aria-label="Fibonacci levels after a rise">{lines}{path}'
            f'<text x="8" y="12" font-size="8.5" fill="#6b7785">A rise, then a pullback that pauses near a level</text></svg>')


def screen_map_svg():
    def box(x, y, w, h, fill="#fff", stroke="#c9d1dd", rx=5):
        return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}"/>'

    def num(x, y, n):
        return (f'<circle cx="{x}" cy="{y}" r="8.5" fill="{NAVY}"/><text x="{x}" y="{y + 3.4}" font-size="9.5" font-weight="700" fill="#fff" text-anchor="middle">{n}</text>')
    s = ['<svg viewBox="0 0 700 472" width="100%" role="img" aria-label="Map of the dashboard">',
         '<defs><linearGradient id="g"><stop offset="0" stop-color="#ef5350"/><stop offset=".5" stop-color="#f4b04f"/><stop offset="1" stop-color="#26a69a"/></linearGradient></defs>',
         box(0, 0, 700, 472, "#f6f8fb", "#dfe3ea", 8),
         box(8, 8, 684, 38, "#fff"),
         '<text x="40" y="31" font-size="11" font-weight="700" fill="#1d3557">Site name</text>',
         '<text x="214" y="31" font-size="10.5" fill="#1d3557">Portfolio value  Rs 1,00,000</text>',
         '<text x="410" y="31" font-size="9.5" fill="#6b7785">Dark  ·  Dashboard view</text>',
         box(588, 15, 44, 22, "#fff"), '<text x="610" y="30" font-size="9.5" text-anchor="middle" fill="#1d3557">Tour</text>',
         '<circle cx="678" cy="26" r="11" fill="#fff" stroke="#1d3557"/><text x="678" y="30" font-size="11" font-style="italic" font-weight="700" text-anchor="middle" fill="#1d3557">i</text>',
         box(8, 56, 150, 74), '<text x="18" y="72" font-size="8" font-weight="700" fill="#6b7785">WHAT YOU HOLD</text>',
         box(8, 136, 150, 84), '<text x="18" y="152" font-size="8" font-weight="700" fill="#6b7785">YOUR MONEY</text>',
         '<circle cx="83" cy="192" r="20" fill="none" stroke="#b8c0cc" stroke-width="9"/>',
         box(8, 226, 150, 74), '<text x="18" y="242" font-size="8" font-weight="700" fill="#6b7785">LEADERBOARD</text>',
         box(8, 306, 150, 76), '<text x="18" y="322" font-size="8" font-weight="700" fill="#6b7785">COMBINED READING</text>',
         '<path d="M 42 368 A 38 38 0 0 1 124 368" fill="none" stroke="#c4c9d2" stroke-width="9"/>',
         box(166, 56, 350, 26, "#eef1f6"), '<text x="178" y="73" font-size="9.5" fill="#6b7785">SEARCH STOCK</text>',
         '<text x="166" y="100" font-size="11" font-weight="700" fill="#1d3557">Company name   Rs 1,211.20   -0.31%</text>',
         box(166, 108, 350, 24, "#fff"), '<text x="176" y="124" font-size="8.5" fill="#6b7785">1  2  4  |  Day  Week  Month  |  6M  1Y  2Y  5Y  |  Fibonacci  |  Dark</text>',
         box(166, 138, 350, 168),
         '<polyline fill="none" stroke="#1b2430" stroke-width="1.3" points="176,250 210,230 240,262 280,200 310,222 350,170 390,205 430,180 470,230 505,215"/>',
         '<polyline fill="none" stroke="#d98e04" stroke-width="1.6" points="176,245 240,240 310,225 390,200 470,215 505,222"/>',
         '<polyline fill="none" stroke="#1d3557" stroke-width="1.8" points="176,230 310,224 505,226"/>',
         box(166, 312, 350, 70), '<text x="196" y="332" font-size="8" font-weight="700" fill="#6b7785">BUTTONS FOR PAPER TRADING</text>',
         f'<rect x="338" y="338" width="52" height="24" rx="5" fill="{NAVY}"/><text x="364" y="354" font-size="10" text-anchor="middle" fill="#fff">Buy</text>',
         box(398, 338, 52, 24, "#fff"), '<text x="424" y="354" font-size="10" text-anchor="middle" fill="#8a93a3">Sell</text>',
         box(458, 338, 52, 24, "#fff"), '<text x="484" y="354" font-size="10" text-anchor="middle" fill="#8a93a3">Exit all</text>',
         box(524, 56, 168, 326), '<text x="534" y="72" font-size="8" font-weight="700" fill="#6b7785">INDICATORS</text>']
    for i in range(6):
        y = 82 + i * 49
        s.append(box(532, y, 152, 42, "#fff"))
        s.append(f'<rect x="540" y="{y + 22}" width="136" height="6" rx="3" fill="url(#g)"/>')
    s += [box(8, 392, 684, 70), '<text x="40" y="410" font-size="9.5" font-weight="700" fill="#1d3557">The strategies behind the reading</text>',
          '<text x="40" y="428" font-size="8.5" fill="#6b7785">Strategy   |   Vote   |   What it sees   |   Back-test on this company   |   Full view</text>',
          '<text x="40" y="444" font-size="8.5" fill="#6b7785">Fusion stage, Dow Theory, Relative strength, Wyckoff, Fibonacci, ML model</text>',
          '<circle cx="662" cy="434" r="17" fill="#3f74e6" stroke="#b9ccf6" stroke-width="4"/>',
          '<circle cx="655" cy="434" r="2.3" fill="#fff"/><circle cx="662" cy="434" r="2.3" fill="#fff"/><circle cx="669" cy="434" r="2.3" fill="#fff"/>']
    s += [num(22, 27, 1), num(200, 27, 2), num(402, 27, 3), num(574, 27, 4), num(652, 26, 5),
          num(144, 70, 6), num(144, 150, 7), num(144, 240, 8), num(144, 320, 9),
          num(500, 69, 10), num(500, 120, 11), num(500, 152, 12), num(182, 326, 13),
          num(676, 70, 14), num(22, 404, 15), num(636, 420, 16)]
    s.append("</svg>")
    return "".join(s)


def _wrap(fn, k):
    def inner(*args, **kwargs):
        return _bigger(fn(*args, **kwargs), k)
    return inner


# the drawings are shown smaller than their own size, so their labels are scaled up to stay readable
candle_svg = _wrap(candle_svg, 1.45)
chart_anatomy_svg = _wrap(chart_anatomy_svg, 1.5)
fib_svg = _wrap(fib_svg, 1.3)
barometer_svg = _wrap(barometer_svg, 1.45)
zigzag_svg = _wrap(zigzag_svg, 1.0)
screen_map_svg = _wrap(screen_map_svg, 1.22)
