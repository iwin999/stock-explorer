"""The Fusion analysis tab (CMT Level III, Chapter 8): the Winner's Circle for one company, a screen of all companies,
and a model-portfolio test. The rules live in core/fusion.py; this file is only the screen."""
import numpy as np
import pandas as pd
import streamlit as st

from core import backtest as bt
from core import fundamentals as fd
from core import fusion as fu
from core import ratios
from core.charts import fusion_chart, stage_bar
from core.companies import to_nse
from core.errors import guard
from core.formatting import format_inr
from core.ui import callout, know_how_button, metric_with_help, notice, plain_english, term_row

CREDIT = "Based on the CMT Level III curriculum, Chapter 8 (D. Lundgren, 8.1; J. Letizia, 8.5)."


@st.cache_resource(show_spinner=False)
def _data():
    """Saved prices and yearly company results for all companies (read once, shared by every visitor)."""
    funds = fd.load()
    prices, bench = fu.load_universe()
    if bench is None or len(prices) < fu.MIN_UNIVERSE or len(funds["companies"]) < fu.MIN_UNIVERSE:
        return None
    tech = fu.build_technicals(prices, bench)
    return {"funds": funds, "prices": prices, "bench": bench, "tech": tech, "asof": bench.index[-1]}


@st.cache_data(show_spinner=False)
def _classified(asof):
    d = _data()
    return fu.classify(asof, d["tech"], d["funds"])


@st.cache_data(show_spinner="Running the model-portfolio test...")
def _backtest(cost_pct):
    d = _data()
    return fu.run_fusion_backtest(d["prices"], d["bench"], d["tech"], d["funds"], cost_pct=cost_pct)


@st.cache_data(ttl=3600, show_spinner=False)
def _rated_alone(symbol, asof):
    """Rate ONE company that is not in the built-in list: fetch its prices and yearly results from Yahoo, then rank it
    against the saved companies. Returns the table row (a Series) or None if Yahoo has too little data."""
    from core import fundamentals as fd
    from core.market_data import get_history_with_source
    d = _data()
    hist, _, _ = get_history_with_source(symbol, "7y")
    if d is None or hist is None or len(hist) < 260:
        return None
    technicals = dict(d["tech"])
    technicals[symbol] = fu.technical_table(hist["Close"], d["bench"])
    funds = {"companies": dict(d["funds"]["companies"])}
    try:
        record = fd.fetch_company(symbol)
    except Exception:
        record = None
    if record:
        funds["companies"][symbol] = record
    table = fu.classify(pd.Timestamp(asof), technicals, funds)
    return table.loc[symbol] if symbol in table.index else None


def rating_row(symbol, asof):
    """(table row, note) for any company. A BSE listing of a built-in company uses its NSE twin's rating."""
    symbol = to_nse(symbol)
    table = _classified(asof)
    if symbol in table.index:
        return table.loc[symbol]
    return _rated_alone(symbol, asof)


def company_row(symbol):
    """The fusion rating of one company as a dict (None if it cannot be rated). Used by the bot too."""
    d = _data()
    if d is None:
        return None
    row = rating_row(symbol, d["asof"])
    if row is None:
        return None
    if row.get("group") != row.get("group"):
        return None
    return {"group": int(row["group"]), "stage_name": row["stage_name"], "verdict": row["verdict"],
            "quality_ok": bool(row.get("quality_ok")), "value_ok": bool(row.get("value_ok"))}


def _num(x, kind):
    if x is None or (isinstance(x, float) and (np.isnan(x))):
        return "n/a"
    if x == np.inf:
        return "loss-making"
    return {"pct": f"{x * 100:.1f}%", "x": f"{x:.1f}", "score": f"{x:.0f} / 100"}[kind]


@guard()
def render(symbol, name):
    st.header("Fusion analysis")
    st.caption("Combine what the price is saying (trend and momentum) with the company's results and valuation, as in the "
               "Winner's Circle. A way to organise ideas, not investment advice. " + CREDIT)
    d = _data()
    if d is None:
        notice("The company results file is missing, so fusion analysis is switched off. Ask the admin to run the "
               "download script (see README).")
        return
    asof = d["asof"]
    st.caption(f"Prices saved up to {asof:%d %b %Y}. Company results are the yearly figures from Yahoo Finance, "
               f"used only {fu.REPORT_LAG_DAYS} days after each year ended.")

    this_tab, screen_tab, test_tab = st.tabs(["This company", "Screen of all companies", "Model portfolio test"])
    with this_tab:
        _this_company(symbol, name, asof)
    with screen_tab:
        _screen(asof)
    with test_tab:
        _model_test()


# ---------------------------------------------------------------- this company
def _this_company(symbol, name, asof):
    with st.spinner(f"Rating {name}..."):
        r = rating_row(symbol, asof)
    if r is None:
        st.info(f"There is not enough price history (or Yahoo could not be reached) to rate {name}.")
        return
    if to_nse(symbol) not in _classified(asof).index:
        st.caption(f"{name} is not in the built-in list, so it was rated just now from Yahoo's prices and yearly results, "
                   "ranked against the saved companies. Results can be missing or incomplete for smaller companies.")
    judged = r.get("group") == r.get("group")      # not NaN

    if judged:
        group = int(r["group"])
        callout(f"<b>{name}</b> is in <b>fusion group {group}</b>. {fu.GROUP_TEXT[group]}")
        c1, c2, c3 = st.columns(3)
        with c1:
            metric_with_help("Fusion group", f"{group}", "fusion_group")
        with c2:
            metric_with_help("Trend stage", r["stage_name"], "trend_stage")
        with c3:
            metric_with_help("Overlay verdict", r["verdict"].split(":")[0], "overlay_verdict")
    else:
        callout(f"<b>{name}</b>: the price side can be rated, but there are not enough published company results to rate "
                "its fundamentals, so it has no group.")

    st.subheader("The three circles")
    a, b, c = st.columns(3)
    with a:
        st.markdown("**1. Price trend and momentum** (not negotiable)")
        st.markdown(f"Status: **{'In the circle' if r['in_circle'] else 'Not in the circle'}**")
        st.write(f"Trend stage: {r['stage_name']}")
        st.write(f"6-month return: {_num(r['ret6'], 'pct')}")
        st.write(f"Versus the Nifty 50: {_num(r['rel6'], 'pct')}")
        st.caption("In the circle = clear uptrend, positive 6-month return, and ahead of the Nifty 50.")
    with b:
        st.markdown("**2. Quality of fundamentals**")
        if judged:
            st.markdown(f"Status: **{'In the circle' if r['quality_ok'] else 'Not in the circle'}**")
            st.write(f"Quality score: {_num(r['F'], 'score')}")
            st.write(f"Revenue growth: {_num(r['revenue_growth'], 'pct')}; profit growth: {_num(r['earnings_growth'], 'pct')}")
            st.write(f"Return on equity: {_num(r['roe'], 'pct')}; operating margin: {_num(r['op_margin'], 'pct')}")
            st.write(f"Debt to equity: {_num(r['debt_equity'], 'x')}")
        else:
            st.write("Not enough data.")
        st.caption("Growth, returns and low debt, ranked against the other companies.")
    with c:
        st.markdown("**3. Valuation**")
        if judged:
            st.markdown(f"Status: **{'In the circle' if r['value_ok'] else 'Not in the circle'}**")
            st.write(f"Valuation score: {_num(r['V'], 'score')}")
            st.write(f"Price to earnings (P/E): {_num(r['pe'], 'x')}")
            st.write(f"Price to book (P/B): {_num(r['pb'], 'x')}")
        else:
            st.write("Not enough data.")
        st.caption("Low P/E and low price-to-book rank higher.")

    if judged:
        st.subheader("Technical overlay: confirm, delay or reject")
        callout(f"<b>{r['verdict']}</b><br>{r['why']}")
        if r["divergence"]:
            notice("The technicals and fundamentals disagree here. The chapter's advice: pay more attention to risk, "
                   "consider smaller positions and tighter stops, and reassess the evidence.")
        st.caption(f"Based on yearly results for the year ended {r['as_of_year']}.")

    plain_english(
        "- Think of three tests a company must pass: **is the market's price trend up and beating the market** (this one is "
        "mandatory), **are the business results good**, and **is the price reasonable for them**.\n"
        "- Group 1 passes all three, group 2 passes the trend and one other, group 3 passes only the trend, and group 4 has "
        "not passed the trend test yet.\n"
        "- The verdict compares the price trend with the fundamentals: if they agree, confirm; if the fundamentals look good "
        "but the price has not moved yet, delay; if neither supports it, reject.\n"
        "- It describes the past and the present. It does not predict the future.")
    know_how_button("kh_fusion_company", "Fusion analysis for one company", (
        f"{CREDIT}\n\n"
        "**The idea.** A price is built from fundamentals (F), valuation (V) and sentiment (S), written P = (F x V)^S. "
        "The price trend is the market's own judgement of all of it, so a fundamental view only pays once the market agrees.\n\n"
        "**The Winner's Circle.** Three circles: price trend and momentum, quality of fundamentals, valuation. The trend circle "
        "is not negotiable. Group 1 = in the trend circle with both other circles; group 2 = with one; group 3 = with neither; "
        "group 4 = outside the trend circle (a watchlist).\n\n"
        "**How each circle is judged here.**\n"
        "1. *Trend and momentum:* a clear uptrend (price above the 200-day average, 50-day above 200-day, and the 200-day "
        "rising), a positive 6-month return, and a 6-month return ahead of the Nifty 50.\n"
        "2. *Quality:* the company is ranked 0-100 against the 119 companies in our list on growth (revenue and profit "
        "growth), returns (return on equity and operating margin) and low debt (skipped for banks and lenders). The average "
        "of the available parts is the quality score; 50 or more passes.\n"
        "3. *Valuation:* ranked 0-100 on low P/E and low price-to-book (loss-making companies rank worst on P/E); 50 or more passes.\n\n"
        "**The overlay (Chapter 8.5).** Group 1 confirms. Group 2 confirms with a caveat. Group 3 is a divergence (trend without "
        "fundamentals). Group 4 with good fundamentals and valuation is a delay (fundamentals fine, price not confirmed). "
        "Otherwise reject. Divergences call for extra risk management.\n\n"
        "**Honest notes.** The chapter's own scores come from its authors' models and their formulas are not published, so "
        "these are open, simple stand-ins in the same spirit. Company results are as Yahoo Finance reports them, and each year "
        f"is used only {fu.REPORT_LAG_DAYS} days after it ended."))


# ---------------------------------------------------------------- screen of all companies
def _screen(asof):
    table = _classified(asof)
    judged = table[table["group"].notna()]
    st.caption(f"Where do all {len(table)} companies stand today? Ranked using only information available at the last saved close.")
    cols = st.columns(5)
    for i, g in enumerate((1, 2, 3, 4)):
        cols[i].metric(f"Group {g}", int((judged["group"] == g).sum()))
    cols[4].metric("Not rated", int(len(table) - len(judged)), help="Not enough published results to rank the fundamentals.")

    st.subheader("How many companies are in each trend stage?")
    st.plotly_chart(stage_bar(table["stage_name"].value_counts().to_dict()), width="stretch")
    up = int((table["stage"] >= 2).sum())
    st.caption(f"{up} of {len(table)} companies ({up / len(table) * 100:.0f}%) are in a clear uptrend or the base of one. "
               "The chapter uses this kind of count to judge how healthy the market's trend is.")

    st.subheader("The list")
    choice = st.radio("Show", ["Group 1", "Group 2", "Group 3", "Group 4", "All rated companies"], horizontal=True, key="fusion_filter")
    shown = judged if choice.startswith("All") else judged[judged["group"] == int(choice[-1])]
    if shown.empty:
        st.info("No companies in this group right now.")
    else:
        from core.companies import NAME_BY_SYMBOL
        out = pd.DataFrame({
            "Company": [NAME_BY_SYMBOL.get(s, s) for s in shown.index],
            "Group": shown["group"].astype(int),
            "Trend stage": shown["stage_name"],
            "Ahead of Nifty (6m)": shown["rel6"],
            "Quality (0-100)": shown["F"],
            "Valuation (0-100)": shown["V"],
            "Verdict": shown["verdict"],
        }).sort_values(["Group", "Quality (0-100)"], ascending=[True, False])
        st.dataframe(out.style.format({"Ahead of Nifty (6m)": "{:+.1%}", "Quality (0-100)": "{:.0f}", "Valuation (0-100)": "{:.0f}"}),
                     hide_index=True, width="stretch")
    plain_english(
        "- This sorts every company in our list into the four groups, using today's trend and the latest published results.\n"
        "- **Group 1** companies are the ones the framework likes best right now; **group 4** are on the watchlist because the "
        "price has not confirmed.\n"
        "- The bar shows how many companies are in clear uptrends versus downtrends: a quick read of the market's health.\n"
        "- It is a way to find ideas to study, not a list of things to buy.")
    know_how_button("kh_fusion_screen", "Fusion screen", (
        f"{CREDIT}\n\n"
        "The chapter describes screening thousands of stocks in minutes by sorting them into trend stages and then asking the "
        "market which ones also have strong fundamentals. This screen does the same for our 119 companies:\n\n"
        "1. Work out each company's trend stage, 6-month return and its lead or lag against the Nifty 50.\n"
        "2. Take its latest published yearly results and rank growth, returns, leverage, P/E and P/B against the others.\n"
        "3. Apply the Winner's Circle to give a group from 1 to 4, then the overlay verdict.\n\n"
        "Rankings are relative: a company can be a poor performer yet rank in the top half if the others are worse."))


# ---------------------------------------------------------------- model portfolio test
def _model_test():
    st.caption("What if a portfolio had been rebuilt each month from the companies in group 1 (or groups 1 and 2), using only "
               "information public at the time?")
    cost = st.number_input("Trading cost on what is bought and sold each month (%)", min_value=0.0, max_value=2.0,
                           value=bt.DEFAULT_COST_PCT, step=0.05, format="%.2f", key="fusion_cost")
    res = _backtest(float(cost))
    if res is None:
        st.info("There is not enough saved data to run the test.")
        return
    s = res["stats"]
    g1, g12, allc, nifty = (s.get(k) for k in ("Group 1 only", "Groups 1 and 2", "All companies (equal weight)", "Nifty 50"))
    callout(f"From {res['start']:%d %b %Y} to {res['end']:%d %b %Y}, a monthly-rebuilt equal-weight portfolio of <b>group 1</b> "
            f"companies turned {format_inr(100000, 0)} into <b>{format_inr(g1['final_value'], 0)}</b> "
            f"({g1['total_return'] * 100:+.1f}%), against {format_inr(allc['final_value'], 0)} ({allc['total_return'] * 100:+.1f}%) "
            f"for owning all the companies equally, and {format_inr(nifty['final_value'], 0)} ({nifty['total_return'] * 100:+.1f}%) "
            "for the Nifty 50.")
    st.plotly_chart(fusion_chart(res["curves"]), width="stretch")

    names = ["Group 1 only", "Groups 1 and 2", "All companies (equal weight)", "Nifty 50"]
    term_row("Measure", None, *names, header=True)
    for label, key in (("Total return", "total_return"), ("Average yearly return", "cagr"), ("Worst fall (max drawdown)", "max_drawdown"),
                       ("Volatility", "volatility"), ("Sharpe ratio", "sharpe"), ("Sortino ratio", "sortino")):
        cells = []
        for n in names:
            v = s[n].get(key)
            cells.append(ratios.describe(key, s[n])[0] if key in ("sharpe", "sortino") else ratios.pct(v, sign=key in ("total_return", "cagr")))
        term_row(label, key, *cells)
    term_row("Average number of companies held", None, *[f"{res['avg_holdings'].get(n, 0):.0f}" if n != "Nifty 50" else "50 (index)" for n in names])

    held = res["latest"]
    now = held[held["group"] == 1]
    from core.companies import NAME_BY_SYMBOL
    st.markdown("**Group 1 companies at the latest rebalance:** " + (", ".join(NAME_BY_SYMBOL.get(x, x) for x in now.index) or "none"))
    notice("Read this as an illustration, not proof. It covers about 3 years, tests only today's listed companies (those that "
           "disappeared are missing, called survivorship bias), uses results as Yahoo reports them now, and the period was "
           "mostly a rising market. The comparison with 'all companies equally' is the fairer one, because the Nifty 50 is "
           "weighted by company size.")
    plain_english(
        "- Each month we sort every company into the four groups, using only what was public that day.\n"
        "- We then pretend to put equal amounts into the group-1 companies, hold them for the month, and repeat.\n"
        "- The lines show what Rs 1,00,000 would have become. Comparing with 'all companies' shows whether the sorting "
        "added anything, and comparing with the Nifty 50 shows how the group did against the market.\n"
        "- A short test on a rising market can flatter any method, so use it to learn how the method behaves.")
    know_how_button("kh_fusion_test", "Fusion model-portfolio test", (
        f"{CREDIT}\n\n"
        "**Method.**\n"
        "1. On the first trading day of each month, rate every company using only information up to that day's close: price "
        f"history, and the latest yearly results that had been public for at least {fu.REPORT_LAG_DAYS} days.\n"
        "2. Place the companies in groups 1 to 4. The model portfolios hold group 1 only, or groups 1 and 2, in equal "
        "amounts. If no company qualifies, the money stays in cash.\n"
        "3. Trade at the **next** trading day's close (a rating is only known after the close), and charge the trading cost on "
        "the amount bought and sold.\n"
        "4. Let the holdings run to the next month, then repeat.\n"
        "5. 'All companies' holds every rated company equally, rebuilt monthly. The Nifty 50 is bought and held.\n\n"
        "**Why only about 3 years.** Free yearly company results go back about four years, and each year counts only once it "
        "was published, so the fundamental part can be tested from about mid-2023.\n\n"
        "**Limits.** Short window, today's listed companies only, results as currently reported, and a mostly rising market. "
        "Past results do not predict future results."))
