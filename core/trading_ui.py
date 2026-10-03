"""The Paper Trading tab. All maths lives in core/trading.py; this file is only the screen."""
import streamlit as st

from core.formatting import format_inr
from core.market_data import get_latest_price
from core.trading import SAVE_TO_DISK, Portfolio, TradingError
from core.ui import notice


@st.cache_data(ttl=60, show_spinner=False)
def live_price(symbol):
    """Latest price, remembered for 60 seconds so clicking around stays fast."""
    price = get_latest_price(symbol)
    return round(price, 2) if price else None


def _get_portfolio():
    """One Portfolio per visitor (per browser tab).

    Local mode (STOCK_APP_SAVE=1): loaded from / saved to data/portfolio.json.
    Cloud mode (default): every visitor starts with their own fresh Rs 1,00,000,
    kept in memory only, so visitors never see each other's trades.
    """
    if "portfolio" not in st.session_state:
        st.session_state.portfolio = Portfolio.load() if SAVE_TO_DISK else Portfolio()
    return st.session_state.portfolio


def _save(pf):
    if SAVE_TO_DISK:
        pf.save()


def _colour_pnl(value):
    return "color: #2e9e5b" if value >= 0 else "color: #d64545"


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

    # ---------- prices for everything we hold, plus the selected stock ----------
    with st.spinner("Getting latest prices..."):
        prices = {s: live_price(s) for s in pf.holdings}
        price = live_price(symbol) or fallback_price  # fall back to the last daily close
    prices[symbol] = prices.get(symbol) or price

    # ---------- account summary ----------
    total = pf.total_value(prices)
    gain = total - pf.deposited
    c1, c2, c3 = st.columns(3)
    c1.metric("Cash available", format_inr(pf.balance))
    c2.metric("Total value (cash + shares)", format_inr(total))
    c3.metric("Profit / loss so far", format_inr(gain), f"{gain / pf.deposited * 100:+.2f}%")

    # ---------- trade box ----------
    st.subheader(f"Trade {name}")
    owned = pf.holdings.get(symbol, {}).get("quantity", 0)
    st.write(f"Price now: **{format_inr(price)}** per share  |  You own: **{owned}** share(s)")
    st.caption("Prices come from Yahoo Finance and can be delayed. When the market is closed you see the last close.")

    qty = st.number_input("How many shares?", min_value=1, value=1, step=1, key="qty")
    affordable = int(pf.balance // price) if price else 0
    st.write(f"Cost of {qty} share(s): **{format_inr(qty * price)}**  (you can afford up to {affordable})")

    buy_col, sell_col = st.columns(2)
    action = None
    if buy_col.button("Buy", type="primary", width="stretch"):
        action = "BUY"
    if sell_col.button("Sell", width="stretch"):
        action = "SELL"

    if action:
        try:
            order = pf.buy(symbol, int(qty), price) if action == "BUY" else pf.sell(symbol, int(qty), price)
            _save(pf)  # remembered on disk only in local mode
            verb = "Bought" if action == "BUY" else "Sold"
            extra = f" Profit/loss on this sale: {format_inr(order['pnl'])}." if action == "SELL" else ""
            st.session_state.flash = ("ok", f"{verb} {qty} share(s) of {name} at {format_inr(price)}.{extra}")
        except TradingError as e:  # a friendly, readable reason (not enough cash, etc.)
            st.session_state.flash = ("error", str(e))
        st.rerun()

    # ---------- holdings ----------
    st.subheader("Your shares")
    table = pf.holdings_table(prices)
    if table.empty:
        st.info("You don't own any shares yet. Choose a company above and press Buy.")
    else:
        styled = (table.style
                  .format({"Avg Price": format_inr, "Current Price": format_inr, "Value": format_inr,
                           "P&L": format_inr, "P&L %": "{:+.2f}%"})
                  .map(_colour_pnl, subset=["P&L", "P&L %"]))
        st.dataframe(styled, hide_index=True, width="stretch")
        st.caption("To sell, choose that company in the dropdown at the top, then press Sell.")

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
        if st.button("Add Rs 10,000 virtual cash"):
            pf.add_funds(10000)
            _save(pf)
            st.rerun()
        sure = st.checkbox("I want to start over with a fresh Rs 1,00,000")
        if st.button("Reset account", disabled=not sure):
            st.session_state.portfolio = Portfolio()
            _save(st.session_state.portfolio)
            st.rerun()
