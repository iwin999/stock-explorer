"""The Dashboard (terminal) view of the SIMPLE site: the whole job on one screen, laid out like a trading terminal.

    top bar:  MCGS Stock Explorer                                    Portfolio value
    left   :  bought and sold list, allocation ring, refresh setting
    centre :  stock search, chart with analysis tools, Buy / Sell / Exit all, prediction comparison for today
    right  :  every indicator, with a hover description, shown relative to its value
"""
import streamlit as st

from core import about, company_search, companies
from core import daily_check as dc
from core import daily_ui
from core import daily_visuals as vis
from core import price_panel
from core import trading_ui as tu
from core.charts import allocation_donut, show as show_chart
from core.errors import guard
from core.formatting import format_inr
from core.live import live_quote
from core.market_data import get_company_name, get_history_with_source
from core.market_hours import is_market_open, now_ist, status_message

REFRESH = {"Off": None, "15 seconds": 15, "30 seconds": 30, "1 minute": 60}     # live prices are shared for 15 seconds at a time
PANEL_HEIGHT = 700

CSS = """<style>
.stApp [data-testid="stMainBlockContainer"], .stApp .block-container { padding-top: 3.2rem !important; max-width: 100% !important; }
.tm-brand { display:flex; align-items:center; gap:.7rem; } .tm-brand img { height:2.6rem; width:auto; }
.tm-brand .t { font-size:1.55rem; font-weight:800; line-height:1.1; }
.tm-value { text-align:left; padding-left:1.1rem; border-left:1px solid rgba(128,128,128,.35); } .tm-value .l { font-size:.8rem; text-transform:uppercase; letter-spacing:.06em; opacity:.7; }
.tm-value .v { font-size:1.7rem; font-weight:800; line-height:1.1; }
.st-key-tm_top { background:rgba(128,128,128,.10); border:1px solid rgba(128,128,128,.28); border-radius:16px; padding:.55rem 1.1rem !important; margin-bottom:.7rem; }
.st-key-tm_top label p, .st-key-tm_chartbar label p { white-space:nowrap; font-size:.95rem !important; font-weight:600; }
.st-key-tm_top [data-testid="stHorizontalBlock"] { gap:.6rem; flex-wrap:nowrap; }
.st-key-tm_top [data-testid="stColumn"], .st-key-tm_chartbar [data-testid="stColumn"] { min-width:0 !important; }
.st-key-tm_chartbar { margin:.3rem 0 .2rem 0; } .st-key-tm_chartbar [data-testid="stHorizontalBlock"] { flex-wrap:nowrap; gap:.8rem; }
.st-key-tm_chartbar [data-testid="stButtonGroup"] button { padding:.25rem .8rem; min-height:2.1rem; font-size:.92rem !important; }
.st-key-tm_chartbar button[data-variant="segmented_control"] { background:transparent !important; color:inherit !important; border:1px solid rgba(128,128,128,.45) !important; }
.st-key-tm_chartbar button[data-variant="segmented_control"][data-selected="true"] { background:#2962ff !important; color:#ffffff !important; border:1px solid #2962ff !important; }
.st-key-tm_chartbar button[data-variant="segmented_control"] * { color:inherit !important; }
.tm-row { display:flex; justify-content:space-between; gap:.5rem; padding:.35rem 0; border-bottom:1px solid rgba(128,128,128,.25); font-size:.92rem; }
.tm-row .s { opacity:.65; font-size:.8rem; } .tm-h { font-weight:800; font-size:.8rem; text-transform:uppercase; letter-spacing:.06em; opacity:.7; margin:.5rem 0 .2rem 0; }
.dc-card.tm { padding:.5rem .7rem .05rem .7rem; margin-bottom:.45rem; cursor:help; }
.dc-card.tm .dc-name { font-size:.92rem; } .dc-card.tm .scale { margin:.1rem 0 .3rem 0; }
.dc-card.tm .scale-verdict { display:none; }
.up { color:#26a69a; font-weight:700; } .down { color:#ef5350; font-weight:700; } .flat { color:#868993; font-weight:700; }
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
                f'<span class="{kind}" style="font-size:1rem">{pct:+.2f}%</span></div></div>', unsafe_allow_html=True)


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


@guard()
def _ring():
    pf = tu._get_portfolio()
    snap = tu.snapshot_now(pf)
    st.markdown('<div class="tm-h">Where your money is</div>', unsafe_allow_html=True)
    donut = allocation_donut(snap["by_class"])
    donut.update_layout(height=230, margin=dict(l=0, r=0, t=0, b=0), legend=dict(orientation="h", y=-0.05, font=dict(size=11)))
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


@guard()
def _prediction(symbol, name, hist, offline):
    st.markdown('<div class="tm-h">Prediction comparison for today</div>', unsafe_allow_html=True)
    result, info = daily_ui.evaluate_now(symbol, hist, offline)
    if result is None:
        st.caption("Not enough history for this company to make a call.")
        return
    voters = [v for v in result["votes"] if v["voting"]]
    word = "today" if result["target"] == now_ist().date() else result["target"].strftime("on %d %b")
    left, right = st.columns([1.3, 1.7])
    left.markdown(vis.hero(result["prediction"], result["score"], voters, word), unsafe_allow_html=True)
    if result["actual"] is None:
        right.info("Today's price is not available yet to compare.")
    else:
        right.markdown(vis.versus(result["prediction"], result["actual_direction"], result["matched"]), unsafe_allow_html=True)
        right.markdown(vis.range_bar(result["range"][0], result["range"][1], result["prev_close"], result["actual"],
                                     "Now" if result["status"] == "live" else "Close"), unsafe_allow_html=True)
    if info["note"]:
        st.caption(info["note"])


@guard()
def _indicators(symbol, hist, offline):
    result, _ = daily_ui.evaluate_now(symbol, hist, offline)
    if result is None:
        st.caption("Not enough history for the indicators.")
        return
    st.markdown(f'<div class="tm-h">Indicators for {companies.code_of(symbol)} (hover for a description)</div>', unsafe_allow_html=True)
    ordered = [v for v in result["votes"] if v["voting"]] + [v for v in result["votes"] if not v["voting"]]
    st.markdown("".join(vis.terminal_card(v) for v in ordered), unsafe_allow_html=True)


@st.dialog("Paper trade")
def _order_dialog(mode, symbol, name, price, offline):
    pf = tu._get_portfolio()
    st.markdown(f"**{mode} {name}**")
    tu._cash_ticket(pf, symbol, name, price, offline, f"term_{mode.lower()}", mode)


# ---------------- the page ----------------
def run():
    pf = tu._get_portfolio()
    tu.housekeeping()
    tu.show_flash()
    tu.show_events()
    st.html(vis.CSS + CSS)
    st.session_state.setdefault("term_refresh", "15 seconds")
    every = _every()

    # top bar
    with st.container(key="tm_top"):
        c_title, c_value, c_dark, c_term, c_info = st.columns([3.1, 2.7, 1.5, 1.8, 0.5], vertical_alignment="center")
        c_title.markdown(f'<div class="tm-brand">{about._crest_html()}<div class="t">MCGS Stock Explorer</div></div>', unsafe_allow_html=True)
        with c_value:
            st.fragment(run_every=every)(_portfolio_value)()
        c_dark.toggle("Dark mode", key="dark_site", on_change=about._dark_changed)
        c_term.toggle("Dashboard view", key="terminal_view", on_change=switched)
        with c_info:
            about.icon()

    left, mid, right = st.columns([1.2, 3.3, 1.45], gap="small")

    with left:
        lists_box = st.container(height=290, border=True)
        ring_box = st.container(height=270, border=True)
        refresh_box = st.container(border=True)
    with refresh_box:
        st.selectbox("Refreshing at intervals configured", list(REFRESH), key="term_refresh",
                     help="How often prices and your portfolio update by themselves. Prices from Yahoo are shared for 15 seconds, so "
                          "going faster would not show anything new. Updates only happen while the market is open.")
        st.caption(f"{status_message()}." + (" Updating automatically." if every else " Not updating by itself."))
    with lists_box:
        st.fragment(run_every=every)(_lists)()
    with ring_box:
        st.fragment(run_every=every)(_ring)()

    with mid:
        symbol = company_search.choose(compact=True)
        name = _name(symbol)
        hist, source, last_date = _history(symbol)
        offline = source == "offline"
        if hist is None or len(hist) < 30:
            st.error("Price data for this company could not be loaded right now. Please choose another company.")
            return
        st.fragment(run_every=every)(_headline)(symbol, name, hist, offline)
        price_panel.render(hist, symbol, name, header=False, height=420, explain=False, compact=True)

        price = float(live_quote(symbol)["price"]) if (not offline and live_quote(symbol)) else float(hist["Close"].iloc[-1])
        st.markdown('<div class="tm-h">Buttons for paper trading</div>', unsafe_allow_html=True)
        b1, b2, b3, _ = st.columns([1, 1, 1, 2.2])
        if b1.button("Buy", type="primary", key="term_buy_btn", width="stretch"):
            _order_dialog("Buy", symbol, name, price, offline)
        if b2.button("Sell", key="term_sell_btn", width="stretch", disabled=symbol not in pf.holdings,
                     help="Sell some or all of this company. Greyed out when you do not own it."):
            _order_dialog("Sell", symbol, name, price, offline)
        if b3.button("Exit all", key="term_exit_btn", width="stretch", disabled=not (pf.holdings or pf.derivatives),
                     help="Sell everything you hold in one go. Your starting capital is not reset."):
            tu._exit_dialog()
        st.fragment(run_every=every)(_prediction)(symbol, name, hist, offline)

    with right:
        box = st.container(height=PANEL_HEIGHT, border=True)
        with box:
            st.fragment(run_every=every)(_indicators)(symbol, hist, offline)
