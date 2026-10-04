"""Accounts and the Paper trading tab.

  * capital_gate()  - the first screen: choose a name and starting capital (or open an existing account).
  * render()        - the Paper trading tab: stocks, ETFs and bonds, futures and options.

All the maths lives in core/trading.py, core/derivatives.py and core/valuation.py; this file is only the screen.
Parts of the page are st.fragments: Streamlit re-runs just those parts every few seconds while the market is
open, so prices and profit/loss move live without reloading the whole page.
"""
import streamlit as st

from core import about
from core import accounts as acc
from core import derivatives as dv
from core import instruments as ins
from core import valuation as val
from core.formatting import format_inr
from core.live import REFRESH_SECONDS, close_on, live_quote, spot_price, vol_estimate
from core.market_data import get_latest_price
from core.market_hours import is_market_open, now_ist
from core.trading import MAX_CAPITAL, MIN_CAPITAL, Portfolio, TradingError, check_capital
from core.errors import guard
from core.ui import know_how_button, notice, show_disclaimer

CAPITAL_PRESETS = [50000, 100000, 500000, 1000000]
DERIVATIVES_NOTE = ("Futures and options prices here are **calculated** from the live share price with standard "
                    "formulas, because free data for NSE or BSE derivatives does not exist. Lot sizes and margins are "
                    "simplified for learning. They are estimates, not exchange quotes.")


# ---------------- where accounts are kept ----------------
@st.cache_resource
def _file_store():
    return acc.FileStore()


@st.cache_resource
def _supabase_store(url, key):
    return acc.SupabaseStore(url, key)


def get_store():
    """The online database when its secrets are set, otherwise files on this computer.

    The secrets are checked on every run (it is cheap), so if they are added or changed while the app is
    already running, the app notices straight away instead of staying on the old storage.
    """
    try:
        cfg = st.secrets["supabase"]
        return _supabase_store(str(cfg["url"]).strip(), str(cfg["key"]).strip())
    except Exception:
        return _file_store()


def storage_diagnosis():
    """Why the online database is not being used (None if it is configured)."""
    try:
        keys = list(st.secrets.keys())
    except Exception:
        keys = []
    if "supabase" not in keys:
        return "No [supabase] section was found in the app's secrets."
    cfg = st.secrets["supabase"]
    missing = [k for k in ("url", "key") if k not in cfg]
    if missing:
        return f"The [supabase] section of the secrets is missing: {', '.join(missing)}."
    return None


def admin_pin():
    try:
        return str(st.secrets["admin_pin"])
    except Exception:
        return None


def has_account():
    """True when a user is signed in. A refresh keeps them signed in: their name rides along in the page address."""
    if "portfolio" in st.session_state:
        return True
    name = st.query_params.get("user")
    if name:
        try:
            pf = acc.load_account(get_store(), name)
        except acc.StorageError:
            pf = None
        if pf is not None:
            st.session_state.portfolio = pf
            return True
        del st.query_params["user"]
    return False


def _get_portfolio():
    return st.session_state.portfolio


def _save(pf):
    """Save the account. A failure is remembered and shown as a banner instead of crashing."""
    try:
        acc.save_account(get_store(), pf)
        st.session_state.pop("save_error", None)
    except acc.AccountGone:
        _sign_out()
        st.session_state.gate_notice = ("This portfolio was removed by the organiser, so you have been signed out. "
                                        "You can create a new one below.")
    except acc.StorageError as e:
        st.session_state.save_error = str(e)


def _sign_in(pf):
    st.session_state.portfolio = pf
    st.session_state.pop("flash", None)
    st.session_state.pop("gate_notice", None)
    st.query_params["user"] = pf.name


def _sign_out():
    st.session_state.pop("portfolio", None)
    if "user" in st.query_params:
        del st.query_params["user"]


# ---------------- first screen ----------------
def capital_gate():
    """Choose a name and starting capital, or open an existing account."""
    store = get_store()
    about.title_row("Stock Explorer")
    st.subheader("Welcome. Who is investing today?")
    st.caption("Practise with virtual money. Nothing real is invested. Your portfolio is saved under your name, "
               "so you can come back and check it later.")

    if st.session_state.get("gate_notice"):
        notice(st.session_state.pop("gate_notice"))
    mode = st.radio("I am a", ["New user", "Returning user"], horizontal=True, key="gate_mode")

    if mode == "New user":
        name = st.text_input("Choose your name", max_chars=24, key="gate_name", placeholder="e.g. Asha")
        labels = [format_inr(a, 0) for a in CAPITAL_PRESETS] + ["Other amount"]
        choice = st.radio("How much would you like to practise with?", labels, index=1, horizontal=True, key="gate_cap")
        if choice == "Other amount":
            amount = st.number_input("Enter your amount (Rs)", min_value=int(MIN_CAPITAL), max_value=int(MAX_CAPITAL),
                                     value=100000, step=10000, key="gate_custom")
            st.caption(f"{format_inr(amount, 0)}  (between {format_inr(MIN_CAPITAL, 0)} and {format_inr(MAX_CAPITAL, 0)})")
        else:
            amount = CAPITAL_PRESETS[labels.index(choice)]
        if st.button("Start", type="primary", key="gate_start"):
            try:
                _sign_in(acc.create_account(store, name, amount))
                st.rerun()
            except (acc.StorageError, TradingError) as e:
                st.error(str(e))
    else:
        try:
            names = store.names()
        except acc.StorageError as e:
            st.error(str(e))
            names = []
        if not names:
            st.info("There are no saved portfolios yet. Choose “New user” to create one.")
        else:
            pick = st.selectbox("Choose your name (type to search)", names, key="gate_pick")
            if st.button("Open my portfolio", type="primary", key="gate_open"):
                try:
                    pf = acc.load_account(store, pick)
                    if pf is None:
                        st.error("That portfolio could not be found.")
                    else:
                        _sign_in(pf)
                        st.rerun()
                except acc.StorageError as e:
                    st.error(str(e))
    st.caption(f"Portfolios are saved in: {store.label}.")
    show_disclaimer()


def user_bar():
    """'Signed in as ...' with a Switch user button."""
    pf = _get_portfolio()
    left, right = st.columns([5, 1])
    left.markdown(f"Signed in as **{pf.name}**")
    if right.button("Switch user", key="switch_user"):
        _sign_out()
        st.rerun()
    if st.session_state.get("save_error"):
        notice(f"Your latest change could not be saved: {st.session_state.save_error}")


def housekeeping():
    """Settle expired contracts and close busted futures, as a broker would. Messages are shown once."""
    pf = _get_portfolio()
    if not pf.derivatives:
        return
    events = val.settle_and_square_off(pf, spot_price, vol_estimate, close_on)
    if events:
        _save(pf)
        st.session_state.setdefault("events", []).extend(events)


def show_events():
    for message in st.session_state.pop("events", []):
        notice(message)


def show_flash():
    """The result of the last click (shown once, at the top of the page, whichever tab it came from)."""
    flash = st.session_state.pop("flash", None)
    if flash:
        (st.success if flash[0] == "ok" else st.error)(flash[1])


# ---------------- prices ----------------
def price_of(symbol, fallback=None):
    """Latest price (shared 15-second cache), or the fallback if Yahoo can't be reached."""
    quote = live_quote(symbol)
    return round(quote["price"], 2) if quote else fallback


def _refresh_every():
    """Seconds between automatic updates: only while the market is open."""
    return REFRESH_SECONDS if is_market_open() else None


def snapshot_now(pf):
    return val.snapshot(pf, spot_price, vol_estimate)


def _colour_pnl(value):
    return "color: #2a9d6f" if value >= 0 else "color: #c8553d"


def positions_table(snap):
    """A formatted table of everything the account holds (None if it holds nothing)."""
    table = snap["positions"]
    if table.empty:
        return None
    show = table.drop(columns=["Symbol"])
    return (show.style
            .format({"Bought at": format_inr, "Now": format_inr, "Value": format_inr, "P&L": format_inr,
                     "P&L %": "{:+.2f}%"})
            .map(_colour_pnl, subset=["P&L", "P&L %"]))


# ---------------- the tab ----------------
def render(symbol, name, fallback_price, offline=False):
    pf = _get_portfolio()

    st.caption("Practise with **virtual** money. Nothing here is real. **In short:** pick Buy or Sell, choose what, choose how much, press the button.")
    if offline:
        notice("Prices below come from saved data, not live prices.")

    st.fragment(run_every=None if offline else _refresh_every())(_account_summary)()

    stocks_tab, etf_tab, fut_tab, opt_tab = st.tabs(["Stocks", "ETFs and bonds", "Futures", "Options"])
    with stocks_tab:
        stocks = [s for s in ins.CASH_INSTRUMENTS if ins.asset_class(s) == ins.STOCKS]
        _trade_picker(pf, "stk", stocks, symbol, offline, "company", open_universe=True)
    with etf_tab:
        etfs = [s for s in ins.CASH_INSTRUMENTS if ins.asset_class(s) != ins.STOCKS]
        st.caption("Funds that hold many companies or bonds in one. Prices are live exchange prices.")
        _trade_picker(pf, "etf", etfs, etfs[0], offline, "fund")
    with fut_tab:
        _futures_ticket(pf, offline)
    with opt_tab:
        _options_ticket(pf, offline)

    st.header("Everything you hold")
    st.fragment(run_every=None if offline else _refresh_every())(_holdings_view)()

    st.subheader("Order history")
    orders = pf.orders_dataframe()
    if orders.empty:
        st.caption("No trades yet.")
    else:
        st.dataframe(orders.iloc[::-1], hide_index=True, width="stretch")  # newest first
        st.download_button("Download orders (CSV)", orders.to_csv(index=False), "orders.csv", "text/csv")

    with st.expander("Account options"):
        add = st.number_input("Add virtual cash (Rs)", min_value=1000, max_value=10000000, value=10000,
                              step=1000, key="add_amount")
        if st.button("Add cash", key="add_cash"):
            pf.add_funds(add)
            _save(pf)
            st.rerun()
        st.divider()
        restart = st.number_input("Start over with this capital (Rs)", min_value=int(MIN_CAPITAL),
                                  max_value=int(MAX_CAPITAL), value=100000, step=10000, key="restart_amount")
        sure = st.checkbox(f"I want to erase all my trades and start again with {format_inr(restart, 0)}", key="restart_sure")
        if st.button("Reset my account", disabled=not sure, key="restart_go"):
            fresh = Portfolio(balance=check_capital(restart), name=pf.name, created_at=pf.created_at)   # still the same person
            _sign_in(fresh)
            _save(fresh)
            st.rerun()


@guard()
def _account_summary():
    pf = _get_portfolio()
    snap = snapshot_now(pf)
    gain = snap["total"] - pf.deposited
    c1, c2, c3 = st.columns(3)
    c1.metric("Cash available", format_inr(pf.balance))
    c2.metric("Total value of your portfolio", format_inr(snap["total"]))
    c3.metric("Profit / loss so far", format_inr(gain), f"{gain / pf.deposited * 100:+.2f}%")
    st.caption(f"Updated {now_ist():%H:%M:%S} IST. Prices come from Yahoo Finance and can be delayed by a few minutes.")


@guard()
def _positions_view():
    pf = _get_portfolio()
    styled = positions_table(snapshot_now(pf))
    if styled is None:
        st.info("You don't own anything yet. Use the tabs above to buy your first investment.")
    else:
        st.dataframe(styled, hide_index=True, width="stretch")


@guard()
def _holdings_view():
    from core import holdings_ui
    pf = _get_portfolio()
    holdings_ui.render(pf, snapshot_now(pf), key="trade")


# ---------------- stocks, ETFs and bonds ----------------
def _trade_picker(pf, key, universe, default, offline, noun, open_universe=False):
    """Buy or Sell, then choose what: Buy lists the fixed list (plus the company chosen at the top of the page when
    `open_universe` is on, so any NSE or BSE company can be traded); Sell lists only what you own."""
    mode = st.radio("What do you want to do?", ["Buy", "Sell"], horizontal=True, key=f"mode_{key}")
    if mode == "Buy":
        options = list(universe)
        if open_universe and default not in options:
            options.insert(0, default)
        index = options.index(default) if default in options else 0
        symbol = st.selectbox(f"Choose a {noun} (click, then type to search)", options, index=index,
                              format_func=ins.label, key=f"pick_{key}_{default}")      # follows the company chosen at the top
        if open_universe:
            st.caption("To trade a company that is not in this list, search for it at the top of the page; it will "
                       "appear here first. NSE and BSE companies both work.")
    else:
        owned = [s for s in pf.holdings if s in universe or (open_universe and s not in ins.CASH_INSTRUMENTS)]
        if not owned:
            st.info(f"You do not own any {noun}s yet, so there is nothing to sell. Switch to Buy to get started.")
            return
        symbol = st.selectbox(f"Which of your {noun}s?", owned, key=f"sellpick_{key}",
                              format_func=lambda s: f"{ins.name_of(s)}: you own {pf.holdings[s]['quantity']}, "
                                                    f"bought at {format_inr(pf.holdings[s]['avg_price'])}")
    _cash_ticket(pf, symbol, ins.name_of(symbol), None, offline, key, mode)


def _set_qty(key, value):
    st.session_state[f"qty_{key}"] = max(1, int(value))


def _cash_ticket(pf, symbol, name, fallback_price, offline, key, mode):
    """The order form for anything bought like a share. Shows what will happen before the button is pressed."""
    price = price_of(symbol, fallback_price) or spot_price(symbol)
    if not price:
        st.warning("No price is available for this right now. Please try again in a moment.")
        return
    quote = None if offline else live_quote(symbol)
    owned = pf.holdings.get(symbol, {}).get("quantity", 0)
    c1, c2, c3 = st.columns(3)
    move = (f"{(quote['price'] / quote['previous_close'] - 1) * 100:+.2f}% today"
            if quote and quote.get("previous_close") else None)
    c1.metric(name, format_inr(price), move)
    c2.metric("You own", f"{owned} units")
    if owned:
        avg = pf.holdings[symbol]["avg_price"]
        c3.metric("Your gain on it", format_inr((price - avg) * owned), f"{(price / avg - 1) * 100:+.1f}%")
    else:
        c3.metric("Cash available", format_inr(pf.balance))

    qkey = f"qty_{key}"
    limit = owned if mode == "Sell" else int(pf.balance // price)
    if limit < 1:
        st.warning("Not enough cash to buy even one unit. You can add virtual cash under Account options below."
                   if mode == "Buy" else "You do not own any of this.")
        return
    if st.session_state.get(qkey, 1) > limit:        # the choice changed: keep the number inside what is allowed
        st.session_state[qkey] = limit

    if mode == "Buy":
        st.write("How much do you want to spend? Pick a quick amount or type your own.")
        cols = st.columns(4)
        for col, amount in zip(cols, (5000, 10000, 25000, 50000)):
            col.button(f"Rs {amount:,}", key=f"amt_{key}_{amount}", width="stretch", disabled=amount < price,
                       on_click=_set_qty, args=(key, min(limit, amount // price)))
    else:
        st.write("How much do you want to sell?")
        cols = st.columns(4)
        for col, (text, share) in zip(cols, (("Quarter", 0.25), ("Half", 0.5), ("Three quarters", 0.75), ("All of it", 1.0))):
            col.button(text, key=f"sh_{key}_{text}", width="stretch", on_click=_set_qty, args=(key, owned * share))
    qty = st.number_input("Number of units", min_value=1, max_value=limit, step=1, key=qkey)

    if mode == "Buy":
        st.info(f"You will pay about **{format_inr(qty * price)}** for **{qty}** unit(s) of {name}. "
                f"Cash left after: {format_inr(pf.balance - qty * price)}.")
    else:
        pnl = (price - pf.holdings[symbol]["avg_price"]) * qty
        st.info(f"You will receive about **{format_inr(qty * price)}** for **{qty}** unit(s). "
                f"That locks in a {'profit' if pnl >= 0 else 'loss'} of **{format_inr(abs(pnl))}**.")

    if st.button(f"{mode} {qty} unit(s)", type="primary", width="stretch", key=f"go_{key}"):
        # Trades use a FRESH price (not the 15-second cache), so the order is as accurate as possible.
        fresh = None if offline else get_latest_price(symbol)
        exec_price = round(fresh, 2) if fresh else price
        try:
            order = (pf.buy(symbol, int(qty), exec_price) if mode == "Buy"
                     else pf.sell(symbol, int(qty), exec_price))
            _save(pf)
            verb = "Bought" if mode == "Buy" else "Sold"
            extra = f" Profit/loss on this sale: {format_inr(order['pnl'])}." if mode == "Sell" else ""
            st.session_state.flash = ("ok", f"{verb} {qty} of {name} at {format_inr(exec_price)}.{extra}")
        except TradingError as e:
            st.session_state.flash = ("error", str(e))
        st.rerun()


# ---------------- futures ----------------
def _fmt_expiry(d):
    return d.strftime("%d %b %Y")


def _futures_ticket(pf, offline):
    st.markdown(DERIVATIVES_NOTE)
    c1, c2 = st.columns(2)
    under = c1.selectbox("Underlying", ins.FNO_UNDERLYINGS, format_func=ins.name_of, key="fut_under")
    expiry = c2.selectbox("Expiry", dv.expiry_dates(), format_func=_fmt_expiry, key="fut_exp")
    side = st.radio("Direction", ["LONG", "SHORT"], horizontal=True, key="fut_side",
                    format_func=lambda s: "Long: profit if the price rises" if s == "LONG"
                    else "Short: profit if the price falls")
    lots = st.number_input("Number of lots", min_value=1, value=1, step=1, key="fut_lots")

    spot = spot_price(under)
    if not spot:
        st.warning("No price is available for this right now.")
        return
    if not live_quote(under):
        notice("A live price is not available right now, so the last saved closing price is being used.")
    price = dv.future_price(spot, dv.years_left(expiry))
    lot = dv.lot_size(spot)
    margin = dv.margin_for_future(price, lots)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Spot price", format_inr(spot))
    m2.metric("Futures price (calculated)", format_inr(price))
    m3.metric("One lot", f"{lot} units")
    m4.metric("Margin to block", format_inr(margin))
    st.caption(f"Contract value: {format_inr(price * lot * lots)}. Only the margin ({dv.FUTURES_MARGIN * 100:.0f}% of the "
               "contract value) is set aside. Profit and loss are credited or debited in cash when you close the position.")

    if st.button("Open position", type="primary", key="fut_open"):
        fresh = None if offline else get_latest_price(under)
        spot_now = fresh or spot
        price_now = dv.future_price(spot_now, dv.years_left(expiry))
        try:
            pf.open_future(under, expiry, side, int(lots), price_now, dv.lot_size(spot_now), dv.FUTURES_MARGIN)
            _save(pf)
            st.session_state.flash = ("ok", f"Opened a {side.lower()} position in {ins.name_of(under)} futures "
                                      f"({lots} lot(s)) at {format_inr(price_now)}.")
        except TradingError as e:
            st.session_state.flash = ("error", str(e))
        st.rerun()

    st.subheader("Your open futures")
    st.fragment(run_every=None if offline else _refresh_every())(_open_derivatives)("FUT")
    know_how_button("kh_futures", "Futures", (
        "**What a future is.** An agreement to buy (long) or sell (short) something at a set price on a set date. "
        "You do not pay the full value up front, only a margin.\n\n"
        "**How the price is calculated here.**\n"
        "1. Spot price = the live price of the share or index.\n"
        "2. Futures price = spot x e^(r x time to expiry), with r = 6.5% a year. This 'cost of carry' is why futures "
        "usually trade slightly above spot.\n"
        "3. One lot = a number of units chosen so that a lot is worth about Rs 2 lakh (real lot sizes are set by the "
        "exchange and are larger).\n"
        "4. Margin = 15% of the contract value, set aside from your cash.\n\n"
        "**Profit or loss.** Long: (current futures price - entry price) x units. Short: the reverse. It is added to or "
        "taken from your cash when you close.\n\n"
        "**Expiry.** Monthly contracts expire on the last Tuesday of the month at 3:30 PM. Open positions are settled "
        "automatically at that day's closing price.\n\n"
        "**Automatic closing.** If losses use up the whole margin, the position is closed for you. In this learning "
        "version, losses beyond the margin are not charged.\n\n"
        "**Risks.** Futures are leveraged: small price moves cause large gains or losses compared with the margin "
        "paid. Real futures can lose more than the margin."))


# ---------------- options ----------------
def _options_ticket(pf, offline):
    st.markdown(DERIVATIVES_NOTE)
    c1, c2, c3 = st.columns(3)
    under = c1.selectbox("Underlying", ins.FNO_UNDERLYINGS, format_func=ins.name_of, key="opt_under")
    expiry = c2.selectbox("Expiry", dv.expiry_dates(), format_func=_fmt_expiry, key="opt_exp")
    kind = c3.radio("Type", ["CALL", "PUT"], horizontal=True, key="opt_kind",
                    format_func=lambda k: "Call: gains if the price rises" if k == "CALL" else "Put: gains if the price falls")

    spot = spot_price(under)
    if not spot:
        st.warning("No price is available for this right now.")
        return
    if not live_quote(under):
        notice("A live price is not available right now, so the last saved closing price is being used.")
    strikes, atm = dv.strike_grid(spot)
    strike = st.selectbox("Strike price", strikes, index=strikes.index(atm), key="opt_strike",
                          format_func=lambda k: f"{k:g}" + ("  (at the money)" if k == atm else ""))
    lots = st.number_input("Number of lots", min_value=1, value=1, step=1, key="opt_lots")

    sigma = vol_estimate(under) or 0.25
    years = dv.years_left(expiry)
    premium = dv.option_price(spot, strike, years, sigma, kind)
    lot = dv.lot_size(spot)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Spot price", format_inr(spot))
    m2.metric("Premium per unit (calculated)", format_inr(premium))
    m3.metric("One lot", f"{lot} units")
    m4.metric("Total cost", format_inr(premium * lot * lots))
    breakeven = strike + premium if kind == "CALL" else strike - premium
    st.caption(f"The most you can lose is the premium paid. Break-even at expiry: {breakeven:,.2f}.")

    if st.button("Buy option", type="primary", key="opt_buy"):
        fresh = None if offline else get_latest_price(under)
        spot_now = fresh or spot
        prem_now = dv.option_price(spot_now, strike, dv.years_left(expiry), sigma, kind)
        try:
            pf.buy_option(under, expiry, strike, kind, int(lots), prem_now, dv.lot_size(spot_now))
            _save(pf)
            st.session_state.flash = ("ok", f"Bought {lots} lot(s) of the {ins.name_of(under)} {strike:g} {kind.lower()} "
                                      f"at {format_inr(prem_now)} per unit.")
        except TradingError as e:
            st.session_state.flash = ("error", str(e))
        st.rerun()
    st.caption("Only buying options is available. Selling (writing) options carries much larger risk and is not included.")

    st.subheader("Your open options")
    st.fragment(run_every=None if offline else _refresh_every())(_open_derivatives)("OPT")
    know_how_button("kh_options", "Options", (
        "**What an option is.** The right, but not the obligation, to buy (call) or sell (put) at a fixed price (the "
        "strike) on or before a date. You pay a price for that right: the premium.\n\n"
        "**How the premium is calculated here.** The Black-Scholes formula, which uses: the live price (spot), the "
        "strike, the time left, the safe interest rate (6.5%), and the stock's volatility over the last year. "
        "More time, higher volatility, or a strike closer to the price all make an option dearer. "
        "A real market price also reflects demand and traders' views, so it will differ.\n\n"
        "**Lot size.** Chosen so one lot is worth about Rs 2 lakh (the exchange fixes real lot sizes).\n\n"
        "**Profit or loss.** You can sell the option at any time at its current calculated premium. At expiry a call is "
        "worth max(price - strike, 0) per unit and a put is worth max(strike - price, 0). If that is zero, the option "
        "expires worthless and the premium is lost.\n\n"
        "**Expiry.** The last Tuesday of the month at 3:30 PM. Open options are settled automatically at that day's "
        "closing price.\n\n"
        "**Risks.** Options can lose all of the premium quickly, especially close to expiry."))


@guard()
def _open_derivatives(kind):
    """List open futures ('FUT') or options ('OPT') with a Close/Sell button for each."""
    pf = _get_portfolio()
    mine = [p for p in pf.derivatives if p["type"] == kind]
    if not mine:
        st.caption("None open.")
        return
    for pos in mine:
        spot = spot_price(pos["underlying"])
        under = ins.name_of(pos["underlying"])
        if kind == "FUT":
            mark = val.mark_future(pos, spot) if spot else {"price": pos["entry"], "pnl": 0.0, "value": pos["margin"]}
            text = f"{under} future, {pos['side'].lower()}, {pos['lots']} lot(s), expires {pos['expiry']}"
            detail = f"Entry {format_inr(pos['entry'])}  |  Now {format_inr(mark['price'])}"
            label = "Close position"
        else:
            sigma = vol_estimate(pos["underlying"])
            mark = (val.mark_option(pos, spot, sigma) if spot and sigma else
                    {"price": pos["premium"], "pnl": 0.0, "value": pos["premium"] * pos["lot_size"] * pos["lots"]})
            text = f"{under} {pos['strike']:g} {pos['kind'].lower()}, {pos['lots']} lot(s), expires {pos['expiry']}"
            detail = f"Paid {format_inr(pos['premium'])}  |  Now {format_inr(mark['price'])} per unit"
            label = "Sell"
        c1, c2, c3 = st.columns([4, 2, 1.3])
        c1.markdown(f"**{text}**  \n{detail}")
        colour = "#2a9d6f" if mark["pnl"] >= 0 else "#c8553d"
        c2.markdown(f'Value {format_inr(mark["value"])}  \n<span style="color:{colour}">Profit/loss {format_inr(mark["pnl"])}</span>',
                    unsafe_allow_html=True)
        if c3.button(label, key=f"close_{pos['id']}"):
            try:
                fresh = get_latest_price(pos["underlying"]) or spot
                if kind == "FUT":
                    price_now = val.mark_future(pos, fresh)["price"] if fresh else pos["entry"]
                    pnl = pf.close_future(pos["id"], price_now)
                else:
                    sigma = vol_estimate(pos["underlying"]) or 0.25
                    prem_now = val.mark_option(pos, fresh, sigma)["price"] if fresh else pos["premium"]
                    pnl = pf.sell_option(pos["id"], prem_now)
                _save(pf)
                st.session_state.flash = ("ok", f"Closed {text}. Profit/loss: {format_inr(pnl)}.")
            except TradingError as e:
                st.session_state.flash = ("error", str(e))
            st.rerun()
