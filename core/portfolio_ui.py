"""The "Your Portfolio" tab: live dashboard, portfolio builder, leaderboard and organiser tools."""
import json

import pandas as pd
import streamlit as st

from core import accounts as acc
from core import builder
from core import derivatives as dv
from core import instruments as ins
from core import valuation as val
from core.charts import allocation_donut
from core.formatting import format_inr, format_ist
from core.live import spot_price, vol_estimate
from core.market_hours import now_ist
from core.trading import Portfolio
from core.trading_ui import (_get_portfolio, _refresh_every, _save, _sign_out, admin_pin, get_store,
                             positions_table, snapshot_now, storage_diagnosis)
from core.ui import callout, know_how_button, notice, plain_english

ETF_OPTIONS = [s for s in ins.CASH_INSTRUMENTS if ins.asset_class(s) == ins.ETFS]
BOND_OPTIONS = [s for s in ins.CASH_INSTRUMENTS if ins.asset_class(s) == ins.BONDS]
STOCK_OPTIONS = [s for s in ins.CASH_INSTRUMENTS if ins.asset_class(s) == ins.STOCKS]


@st.cache_data(ttl=10, show_spinner=False)
def _all_accounts(_store):
    """Every saved account (cached for 10 seconds so the leaderboard stays quick)."""
    return _store.all()


def render():
    pf = _get_portfolio()
    st.header(f"Your portfolio: {pf.name}")
    st.caption("Your own paper-trading portfolio. It is saved under your name, so you can come back later and see how it did.")

    st.fragment(run_every=_refresh_every())(_dashboard)()

    with st.expander("Build or add to my portfolio", expanded=not pf.holdings and not pf.derivatives):
        _builder(pf)

    st.header("Leaderboard")
    st.caption("Everyone's portfolio, ranked by return since they started.")
    st.fragment(run_every=_refresh_every())(_leaderboard)()

    _lookup()
    _organiser_tools()

    plain_english(
        "- **Your portfolio** adds up everything you own, plus your cash, at today's prices.\n"
        "- The **ring chart** shows how your money is spread across stocks, ETFs, bonds, futures, options and cash. "
        "Spreading money across different kinds of investments is called diversification.\n"
        "- **Return** is how much your total has grown or shrunk compared with the money you started with.\n"
        "- The **leaderboard** compares everyone's return, so a bigger portfolio does not automatically win.")


# ---------------- dashboard (updates live) ----------------
def _dashboard():
    pf = _get_portfolio()
    snap = snapshot_now(pf)
    gain = snap["total"] - pf.deposited
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Portfolio value", format_inr(snap["total"]))
    c2.metric("Profit / loss", format_inr(gain), f"{snap['return_pct']:+.2f}%")
    c3.metric("Started with", format_inr(pf.deposited))
    c4.metric("Cash", format_inr(pf.balance))
    left, right = st.columns([0.8, 1.8])
    with left:
        st.subheader("Where your money is")
        if snap["total"] > 0:
            st.plotly_chart(allocation_donut(snap["by_class"]), width="stretch")
    with right:
        st.subheader("What you hold")
        styled = positions_table(snap)
        if styled is None:
            st.info("You hold only cash so far. Use the builder below, or the Paper trading tab, to invest.")
        else:
            st.dataframe(styled, hide_index=True, width="stretch")
    st.caption(f"Updated {now_ist():%H:%M:%S} IST. Prices can be delayed by a few minutes. "
               "Futures and options values are calculated, not exchange quotes.")


# ---------------- builder ----------------
def _builder(pf):
    st.caption(f"Cash available to invest: **{format_inr(pf.balance)}**. Choose how much of it goes into each kind of "
               "investment and which ones. Money is split equally between the ones you pick in each group, and "
               "anything that cannot be bought in whole units stays as cash.")

    st.markdown("**1. How much in each?** (the rest stays as cash)")
    cols = st.columns(5)
    alloc = {}
    defaults = {ins.STOCKS: 40, ins.ETFS: 20, ins.BONDS: 20, ins.FUTURES: 0, ins.OPTIONS: 0}
    for col, cls in zip(cols, builder.BUILDER_CLASSES):
        alloc[cls] = col.slider(cls, 0, 100, defaults[cls], step=5, key=f"alloc_{cls}", format="%d%%")
    total_pct = sum(alloc.values())
    if total_pct > 100:
        st.error(f"These add up to {total_pct}%, which is more than 100%. Please reduce some of them.")
        return
    st.caption(f"Invested: {total_pct}%   |   Kept as cash: {100 - total_pct}%")

    st.markdown("**2. Which ones?**")
    picks = {}
    if alloc[ins.STOCKS]:
        picks[ins.STOCKS] = st.multiselect("Stocks", STOCK_OPTIONS, default=["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS"],
                                           format_func=ins.label, key="pick_stocks")
    if alloc[ins.ETFS]:
        picks[ins.ETFS] = st.multiselect("ETFs", ETF_OPTIONS, default=["NIFTYBEES.NS", "GOLDBEES.NS"],
                                         format_func=ins.label, key="pick_etfs")
    if alloc[ins.BONDS]:
        picks[ins.BONDS] = st.multiselect("Bonds", BOND_OPTIONS, default=["EBBETF0430.NS"],
                                          format_func=ins.label, key="pick_bonds")
    if alloc[ins.FUTURES]:
        under = st.multiselect("Futures: underlyings", ins.FNO_UNDERLYINGS, default=["^NSEI"],
                               format_func=ins.name_of, key="pick_fut")
        side = st.radio("Futures direction", ["LONG", "SHORT"], horizontal=True, key="pick_fut_side",
                        format_func=lambda s: "Long (profit if prices rise)" if s == "LONG" else "Short (profit if prices fall)")
        picks[ins.FUTURES] = [(u, side) for u in under]
    if alloc[ins.OPTIONS]:
        under = st.multiselect("Options: underlyings", ins.FNO_UNDERLYINGS, default=["RELIANCE.NS"],
                               format_func=ins.name_of, key="pick_opt")
        kind = st.radio("Option type", ["CALL", "PUT"], horizontal=True, key="pick_opt_kind",
                        format_func=lambda k: "Call (gains if prices rise)" if k == "CALL" else "Put (gains if prices fall)")
        picks[ins.OPTIONS] = [(u, kind) for u in under]
        st.caption("Options are bought at the strike nearest the current price, expiring at the nearest month-end.")

    # ---- preview ----
    symbols = {(i[0] if isinstance(i, tuple) else i) for items in picks.values() for i in items}
    prices = {s: spot_price(s) for s in symbols}
    sigmas = {s: vol_estimate(s) for s in symbols if s in ins.FNO_UNDERLYINGS}
    plan = builder.plan_portfolio(pf.balance, alloc, picks, prices, sigmas)

    st.markdown("**3. Preview**")
    if not plan["orders"]:
        st.info("Nothing to buy yet. Choose some investments above, or increase an amount.")
    else:
        table = pd.DataFrame([{"Group": o["class"], "Investment": o["label"], "Quantity": o["detail"],
                               "Price": o["price"], "Cost": o["cost"]} for o in plan["orders"]])
        st.dataframe(table.style.format({"Price": format_inr, "Cost": format_inr}), hide_index=True, width="stretch")
    for line in plan["skipped"]:
        st.caption(line)
    st.caption(f"Total to invest: {format_inr(plan['spent'])}   |   Cash left afterwards: {format_inr(plan['left'])}")

    if plan["orders"] and st.button("Create my portfolio", type="primary", key="build_go"):
        try:
            count = builder.execute_plan(pf, plan)
            _save(pf)
            st.session_state.flash = ("ok", f"Done. {count} investment(s) were added to your portfolio.")
        except Exception as e:                                     # a TradingError or similar: show it plainly
            st.session_state.flash = ("error", str(e))
        st.rerun()

    know_how_button("kh_builder", "Portfolio builder", (
        "**What it does.** It turns your percentages into actual paper trades at today's prices.\n\n"
        "**Steps.**\n"
        "1. Each group gets its percentage of your cash.\n"
        "2. That money is split equally between the investments you picked in the group.\n"
        "3. **Stocks, ETFs and bonds:** buys as many whole units as the money allows.\n"
        "4. **Futures:** the money pays the margin (15% of the contract value); buys as many whole lots as it covers, "
        "using the nearest month-end expiry. Long profits if the price rises, short if it falls.\n"
        "5. **Options:** the money pays the premium for a call or put at the strike nearest today's price, nearest expiry.\n"
        "6. Whatever cannot be bought in whole units stays as cash.\n\n"
        "**Bonds here** are real NSE-traded bond funds (government and PSU bond ETFs, and liquid ETFs) with live prices.\n\n"
        "**Futures and options** prices are calculated with standard formulas because free data for NSE derivatives "
        "does not exist. See the Paper trading tab for details.\n\n"
        "**Diversification.** Spreading money across different kinds of investments reduces the damage if any one of "
        "them does badly. Futures and options are riskier than the others."))


# ---------------- leaderboard (updates live) ----------------
def _ranked(records):
    rows = []
    for rec in records:
        try:
            pf = Portfolio.from_dict(rec["data"])
            snap = val.snapshot(pf, spot_price, vol_estimate)
        except Exception:
            continue
        rows.append({"Name": rec["name"], "Portfolio value": snap["total"], "Return": snap["return_pct"],
                     "Started with": pf.deposited, "Holdings": len(pf.holdings) + len(pf.derivatives)})
    rows.sort(key=lambda r: r["Return"], reverse=True)
    for i, r in enumerate(rows, start=1):
        r["Rank"] = i
    return rows


def _leaderboard():
    me = _get_portfolio().name
    try:
        rows = _ranked(_all_accounts(get_store()))
    except acc.StorageError as e:
        st.error(str(e))
        return
    if not rows:
        st.info("No portfolios yet.")
        return
    df = pd.DataFrame(rows)[["Rank", "Name", "Portfolio value", "Return", "Started with", "Holdings"]]

    def mine(row):
        return ["font-weight: 700; background-color: #eef2f7" if row["Name"] == me else "" for _ in row]

    styled = (df.style.apply(mine, axis=1)
              .format({"Portfolio value": format_inr, "Started with": format_inr, "Return": "{:+.2f}%"}))
    st.dataframe(styled, hide_index=True, width="stretch")
    mine_row = next((r for r in rows if r["Name"] == me), None)
    if mine_row:
        st.caption(f"You are ranked {mine_row['Rank']} of {len(rows)}.")


# ---------------- look up anyone's portfolio ----------------
def _lookup():
    st.header("Look up a portfolio")
    st.caption("See the current value of anyone's portfolio, for example when a visitor comes back at the end of the day.")
    store = get_store()
    try:
        names = store.names()
    except acc.StorageError as e:
        st.error(str(e))
        return
    if not names:
        return
    pick = st.selectbox("Choose a name", names, key="lookup_pick")
    try:
        pf = acc.load_account(store, pick)
    except acc.StorageError as e:
        st.error(str(e))
        return
    if pf is None:
        st.warning("That portfolio could not be found.")
        return
    snap = val.snapshot(pf, spot_price, vol_estimate)
    gain = snap["total"] - pf.deposited
    callout(f"<b>{pf.name}</b> started with <b>{format_inr(pf.deposited)}</b> and the portfolio is now worth "
            f"<b>{format_inr(snap['total'])}</b> ({snap['return_pct']:+.2f}%, {'a profit' if gain >= 0 else 'a loss'} of "
            f"{format_inr(abs(gain))}).")
    left, right = st.columns([1, 1.6])
    with left:
        if snap["total"] > 0:
            st.plotly_chart(allocation_donut(snap["by_class"]), width="stretch", key="lookup_donut")
    with right:
        styled = positions_table(snap)
        if styled is None:
            st.info("This portfolio holds only cash.")
        else:
            st.dataframe(styled, hide_index=True, width="stretch")


# ---------------- organiser tools ----------------
def _organiser_tools():
    store = get_store()
    pin = admin_pin()
    local = isinstance(store, acc.FileStore)
    with st.expander("Organiser tools"):
        problem = storage_diagnosis() if local else None
        if problem:
            st.warning(f"The online database is not connected. {problem} Until it is, portfolios are kept in "
                       "files on the server and will be lost when the app restarts.")
        if pin is None and not local:
            st.info("Organiser tools are switched off. Add an organiser PIN to the app's secrets to use them "
                    "(see DEPLOY.md).")
            return
        if pin is not None:
            entered = st.text_input("Organiser PIN", type="password", key="admin_pin",
                                    help="Type the PIN and press Enter.")
            # forgiving: ignore stray spaces or quote marks that were typed around it
            if entered.strip().strip("\"'“”‘’").strip() != pin.strip():
                st.caption("Type the PIN and press Enter. Use only the characters, without quote marks.")
                return
        try:
            records = store.all()
        except acc.StorageError as e:
            st.error(str(e))
            return

        st.markdown(f"**{len(records)} portfolio(s)** saved in {store.label}.")
        if local:
            st.caption("Note: if this app is running online, portfolios kept in files are lost when the app restarts. "
                       "Set up the online database (see DEPLOY.md) so they are never lost.")
        if records:
            when = pd.DataFrame([{
                "Name": r["name"],
                "First seen (IST)": format_ist((r.get("data") or {}).get("created_at")),
                "Last active (IST)": format_ist(r.get("updated_at")),
            } for r in sorted(records, key=lambda r: str(r.get("updated_at") or ""), reverse=True)])
            st.dataframe(when, hide_index=True, width="stretch")
            st.caption("Last active = the most recent time that portfolio was saved. 'Not recorded' means the account was "
                       "made before first-seen times were tracked.")
        names = sorted((r["name"] for r in records), key=str.casefold)
        if names:
            target = st.selectbox("Delete a portfolio", names, key="admin_target")
            sure = st.checkbox(f"Yes, permanently delete {target}'s portfolio", key="admin_sure")
            if st.button("Delete", disabled=not sure, key="admin_delete"):
                store.delete(acc.make_key(target))
                _all_accounts.clear()
                if target.casefold() == _get_portfolio().name.casefold():
                    _sign_out()
                st.rerun()
        st.divider()
        st.download_button("Download a backup of all portfolios", json.dumps(records, default=str),
                           "portfolios_backup.json", "application/json", key="admin_backup")
        uploaded = st.file_uploader("Restore from a backup file", type="json", key="admin_restore")
        if uploaded is not None and st.button("Restore these portfolios", key="admin_restore_go"):
            try:
                restored = json.load(uploaded)
                for rec in restored:
                    store.put(rec["key"], rec["name"], rec["data"])
                _all_accounts.clear()
                st.success(f"Restored {len(restored)} portfolio(s).")
            except (ValueError, KeyError, TypeError, acc.StorageError) as e:
                st.error(f"That file could not be restored: {e}")
