"""The Dashboard (terminal) view of the SIMPLE site: the whole job on one screen, laid out like a trading terminal.

    top bar:  MCGS Stock Explorer                                    Portfolio value
    left   :  bought and sold list, allocation ring, refresh setting
    centre :  stock search, chart with analysis tools, Buy / Sell / Exit all, prediction comparison for today
    right  :  every indicator, with a hover description, shown relative to its value
"""
import streamlit as st

from core import about, company_search, companies
from core import cmt_strategies as cmt
from core import instruments as ins
from core import daily_check as dc
from core import daily_ui
from core import daily_visuals as vis
from core import ml_model
from core import price_panel
from core import tour
from core import trading_ui as tu
from core.charts import allocation_donut, show as show_chart
from core.errors import guard
from core.formatting import format_inr
from core.live import live_quote
from core.market_data import get_company_name, get_history_with_source
from core.market_hours import is_market_open, now_ist, status_message
from core.ui import DISCLAIMER, show_disclaimer

REFRESH = {"Off": None, "15 seconds": 15, "30 seconds": 30, "1 minute": 60}     # live prices are shared for 15 seconds at a time
PANEL_HEIGHT = 755
PANEL_INDICATORS = ["RSI (speed)", "MACD (momentum)", "Trend strength (ADX)", "Z-score", "Supertrend", "Bollinger band"]

CSS = """<style>
.stApp [data-testid="stMainBlockContainer"], .stApp .block-container { padding-top: 3.2rem !important; max-width: 100% !important; }
.stApp [data-testid="stLayoutWrapper"]:has(> .st-key-tm_ind), .stApp [data-testid="stLayoutWrapper"]:has(> .st-key-tm_lists) { flex:1 1 0 !important; height:auto !important; min-height:100px; }
.st-key-tm_ind, .st-key-tm_lists { height:100% !important; }
[data-testid="stDialog"] [data-testid="stMetric"] { background:rgba(128,128,128,.06); border:1px solid rgba(128,128,128,.28); border-radius:10px; padding:.7rem .95rem; }
[data-testid="stDialog"] [data-testid="stMetricLabel"], [data-testid="stDialog"] [data-testid="stMetricLabel"] * { font-size:.85rem !important; font-weight:500; letter-spacing:.01em; opacity:.75; }
[data-testid="stDialog"] [data-testid="stMetricValue"], [data-testid="stDialog"] [data-testid="stMetricValue"] * { font-size:1.55rem !important; font-weight:650 !important; line-height:1.25; letter-spacing:-.01em; font-variant-numeric:tabular-nums; font-feature-settings:"tnum" 1, "lnum" 1; }
[data-testid="stDialog"] [data-testid="stMetricDelta"], [data-testid="stDialog"] [data-testid="stMetricDelta"] * { font-size:.82rem !important; font-weight:600; font-variant-numeric:tabular-nums; }
[data-testid="stDialog"] button { min-height:2.6rem; font-size:.98rem !important; font-weight:600; border-radius:8px; font-variant-numeric:tabular-nums; }
[data-testid="stDialog"] [role="tab"] button, [data-testid="stDialog"] button[role="tab"] { min-height:0; }
[data-testid="stDialog"] input[type="number"], [data-testid="stDialog"] [data-testid="stNumberInput"] input { font-variant-numeric:tabular-nums; font-weight:600; font-size:1.05rem; }
[data-testid="stDialog"] [data-testid="stAlert"] strong, [data-testid="stDialog"] [data-testid="stAlert"] b { font-variant-numeric:tabular-nums; }
.st-key-tm_strat { background:var(--tm-panel,#fff); border:1px solid var(--tm-line,#dfe3ea); border-radius:14px; padding:1.4rem 1.8rem 1.2rem 1.8rem !important; box-shadow:0 1px 3px rgba(16,24,40,.07); }
.st-key-tm_strat [data-testid="stVerticalBlock"] { gap:.35rem; } .st-key-tm_strat [data-testid="stHorizontalBlock"] { border-bottom:1px solid var(--tm-line,#dfe3ea); padding:.4rem 0; }
.st-key-tm_strat .ss-h { font-size:.85rem; font-weight:600; color:var(--tm-muted,#6b7785); } .st-key-tm_strat .ss-c { font-size:1rem; }
.st-key-tm_strat .up { color:var(--pp-up,#158a7e); } .st-key-tm_strat .down { color:var(--pp-down,#d6453d); } .st-key-tm_strat .flat { color:var(--pp-flat,#6b7785); }
.st-key-tm_strat button { min-height:2rem; padding:.1rem .6rem; font-weight:700; color:var(--tm-accent,#2f5597); }
.tm-row { display:flex; justify-content:space-between; gap:.5rem; padding:.35rem 0; border-bottom:1px solid rgba(128,128,128,.25); font-size:.92rem; }
.tm-row .s { opacity:.65; font-size:.8rem; } .tm-h { font-weight:800; font-size:.8rem; text-transform:uppercase; letter-spacing:.06em; opacity:.7; margin:.5rem 0 .2rem 0; }
.dc-card.tm { padding:.5rem .7rem .05rem .7rem; margin-bottom:.45rem; cursor:help; }
.dc-card.tm .dc-name { font-size:.92rem; } .dc-card.tm .scale { margin:.1rem 0 .3rem 0; }
.dc-card.tm .scale-verdict { font-size:.85rem; margin-top:0; }
.up { color:#26a69a; font-weight:700; } .down { color:#ef5350; font-weight:700; } .flat { color:#868993; font-weight:700; }
</style>"""


def _theme_css(dark):
    """The top bar and the chart controls, in the site's navy (steel blue in Dark mode). Everything is centred on one line."""
    ink, muted = ("#e6e9ef", "#9aa3b2") if dark else ("#1d3557", "#6b7785")
    panel, line = ("#1e222d", "#2a2e39") if dark else ("#ffffff", "#dfe3ea")
    pick, hover = ("#3b5b8c", "rgba(255,255,255,.07)") if dark else ("#1d3557", "rgba(29,53,87,.07)")
    return f"""<style>
:root {{ --tm-panel:{panel}; --tm-line:{line}; --tm-muted:{muted}; --tm-ink:{ink}; --pp-up:{"#26a69a" if dark else "#158a7e"}; --pp-down:{"#ef5350" if dark else "#d6453d"}; --pp-flat:{muted}; --tm-accent:{"#8fa8d4" if dark else "#2f5597"}; --tm-fill:{"#3f5f94" if dark else "#2f5597"}; }}
.st-key-tm_top, .st-key-tm_trade {{ background:{panel}; border:1px solid {line}; border-radius:12px; padding:.6rem 1.2rem !important;
  box-shadow:0 1px 3px rgba(16,24,40,.07); margin-bottom:.8rem; }}
.st-key-tm_trade {{ border:1px solid {line}; border-radius:12px; padding:.55rem 1.2rem !important; box-shadow:0 1px 3px rgba(16,24,40,.07); margin-bottom:0 !important; }}
.st-key-tm_top [data-testid="stHorizontalBlock"], .st-key-tm_trade [data-testid="stHorizontalBlock"] {{ align-items:center !important; gap:1rem; flex-wrap:nowrap; }}
.st-key-tm_top [data-testid="stColumn"], .st-key-tm_trade [data-testid="stColumn"] {{ min-width:0 !important; }}
.st-key-tm_top [data-testid="stVerticalBlock"], .st-key-tm_trade [data-testid="stVerticalBlock"] {{ gap:0 !important; }}
.st-key-tm_top [data-testid="stElementContainer"], .st-key-tm_trade [data-testid="stElementContainer"] {{ margin:0 !important; padding:0 !important; }}
.st-key-tm_trade [data-testid="stMarkdownContainer"] {{ margin:0 !important; }}
.st-key-tm_trade button {{ min-height:2.2rem !important; height:2.2rem !important; font-size:.92rem !important; font-weight:600; border-radius:8px; padding:0 .8rem; }}
.tm-tl {{ font-size:.72rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:{muted}; }}
.tm-ts {{ font-size:.92rem; color:{ink}; margin-top:.1rem; }}
.st-key-tm_top [data-testid="stMarkdownContainer"] {{ margin:0 !important; }}
.st-key-tm_top [data-testid="stColumn"] {{ margin:0 !important; }}
.st-key-tm_top [data-testid="stToggle"] label {{ gap:.5rem; }}
.st-key-tm_top label p, .st-key-tm_chartbar label p {{ white-space:nowrap; font-size:.9rem !important; font-weight:500; color:{muted} !important; margin:0; }}
.st-key-tm_top .st-key-about_btn button {{ min-height:2.1rem !important; height:2.1rem !important; width:2.1rem !important; padding:0 !important;
  font-size:1rem !important; border-width:1.5px !important; border-radius:50% !important; }}
.tm-brand {{ display:flex; align-items:center; gap:.75rem; }} .tm-brand img {{ height:2.4rem; width:auto; display:block; }}
.tm-brand .t {{ font-size:1.35rem; font-weight:700; line-height:1.1; color:{ink}; letter-spacing:.01em; }}
.tm-value {{ border-left:1px solid {line}; padding-left:1.2rem; line-height:1.15; }}
.tm-value .l {{ font-size:.68rem; text-transform:uppercase; letter-spacing:.08em; color:{muted}; }}
.tm-value .v {{ font-size:1.45rem; font-weight:700; color:{ink}; }}
.tm-value .v span {{ font-size:.9rem; font-weight:600; margin-left:.35rem; }}
.st-key-tm_chartbar {{ margin:.2rem 0 .3rem 0; }}
.st-key-tm_chartbar [data-testid="stHorizontalBlock"] {{ align-items:center !important; flex-wrap:nowrap; gap:1.1rem; }}
.st-key-tm_chartbar [data-testid="stColumn"] {{ min-width:0 !important; }}
.st-key-tm_chartbar [data-testid="stElementContainer"] {{ margin:0 !important; }}
.st-key-tm_chartbar button[data-variant="segmented_control"] {{ background:transparent !important; border:1px solid {line} !important;
  padding:.2rem .6rem; min-height:2rem; font-size:.85rem !important; font-weight:500; }}
.st-key-tm_chartbar button[data-variant="segmented_control"] * {{ color:{muted} !important; }}
.st-key-tm_chartbar button[data-variant="segmented_control"]:hover {{ background:{hover} !important; }}
.st-key-tm_chartbar button[data-variant="segmented_control"][data-selected="true"] {{ background:{pick} !important; border-color:{pick} !important; }}
.st-key-tm_chartbar button[data-variant="segmented_control"][data-selected="true"] * {{ color:#ffffff !important; }}
</style>"""


# ---------------- data ----------------
@st.cache_data(ttl=600, show_spinner=False)
def _history(symbol):
    return get_history_with_source(symbol, "7y")


@st.cache_data(ttl=86400, show_spinner=False)
def _name(symbol):
    return companies.NAME_BY_SYMBOL.get(symbol) or get_company_name(symbol)


def _every():
    """Seconds between automatic refreshes (None when switched off or the market is shut)."""
    choice = st.session_state.get("term_refresh", "15 seconds")
    return REFRESH.get(choice) if is_market_open() else None


def switched():
    """Callback of the 'Dashboard view' switch. (Dark mode is left exactly as the visitor has it.)"""


# ---------------- pieces ----------------
@guard()
def _portfolio_value():
    pf = tu._get_portfolio()
    snap = tu.snapshot_now(pf)
    gain = snap["total"] - pf.deposited
    kind = "up" if gain >= 0 else "down"
    pct = gain / pf.deposited * 100 if pf.deposited else 0.0
    st.markdown(f'<div class="tm-value"><div class="l">Portfolio value</div><div class="v">{format_inr(snap["total"], 0)} '
                f'<span class="{kind}">{pct:+.2f}%</span></div></div>', unsafe_allow_html=True)


@guard()
def _lists():
    pf = tu._get_portfolio()
    snap = tu.snapshot_now(pf)
    table = snap["positions"]
    st.markdown('<div class="tm-h">Bought: what you hold</div>', unsafe_allow_html=True)
    if table.empty:
        st.caption("Nothing yet. Use Buy under the chart.")
    for _, r in table.iterrows():
        kind = "up" if r["P&L"] >= 0 else "down"
        st.markdown(f'<div class="tm-row"><div><b>{r["Instrument"]}</b><div class="s">{r["Details"].replace("units", "shares")}</div></div>'
                    f'<div style="text-align:right" class="{kind}">{format_inr(r["P&L"], 0)}<div class="s">{r["P&L %"]:+.1f}%</div></div></div>',
                    unsafe_allow_html=True)
    sells = [o for o in pf.order_history if o["type"] == "SELL"][-6:]
    st.markdown('<div class="tm-h">Sold: recent sales</div>', unsafe_allow_html=True)
    if not sells:
        st.caption("No sales yet.")
    for o in reversed(sells):
        kind = "up" if o["pnl"] >= 0 else "down"
        st.markdown(f'<div class="tm-row"><div><b>{companies.NAME_BY_SYMBOL.get(o["symbol"], o["symbol"])}</b>'
                    f'<div class="s">{o["quantity"]} sold at {format_inr(o["price"])}</div></div>'
                    f'<div style="text-align:right" class="{kind}">{format_inr(o["pnl"], 0)}</div></div>', unsafe_allow_html=True)


@st.cache_data(ttl=10, show_spinner=False)
def _leaderboard_rows(site):
    """Everyone's rank on THIS site, best return first (cached for 10 seconds; `site` keeps the two sites' lists apart)."""
    from core import portfolio_ui
    return portfolio_ui._ranked(tu.get_store().all())


@guard()
def _leaderboard():
    me = tu._get_portfolio().name
    rows = _leaderboard_rows(st.session_state.get("site", "full"))
    st.markdown('<div class="tm-h">Leaderboard</div>', unsafe_allow_html=True)
    if not rows:
        st.caption("No portfolios yet.")
        return
    shown = rows[:4]
    mine = next((r for r in rows if r["Name"] == me), None)
    if mine and mine not in shown:
        shown = shown[:3] + [mine]
    for r in shown:
        kind = "up" if r["Return"] >= 0 else "down"
        you = r["Name"] == me
        st.markdown(f'<div class="tm-row"><div>{"<b>" if you else ""}#{r["Rank"]} {r["Name"]}{" (you)" if you else ""}{"</b>" if you else ""}</div>'
                    f'<div class="{kind}">{r["Return"]:+.2f}%</div></div>', unsafe_allow_html=True)
    if mine:
        st.caption(f"You are #{mine['Rank']} of {len(rows)} by return.")


@guard()
def _ring():
    pf = tu._get_portfolio()
    snap = tu.snapshot_now(pf)
    st.markdown('<div class="tm-h">Where your money is</div>', unsafe_allow_html=True)
    donut = allocation_donut(snap["by_class"])
    donut.update_layout(height=125, margin=dict(l=0, r=0, t=0, b=0), legend=dict(orientation="h", y=-0.05, font=dict(size=11)))
    show_chart(donut, key="term_ring")


@guard()
def _headline(symbol, name, hist, offline):
    quote = None if offline else live_quote(symbol)
    last, prev = float(hist["Close"].iloc[-1]), float(hist["Close"].iloc[-2])
    price = quote["price"] if quote else last
    prev_close = (quote or {}).get("previous_close") or prev
    change = price - prev_close
    kind = "up" if change >= 0 else "down"
    st.markdown(f'<div style="display:flex;align-items:baseline;gap:.8rem;flex-wrap:wrap"><span style="font-size:1.3rem;font-weight:800">{name}</span>'
                f'<span style="font-size:1.7rem;font-weight:800">{format_inr(price)}</span>'
                f'<span class="{kind}">{change:+,.2f} ({change / prev_close * 100:+.2f}%)</span>'
                f'<span style="opacity:.65;font-size:.85rem">{status_message()}{"" if is_market_open() else ", last close"}</span></div>',
                unsafe_allow_html=True)


def _bench_close(symbol):
    """The Nifty 50 closes (or the Sensex's for a BSE listing), used by relative strength and the ML estimate."""
    bench_symbol, _ = companies.benchmark_for(symbol)
    bench, _, _ = _history(bench_symbol)
    return bench["Close"] if bench is not None else None


def _cmt_result(symbol, hist, offline):
    """(result, plan) of the five-CMT-strategy call, or (None, plan) when there is too little history or no index data."""
    now = now_ist().replace(tzinfo=None)
    quote = None if offline else live_quote(symbol)
    open_now = is_market_open() and not offline
    info = dc.plan(hist, now, live_price=quote["price"] if quote else None, market_open=open_now)
    return cmt.evaluate(info["basis"], _bench_close(symbol), info), info


@guard()
def _full_view_body(name, result, ml, rating):
    """The inside of a Full view pop-up."""
    if name == "ML model":
        body = vis.ml_view(ml)
    else:
        body = vis.strategy_view(name, result["view"], rating)
    st.markdown(f'<div class="ss-view">{body}</div>', unsafe_allow_html=True)


def _open_full_view(name, result, ml, rating):
    """Open a strategy's Full view in a pop-up, like the About box."""
    st.dialog(f"{name}: full view", width="large")(_full_view_body)(name, result, ml, rating)


@guard()
def _strategies(symbol, hist, offline):
    """The strategies card: the five CMT strategies and the ML model as rows, each with a Full view pop-up. They only use yesterday's data
    and earlier, so this card does not change during the day and is not refreshed on a timer."""
    result, info = _cmt_result(symbol, hist, offline)
    if result is None:
        show_disclaimer()
        return
    ml = ml_model.estimate(info["basis"], _bench_close(symbol))
    try:
        from core import fusion_ui
        rating = fusion_ui.company_row(symbol)            # the company's Winner's Circle group, if its company results are available
    except Exception:
        rating = None
    rows = vis.strategy_rows(result, cmt.load_stats(), ml)
    with st.container(key="tm_strat"):
        st.markdown('<div class="pp-sec" style="margin-top:0">The strategies behind the reading'
                    '<small>click Full view to see what a strategy is doing</small></div>', unsafe_allow_html=True)
        widths = [1.5, 0.9, 2.0, 1.9, 0.8]
        head = st.columns(widths, vertical_alignment="center")
        for col, label in zip(head, ("Strategy", "Vote", "What it sees", "Back-test: how often it matched the next move", "Full view")):
            col.markdown(f'<span class="ss-h">{label}</span>', unsafe_allow_html=True)
        for i, row in enumerate(rows):
            c1, c2, c3, c4, c5 = st.columns(widths, vertical_alignment="center")
            c1.markdown(f'<span class="pp-sname">{row["name"]}</span>', unsafe_allow_html=True)
            c2.markdown(f'<span class="pp-vote {row["cls"]}">{row["word"]}</span>', unsafe_allow_html=True)
            c3.markdown(f'<span class="ss-c">{row["reading"]}</span>', unsafe_allow_html=True)
            c4.markdown(f'<span class="pp-test">{row["tested"]}</span>', unsafe_allow_html=True)
            if c5.button("Full view", key=f"sv_{i}", width="stretch"):
                _open_full_view(row["name"], result, ml, rating)
        st.markdown(vis.learn_strip() + f'<div class="pp-foot"><b>Disclaimer.</b> {DISCLAIMER}</div>', unsafe_allow_html=True)


@guard()
def _barometer(symbol, hist, offline):
    """How the five strategies read together for this company, as a simple dial."""
    result, _ = _cmt_result(symbol, hist, offline)
    if result is None:
        st.caption("Not enough history for the strategies.")
        return
    voters = [v for v in result["votes"] if v["voting"]]
    ups = sum(1 for v in voters if v["vote"] > 0)
    downs = sum(1 for v in voters if v["vote"] < 0)
    st.markdown(vis.barometer(result["score"], result["n"], ups, downs, len(voters) - ups - downs), unsafe_allow_html=True)


@guard()
def _indicators(symbol, hist, offline):
    result, _ = daily_ui.evaluate_now(symbol, hist, offline, scales=True)          # gauges drawn like the real site's Key signals
    if result is None:
        st.caption("Not enough history for the indicators.")
        return
    st.markdown(f'<div class="tm-h">Indicators for {companies.code_of(symbol)} (hover for a description)</div>', unsafe_allow_html=True)
    by_name = {v["name"]: v for v in result["votes"]}
    chosen = [by_name[n] for n in PANEL_INDICATORS if n in by_name]             # the six that matter most, nicely drawn
    st.markdown("".join(vis.terminal_card(v) for v in chosen), unsafe_allow_html=True)


@st.dialog("Paper trade", width="large")
@guard()
def _order_dialog(mode, symbol, name, price, offline):
    """The order pop-up: stocks first, then ETFs and bonds, futures and options (the same tickets as the real site's Paper trading tab).
    Pop-ups cannot open other pop-ups, so the 'Know how' buttons inside it unfold in place instead."""
    st.session_state["_inline_know_how"] = True
    try:
        _order_tabs(mode, symbol, name, price, offline)
    finally:
        st.session_state.pop("_inline_know_how", None)


def _order_tabs(mode, symbol, name, price, offline):
    pf = tu._get_portfolio()
    stocks_tab, funds_tab, fut_tab, opt_tab = st.tabs(["Stocks", "ETFs and bonds", "Futures", "Options"])
    with stocks_tab:
        st.markdown(f"**{mode} {name}**")
        tu._cash_ticket(pf, symbol, name, price, offline, f"term_{mode.lower()}", mode)
    with funds_tab:
        funds = [x for x in ins.CASH_INSTRUMENTS if ins.asset_class(x) != ins.STOCKS]
        st.caption("Funds that hold many companies or bonds in one. Prices are live exchange prices.")
        tu._trade_picker(pf, "etf", funds, funds[0], offline, "fund")
    with fut_tab:
        tu._futures_ticket(pf, offline)
    with opt_tab:
        tu._options_ticket(pf, offline)


# ---------------- the page ----------------
def _start_tour():
    tour.start(lambda page: None, "dash")


def _finish_tour():
    """Mark the tour as offered (finished, skipped or declined) for this account so the first-visit prompt does not come back."""
    pf = tu._get_portfolio()
    pf.tour_seen = True
    tu._save(pf)


def run():
    pf = tu._get_portfolio()
    tu.housekeeping()
    tu.show_flash()
    tu.show_events()
    st.html(vis.CSS + CSS + _theme_css(bool(st.session_state.get("dark_site"))))
    st.session_state.setdefault("term_refresh", "15 seconds")
    every = _every()

    # top bar
    with st.container(key="tm_top"):
        c_title, c_value, c_dark, c_term, c_tour, c_info = st.columns([3.0, 2.6, 1.4, 1.7, 0.9, 0.5], vertical_alignment="center")
        c_title.markdown(f'<div class="tm-brand">{about._crest_html()}<div class="t">MCGS Stock Explorer</div></div>', unsafe_allow_html=True)
        with c_value:
            st.fragment(run_every=every)(_portfolio_value)()
        c_dark.toggle("Dark mode", key="dark_site", on_change=about._dark_changed)
        c_term.toggle("Dashboard view", key="terminal_view", on_change=switched)
        c_tour.button("Tour", key="tour_btn_top", on_click=_start_tour, help="A quick guided tour of this screen, one part at a time.")
        with c_info:
            about.icon()

    if not pf.tour_seen and tour.active() is None:                   # first visit: offer the tour once
        with st.container(border=True):
            say, yes, no = st.columns([4, 1.2, 1], vertical_alignment="center")
            say.markdown("**New here?** A one-minute tour points out each part of this screen and says what it does.")
            yes.button("Show me around", type="primary", key="tour_yes", width="stretch", on_click=_start_tour)
            no.button("Not now", key="tour_no", width="stretch", on_click=_finish_tour)

    left, mid, right = st.columns([1.2, 3.3, 1.45], gap="small")

    with left:
        lists_box = st.container(height=290, border=True, key="tm_lists")
        ring_box = st.container(border=True)
        board_box = st.container(border=True, key="tm_board")
        baro_box = st.container(border=True, key="tm_baro")
    with lists_box:
        st.fragment(run_every=every)(_lists)()
    with board_box:
        st.fragment(run_every=every)(_leaderboard)()
    with ring_box:
        st.fragment(run_every=every)(_ring)()

    with mid:
        with st.container(key="tm_search"):
            symbol = company_search.choose(compact=True)
        name = _name(symbol)
        hist, source, last_date = _history(symbol)
        offline = source == "offline"
        if hist is None or len(hist) < 30:
            st.error("Price data for this company could not be loaded right now. Please choose another company.")
            show_disclaimer()
            return
        st.fragment(run_every=every)(_headline)(symbol, name, hist, offline)
        with st.container(key="tm_chartarea"):
            price_panel.render(hist, symbol, name, header=False, height=520, explain=False, compact=True)

        price = float(live_quote(symbol)["price"]) if (not offline and live_quote(symbol)) else float(hist["Close"].iloc[-1])
        with st.container(key="tm_trade"):
            t_label, b1, b2, b3 = st.columns([3.2, 1, 1, 1.1], vertical_alignment="center")
            owned = pf.holdings.get(symbol, {}).get("quantity", 0)
            t_label.markdown(f'<div class="tm-tl">Buttons for paper trading</div><div class="tm-ts">{companies.code_of(symbol)}: '
                             f'{"you own " + str(owned) + " share" + ("s" if owned != 1 else "") if owned else "you do not own it yet"}</div>',
                             unsafe_allow_html=True)
            if b1.button("Buy", type="primary", key="term_buy_btn", width="stretch"):
                _order_dialog("Buy", symbol, name, price, offline)
            if b2.button("Sell", key="term_sell_btn", width="stretch", disabled=not (pf.holdings or pf.derivatives),
                         help="Sell what you hold: shares here, or switch to the ETFs, Futures or Options tab. Greyed out until you hold something."):
                _order_dialog("Sell", symbol, name, price, offline)
            if b3.button("Exit all", key="term_exit_btn", width="stretch", disabled=not (pf.holdings or pf.derivatives),
                         help="Sell everything you hold in one go. Your starting capital is not reset."):
                tu._exit_dialog()

    with baro_box:
        st.markdown('<div class="tm-h">Combined strategy reading</div>', unsafe_allow_html=True)
        _barometer(symbol, hist, offline)

    with right:
        box = st.container(height=PANEL_HEIGHT, border=True, key="tm_ind")
        with box:
            st.fragment(run_every=every)(_indicators)(symbol, hist, offline)

    # the strategies table has its own row, as wide as the whole page (left edge of the left column to right edge of the right panel)
    _strategies(symbol, hist, offline)

    tour.render(lambda page: None, _finish_tour, dark=bool(st.session_state.get("dark_site")))
