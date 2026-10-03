"""The Paper Trading tab and the opening 'choose your capital' screen.

All the maths lives in core/trading.py; this file is only the screen.
Parts of the page are st.fragments: Streamlit re-runs just those parts every
few seconds while the market is open, so prices and profit/loss move live
without reloading the whole page (and without interrupting typing elsewhere).
"""
import os

import streamlit as st

from core.formatting import format_inr
from core.live import REFRESH_SECONDS, live_quote
from core.market_data import get_latest_price
from core.market_hours import is_market_open, now_ist
from core.trading import (DEFAULT_BALANCE, DEFAULT_PATH, MAX_CAPITAL, MIN_CAPITAL, SAVE_TO_DISK,
                          Portfolio, TradingError, check_capital)
from core.ui import notice, show_disclaimer

CAPITAL_PRESETS = [50000, 100000, 500000, 1000000]


# ---------------- account creation ----------------
def has_account():
    """True once the visitor has an account (they chose their capital).

    Local mode (STOCK_APP_SAVE=1): a saved account on disk counts, so the family
    laptop is not asked again every time.
    """
    if "portfolio" in st.session_state:
        return True
    if SAVE_TO_DISK and os.path.exists(DEFAULT_PATH):
        st.session_state.portfolio = Portfolio.load()
        return True
    return False


def capital_gate():
    """The first thing a visitor sees: choose how much virtual money to practise with."""
    st.title("Stock Explorer")
    st.subheader("How much would you like to practise with?")
    st.caption("This is virtual money for paper trading. Nothing real is invested. "
               "You can start over with a different amount at any time.")

    labels = [format_inr(a, 0) for a in CAPITAL_PRESETS] + ["Other amount"]
    choice = st.radio("Starting capital", labels, index=1, horizontal=True)
    if choice == "Other amount":
        amount = st.number_input("Enter your amount (Rs)", min_value=int(MIN_CAPITAL), max_value=int(MAX_CAPITAL),
                                 value=int(DEFAULT_BALANCE), step=10000)
        st.caption(f"{format_inr(amount, 0)}  (between {format_inr(MIN_CAPITAL, 0)} and {format_inr(MAX_CAPITAL, 0)})")
    else:
        amount = CAPITAL_PRESETS[labels.index(choice)]

    if st.button("Start", type="primary"):
        try:
            st.session_state.portfolio = Portfolio(balance=check_capital(amount))
            _save(st.session_state.portfolio)
            st.rerun()
        except TradingError as e:
            st.error(str(e))
    show_disclaimer()


def _get_portfolio():
    return st.session_state.portfolio


def _save(pf):
    if SAVE_TO_DISK:
        pf.save()


def _apply_starting_capital():
    """Runs when the visitor edits the capital box (only shown before the first trade)."""
    try:
        amount = check_capital(st.session_state.start_capital)
        st.session_state.portfolio = Portfolio(balance=amount)
        _save(st.session_state.portfolio)
    except TradingError as e:
        st.session_state.flash = ("error", str(e))


# ---------------- prices ----------------
def price_of(symbol, fallback=None):
    """Latest price (shared 15-second cache), or the fallback if Yahoo can't be reached."""
    quote = live_quote(symbol)
    return round(quote["price"], 2) if quote else fallback


def _refresh_every():
    """Seconds between automatic updates: only while the market is open."""
    return REFRESH_SECONDS if is_market_open() else None


def _colour_pnl(value):
    return "color: #2a9d6f" if value >= 0 else "color: #c8553d"


def _prices_for(pf, symbol, fallback):
    prices = {s: price_of(s) for s in pf.holdings}
    prices[symbol] = prices.get(symbol) or price_of(symbol, fallback)
    return prices


# ---------------- the tab ----------------
def render(symbol, name, fallback_price, offline=False):
    pf = _get_portfolio()

    # A message left by the previous click (we rerun the page after every trade).
    flash = st.session_state.pop("flash", None)
    if flash:
        (st.success if flash[0] == "ok" else st.error)(flash[1])

    st.caption("Practice with **virtual** money. Nothing here is real."
               + ("" if SAVE_TO_DISK else " Your account is private to you and resets when you refresh or close the page."))
    if offline:
        notice("Prices below come from saved data, not live prices.")

    # ---------- account summary + price (updates live) ----------
    st.fragment(run_every=None if offline else _refresh_every())(_account_summary)(symbol, name, fallback_price)

    # ---------- capital can be changed until the first trade ----------
    if not pf.order_history:
        st.number_input("Starting capital (Rs)", min_value=int(MIN_CAPITAL), max_value=int(MAX_CAPITAL),
                        value=int(pf.deposited), step=10000, key="start_capital",
                        on_change=_apply_starting_capital,
                        help="You can change this until you place your first trade.")

    # ---------- trade box ----------
    st.subheader(f"Trade {name}")
    price = price_of(symbol, fallback_price)
    qty = st.number_input("How many shares?", min_value=1, value=1, step=1, key="qty")
    affordable = int(pf.balance // price) if price else 0
    st.write(f"Estimated cost of {qty} share(s): **{format_inr(qty * price)}**  (you can afford up to {affordable})")

    # As on the real Indian market (for normal delivery trades), you can only sell shares you own.
    owned = pf.holdings.get(symbol, {}).get("quantity", 0)
    buy_col, sell_col = st.columns(2)
    action = None
    if buy_col.button("Buy", type="primary", width="stretch"):
        action = "BUY"
    if sell_col.button("Sell", width="stretch", disabled=owned == 0):
        action = "SELL"
    if owned == 0:
        st.caption("Sell is available once you own shares of this company. Shares must be bought before they can be sold.")
    elif qty > owned:
        st.caption(f"You own {owned} share(s) of this company, so you can sell up to {owned}.")

    if action:
        # Trades use a FRESH price (not the 15-second cache), so the order is as accurate as possible.
        exec_price = None if offline else get_latest_price(symbol)
        exec_price = round(exec_price, 2) if exec_price else price
        try:
            order = (pf.buy(symbol, int(qty), exec_price) if action == "BUY"
                     else pf.sell(symbol, int(qty), exec_price))
            _save(pf)  # remembered on disk only in local mode
            verb = "Bought" if action == "BUY" else "Sold"
            extra = f" Profit/loss on this sale: {format_inr(order['pnl'])}." if action == "SELL" else ""
            st.session_state.flash = ("ok", f"{verb} {qty} share(s) of {name} at {format_inr(exec_price)}.{extra}")
        except TradingError as e:  # a friendly, readable reason (not enough cash, etc.)
            st.session_state.flash = ("error", str(e))
        st.rerun()

    # ---------- holdings (updates live) ----------
    st.subheader("Your shares")
    st.fragment(run_every=None if offline else _refresh_every())(_holdings_table)(symbol, fallback_price)

    # ---------- order history ----------
    st.subheader("Order history")
    orders = pf.orders_dataframe()
    if orders.empty:
        st.caption("No trades yet.")
    else:
        st.dataframe(orders.iloc[::-1], hide_index=True, width="stretch")  # newest first
        st.download_button("Download orders (CSV)", orders.to_csv(index=False), "orders.csv", "text/csv")

    # ---------- extras ----------
    with st.expander("Account options"):
        add = st.number_input("Add virtual cash (Rs)", min_value=1000, max_value=10000000, value=10000,
                              step=1000, key="add_amount")
        if st.button("Add cash"):
            pf.add_funds(add)
            _save(pf)
            st.rerun()

        st.divider()
        restart = st.number_input("Start over with this capital (Rs)", min_value=int(MIN_CAPITAL),
                                  max_value=int(MAX_CAPITAL), value=int(DEFAULT_BALANCE), step=10000,
                                  key="restart_amount")
        sure = st.checkbox(f"I want to erase my trades and start again with {format_inr(restart, 0)}")
        if st.button("Reset account", disabled=not sure):
            st.session_state.portfolio = Portfolio(balance=check_capital(restart))
            _save(st.session_state.portfolio)
            st.rerun()


# ---------------- the parts that refresh themselves ----------------
def _account_summary(symbol, name, fallback_price):
    pf = _get_portfolio()
    prices = _prices_for(pf, symbol, fallback_price)
    total = pf.total_value(prices)
    gain = total - pf.deposited
    c1, c2, c3 = st.columns(3)
    c1.metric("Cash available", format_inr(pf.balance))
    c2.metric("Total value (cash + shares)", format_inr(total))
    c3.metric("Profit / loss so far", format_inr(gain), f"{gain / pf.deposited * 100:+.2f}%")
    owned = pf.holdings.get(symbol, {}).get("quantity", 0)
    st.write(f"{name}: **{format_inr(prices[symbol])}** per share  |  You own: **{owned}** share(s)")
    st.caption(f"Updated {now_ist():%H:%M:%S} IST. Prices come from Yahoo Finance and can be delayed by a few minutes.")


def _holdings_table(symbol, fallback_price):
    pf = _get_portfolio()
    table = pf.holdings_table(_prices_for(pf, symbol, fallback_price))
    if table.empty:
        st.info("You don't own any shares yet. Choose a company above and press Buy.")
        return
    styled = (table.style
              .format({"Avg Price": format_inr, "Current Price": format_inr, "Value": format_inr,
                       "P&L": format_inr, "P&L %": "{:+.2f}%"})
              .map(_colour_pnl, subset=["P&L", "P&L %"]))
    st.dataframe(styled, hide_index=True, width="stretch")
    st.caption("To sell, choose that company in the dropdown at the top, then press Sell.")
