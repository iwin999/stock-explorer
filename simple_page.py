"""Stock Explorer, simple version: the same accounts, prices and leaderboard as the full site, in plain words, built for a
phone (one column, big buttons, a menu along the bottom) and with a guided tour for first-time visitors."""
import math

import streamlit as st

from core import instruments as ins
from core import about, assistant_ui, companies, tour, universe
from core import simple_words as words
from core.charts import allocation_donut, show as show_chart, simple_line_chart
from core.formatting import format_inr
from core.live import live_quote
from core.market_data import get_history_with_source, load_offline
from core.market_hours import is_market_open, now_ist
from core.trading import TradingError
from core.ui import STYLE_CSS, DARK_CSS, show_disclaimer
from core import trading_ui as tu

PAGES = ["Home", "Company", "Portfolio", "Learn"]
POPULAR = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ITC.NS", "SBIN.NS"]

st.set_page_config(page_title="Stock Explorer (simple)", layout="centered")
st.markdown(STYLE_CSS, unsafe_allow_html=True)
if st.session_state.get("dark_site"):
    st.markdown(DARK_CSS, unsafe_allow_html=True)
st.markdown("""<style>
.stApp [data-testid="stMainBlockContainer"], .stApp .block-container { max-width: 560px; padding: 2.4rem 1rem 9rem 1rem !important; }
.stApp, .stApp p, .stApp label { font-size: 1.08rem; }
.stApp button { min-height: 3rem; font-size: 1.05rem !important; border-radius: 12px; }
.big-number { font-size: 2.3rem; font-weight: 700; line-height: 1.1; }
.up { color: #1f9d73; font-weight: 600; } .down { color: #d6453d; font-weight: 600; } .flat { color: #6b7785; font-weight: 600; }
.card { border: 1px solid #d8dde6; border-radius: 14px; padding: 0.9rem 1rem; margin: 0.4rem 0 0.8rem 0; }
.st-key-bottomnav { position: fixed; bottom: 0; left: 0; right: 0; z-index: 998; padding: 0.4rem 0.6rem 0.7rem 0.6rem;
  background: #ffffff; border-top: 1px solid #d8dde6; }
.st-key-bottomnav [role="radiogroup"] { display: flex; width: 100%; max-width: 560px; margin: 0 auto; gap: 0.3rem; }
.st-key-bottomnav [role="radiogroup"] label { flex: 1 1 0; justify-content: center; border-radius: 12px; padding: 0.55rem 0.2rem;
  border: 1px solid #d8dde6; margin: 0; }
.st-key-bottomnav [role="radiogroup"] label > div { margin: 0; padding: 0; justify-content: center; width: 100%; }
.st-key-bottomnav [role="radiogroup"] label > div > div:first-child { display: none !important; }
.st-key-bottomnav [role="radiogroup"] { flex-wrap: nowrap !important; }
.st-key-bottomnav [role="radiogroup"] label[data-selected="true"] { background: #2962ff; border-color: #2962ff; }
.st-key-bottomnav [role="radiogroup"] label[data-selected="true"] p { color: #ffffff !important; }
.st-key-bottomnav [role="radiogroup"] p { font-weight: 600; text-align: center; font-size: 1rem !important; margin: 0; }
.st-key-simplehead [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; align-items: center; }
.st-key-simplehead [data-testid="stColumn"] { min-width: 0 !important; }
.st-key-bottomnav [data-testid="stWidgetLabel"] { display: none; }
</style>""", unsafe_allow_html=True)
if st.session_state.get("dark_site"):
    st.markdown("<style>.card { border-color: #2a2e39; } .st-key-bottomnav { background: #131722; border-top-color: #2a2e39; }"
                " .st-key-bottomnav [role='radiogroup'] label { border-color: #2a2e39; }</style>", unsafe_allow_html=True)

if not tu.has_account():
    tu.capital_gate()
    st.stop()
pf = tu._get_portfolio()


# ---------------- small helpers ----------------
def set_page(name):
    st.session_state["spage"] = name


def finish_tour():
    pf.tour_seen = True
    tu._save(pf)


def open_company(symbol, mode=None):
    """Button callback: show a company's page (optionally with Sell already chosen)."""
    st.session_state["scompany"] = symbol
    if mode:
        st.session_state["s_mode"] = mode
    set_page("Company")
    st.session_state["s_box"] = None


def search_changed():
    value = st.session_state.get("s_box")
    st.session_state.pop("s_suggest", None)
    if not value:
        return
    action, result = words.resolve_search(value)
    if action == "open":
        open_company(result)
    else:
        st.session_state["s_suggest"] = (value, result)


def start_tour():
    tour.start(set_page)


def decline_tour():
    finish_tour()


@st.cache_data(ttl=600, show_spinner=False)
def load_history(symbol):
    return get_history_with_source(symbol, "2y")


def day_move(symbol):
    """(price, change, percent) for today from the live quote, else from the last two saved closes, else None."""
    q = live_quote(symbol)
    if q and q.get("previous_close"):
        return q["price"], q["price"] - q["previous_close"], (q["price"] / q["previous_close"] - 1) * 100
    df = load_offline(symbol)
    if df is not None and len(df) >= 2:
        last, prev = float(df["Close"].iloc[-1]), float(df["Close"].iloc[-2])
        return last, last - prev, (last / prev - 1) * 100
    return None


def span(text, kind):
    return f'<span class="{kind}">{text}</span>'


# ---------------- header ----------------
with st.container(key="simplehead"):
    st.markdown(f'<div class="brand">{about._crest_html()}<h1 style="font-size:1.9rem !important">Stock Explorer</h1></div>',
                unsafe_allow_html=True)
    left, right = st.columns([4, 1])
    left.toggle("Dark mode", key="dark_site", on_change=about._dark_changed)
    with right:
        about.icon()
tu.housekeeping()
tu.show_flash()
page = st.session_state.get("spage", "Home")
if page not in PAGES:
    page = "Home"
snap = tu.snapshot_now(pf)


def money_card():
    gain = snap["total"] - pf.deposited
    pct = gain / pf.deposited * 100 if pf.deposited else 0.0
    kind = "up" if gain >= 0 else "down"
    from core.portfolio_ui import my_rank
    rank = my_rank()
    st.markdown(
        f'<div class="card"><div>Your practice money</div><div class="big-number">{format_inr(snap["total"], 0)}</div>'
        f'<div>{span(words.gain_words(gain, pct), kind)} since you started</div>'
        f'<div style="margin-top:0.4rem">Cash to spend: <b>{format_inr(pf.balance, 0)}</b>'
        + (f' &nbsp;|&nbsp; Rank <b>#{rank[0]} of {rank[1]}</b>' if rank else '') + '</div></div>', unsafe_allow_html=True)


# =====================================================================
# HOME
# =====================================================================
def home():
    if not pf.tour_seen and tour.active() is None:
        with st.container(border=True):
            st.markdown("**New here? Want a quick tour?**")
            st.caption("About a minute. It points out each part of the site and says what it does.")
            a, b = st.columns(2)
            a.button("Yes, show me around", type="primary", key="tour_yes", width="stretch", on_click=start_tour)
            b.button("Not now", key="tour_no", width="stretch", on_click=decline_tour)

    with st.container(key="tour_search"):
        st.selectbox("Find a company", universe.OPTIONS, index=None, key="s_box", accept_new_options=True,
                     format_func=companies.label, on_change=search_changed,
                     placeholder="Type a name, like Tata or Reliance", label_visibility="visible")
    sug = st.session_state.get("s_suggest")
    if sug:
        typed, found = sug
        if found:
            st.caption(f"Closest to “{typed}”, best first. Tap one to open it.")
            for s in found:
                st.button(companies.label(s), key=f"sugg_{s}", width="stretch", on_click=open_company, args=(s,))
        else:
            st.warning(f"Nothing looks like “{typed}”. Try another spelling.")

    with st.container(key="tour_summary"):
        money_card()
        n = day_move("^NSEI")
        b = day_move("^BSESN")
        bits = []
        for label, mv in (("Nifty 50", n), ("Sensex", b)):
            if mv:
                bits.append(label + " " + span("%+.2f%%" % mv[2], "up" if mv[2] >= 0 else "down"))
        status = "Market is open" if is_market_open() else "Market is closed (showing the last close)"
        st.markdown(f"{status}. " + " &nbsp;|&nbsp; ".join(bits), unsafe_allow_html=True)

    with st.container(key="tour_picks"):
        st.markdown("**Popular companies**")
        for sym in POPULAR:
            mv = day_move(sym)
            tail = f"   {mv[2]:+.1f}%" if mv else ""
            st.button(f"{companies.NAME_BY_SYMBOL.get(sym, sym)}{tail}", key=f"pick_{sym}", width="stretch",
                      on_click=open_company, args=(sym,))
    st.button("Take the tour again", key="tour_again", on_click=start_tour)


# =====================================================================
# COMPANY
# =====================================================================
def _set_amount(value):
    st.session_state["s_amount"] = value


def company():
    symbol = st.session_state.get("scompany") or POPULAR[0]
    name = companies.NAME_BY_SYMBOL.get(symbol, symbol)
    hist, source, _ = load_history(symbol)
    if hist is None or len(hist) < 30:
        st.warning("Price data for this company is not available right now. Please try another one.")
        st.button("Back to Home", on_click=set_page, args=("Home",), key="nodata_back")
        return
    mv = day_move(symbol) or (float(hist["Close"].iloc[-1]), 0.0, 0.0)
    price, change, pct = mv
    text, kind = words.move_words(change, pct)
    st.markdown(f"### {name}")
    st.markdown(f'<div class="big-number">{format_inr(price)}</div><div>{span(text, kind)}</div>', unsafe_allow_html=True)
    if source == "offline":
        st.caption("Saved prices are being shown, so this may not be today's price.")

    with st.container(key="tour_chart"):
        period = st.radio("Show", list(words.PERIODS), horizontal=True, key="s_period", label_visibility="collapsed")
        show_chart(simple_line_chart(hist["Close"], words.PERIODS[period], name), key="simple_chart")

    with st.container(key="tour_verdict"):
        st.markdown("**How is it doing?**")
        for heading, sentence, colour in words.verdict(hist):
            st.markdown(f"{span(heading, colour)}: {sentence}", unsafe_allow_html=True)
        st.caption("This describes the past. It does not predict the future and is not advice.")

    owned = pf.holdings.get(symbol, {}).get("quantity", 0)
    with st.container(key="tour_trade"):
        st.markdown("**Buy or sell (practice money)**")
        modes = ["Buy", "Sell"] if owned else ["Buy"]
        if st.session_state.get("s_mode") not in modes:
            st.session_state["s_mode"] = "Buy"
        mode = st.radio("I want to", modes, horizontal=True, key="s_mode")
        if owned:
            avg = pf.holdings[symbol]["avg_price"]
            st.caption(f"You own {owned} share(s), now worth {format_inr(owned * price, 0)} "
                       f"({words.gain_words((price - avg) * owned, (price / avg - 1) * 100)}).")
        if mode == "Buy":
            _buy_box(pf, symbol, name, price)
        else:
            _sell_box(pf, symbol, name, price, owned)


def _buy_box(pf, symbol, name, price):
    st.write("How much money do you want to spend?")
    cols = st.columns(4)
    for col, amount in zip(cols, (1000, 5000, 10000, 25000)):
        col.button(f"{amount:,}", key=f"amt_{amount}", width="stretch", on_click=_set_amount, args=(amount,))
    st.session_state.setdefault("s_amount", 5000)
    amount = st.number_input("Amount in rupees", min_value=100, step=500, key="s_amount")
    qty = int(amount // price)
    if qty < 1:
        st.warning(f"That is less than the price of one share ({format_inr(price)}). Try a bigger amount.")
        return
    cost = qty * price
    if cost > pf.balance:
        st.warning(f"You only have {format_inr(pf.balance, 0)} to spend.")
        return
    st.info(f"You will get **{qty} share(s)** of {name} for about **{format_inr(cost, 0)}**. "
            f"Cash left: {format_inr(pf.balance - cost, 0)}.")
    if st.button(f"Buy {qty} share(s)", type="primary", width="stretch", key="s_buy"):
        _trade("Buy", symbol, name, qty, price)


def _sell_box(pf, symbol, name, price, owned):
    part = st.radio("How much?", ["All", "Half", "Quarter"], horizontal=True, key="s_part")
    qty = max(1, int(owned * {"All": 1, "Half": 0.5, "Quarter": 0.25}[part]))
    avg = pf.holdings[symbol]["avg_price"]
    pnl = (price - avg) * qty
    st.info(f"You will sell **{qty} of your {owned} share(s)** for about **{format_inr(qty * price, 0)}**. "
            f"That locks in a {'profit' if pnl >= 0 else 'loss'} of {format_inr(abs(pnl), 0)}.")
    if st.button(f"Sell {qty} share(s)", type="primary", width="stretch", key="s_sell"):
        _trade("Sell", symbol, name, qty, price)


def _trade(mode, symbol, name, qty, price):
    from core.market_data import get_latest_price
    fresh = get_latest_price(symbol)
    exec_price = round(fresh, 2) if fresh else round(price, 2)
    try:
        if mode == "Buy":
            pf.buy(symbol, qty, exec_price)
            message = f"Bought {qty} share(s) of {name} at {format_inr(exec_price)}."
        else:
            order = pf.sell(symbol, qty, exec_price)
            message = f"Sold {qty} share(s) of {name} at {format_inr(exec_price)}. Profit/loss: {format_inr(order['pnl'])}."
        tu._save(pf)
        st.session_state.flash = ("ok", message)
    except TradingError as e:
        st.session_state.flash = ("error", str(e))
    st.rerun()


# =====================================================================
# PORTFOLIO
# =====================================================================
def portfolio():
    money_card()
    with st.container(key="tour_holdings"):
        st.markdown("**What you own**")
        table = snap["positions"]
        shares = table[table["Class"].isin([ins.STOCKS, ins.ETFS, ins.BONDS])] if not table.empty else table
        if shares.empty:
            st.info("You do not own anything yet. Find a company on Home and buy your first share.")
        for _, row in shares.iterrows():
            kind = "up" if row["P&L"] >= 0 else "down"
            left, right = st.columns([3, 1.2])
            left.markdown(f"**{row['Instrument']}**  \n{row['Details'].replace('units', 'shares')}, worth {format_inr(row['Value'], 0)}  \n"
                          f"{span(words.gain_words(row['P&L'], row['P&L %']), kind)}", unsafe_allow_html=True)
            right.button("Sell", key=f"sellrow_{row['Symbol']}", width="stretch", on_click=open_company,
                         args=(row["Symbol"], "Sell"))
        if pf.derivatives:
            st.caption("You also hold futures or options from the full site. Open the full site to manage those.")
    if snap["total"] > 0 and (pf.holdings or pf.derivatives):
        st.markdown("**Where your money is**")
        donut = allocation_donut(snap["by_class"])
        donut.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0))
        show_chart(donut, key="simple_donut")

    with st.container(key="tour_leader"):
        st.markdown("**Leaderboard**")
        from core.portfolio_ui import _all_accounts, _ranked
        try:
            rows = _ranked(_all_accounts(tu.get_store()))
        except Exception:
            rows = []
        shown = rows[:5]
        if rows and not any(r["Name"] == pf.name for r in shown):
            shown += [r for r in rows if r["Name"] == pf.name]
        for r in shown:
            me = r["Name"] == pf.name
            kind = "up" if r["Return"] >= 0 else "down"
            line = f"#{r['Rank']}  {r['Name']}" + (" (you)" if me else "")
            ret = span("%+.1f%%" % r["Return"], kind)
            st.markdown((f"**{line}**" if me else line) + "  " + ret, unsafe_allow_html=True)
        if not rows:
            st.caption("No portfolios yet.")


# =====================================================================
# LEARN
# =====================================================================
IDEAS = {
    "What is a share?": "A share is a tiny piece of a company. If you own a share of a company, you own a small part of it. "
                        "When the company does well, the price of its share usually goes up.",
    "What is the market?": "The stock market is a big marketplace where people buy and sell shares. The Nifty 50 and the Sensex "
                           "are scores that show how the biggest companies are doing together.",
    "Profit and loss": "If you sell for more than you paid, that is a profit. If you sell for less, that is a loss. "
                       "Until you sell, it is only on paper.",
    "Why do prices move?": "Prices go up when more people want to buy than sell, and down when more want to sell. News about "
                           "a company, the economy and even mood can change that.",
    "Spreading your money": "Putting all your money in one company is risky. Spreading it across different companies means "
                            "one bad day for one company hurts less. People call this diversification.",
}


def learn():
    st.session_state.setdefault("chat_level", "age_10")
    with st.container(key="tour_bot"):
        assistant_ui.render({"company": companies.NAME_BY_SYMBOL.get(st.session_state.get("scompany") or POPULAR[0], ""),
                             "symbol": st.session_state.get("scompany") or POPULAR[0], "last_close": None, "signals": [],
                             "portfolio": {"cash": pf.balance, "holdings": {s: h["quantity"] for s, h in pf.holdings.items()},
                                           "derivatives": len(pf.derivatives)}, "fusion": None})
    st.markdown("### Big ideas in plain words")
    for title, text in IDEAS.items():
        with st.expander(title):
            st.write(text)
    st.button("Take the tour again", key="tour_again_learn", on_click=start_tour)


# ---------------- draw the chosen page ----------------
{"Home": home, "Company": company, "Portfolio": portfolio, "Learn": learn}[page]()
show_disclaimer()

with st.container(key="bottomnav"):
    st.radio("Menu", PAGES, horizontal=True, key="spage", label_visibility="collapsed")

tour.render(set_page, finish_tour, dark=bool(st.session_state.get("dark_site")))
