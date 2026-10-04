"""The "Market carpet" tab: a map of industries (and, one click deeper, the companies in each industry)."""
from datetime import datetime

import streamlit as st

from core import market_carpet as mc
from core.errors import guard
from core.ui import callout, help_bubble, know_how_button, notice, plain_english

KNOW_HOW = """\
**What it is.** A market carpet is a map of the market. Every industry (or, once you open one, every company) is a tile.
The **size** of a tile shows how large it is. The **colour** shows how it has performed: green for up, red for down, grey
for flat. It is the tool the CMT Level III curriculum (Chapter 2.3, "Combining top-down methods") uses to see which
industries are strong at a glance, before looking at any single company.

**The top-down idea behind it.** Chapter 2 describes a simple three-step method:
1. Work out the **trend of the whole market** and trade with it (see the Nifty 50 on the Overview tab).
2. **Rank the industry groups by strength** and focus on the strongest ones. This tab is that step.
3. Inside a strong group, **open the individual charts**, work out price targets and decide where to act.

**How this tab builds the picture.**
- Data comes from Yahoo Finance's screener, asked separately for each of 11 industries on the **NSE** and the **BSE**.
  Only industries that actually have NSE or BSE companies are shown.
- Each industry's tile is sized by the **combined market capitalisation** of the companies shown (share price x number of
  shares). Each company's tile is sized by its own market capitalisation, so the biggest companies get the biggest tiles.
- Where a company is listed on both exchanges it appears once (the NSE listing); BSE-only companies are added.
- An industry's colour is the **market-cap-weighted average** of its companies' performance: big companies count for more,
  like a stock index.
- Performance can be measured three ways: **Today** (change since yesterday's close), **against the 50-day average**
  (how far the price is above or below its average of the last 50 days, a medium-term trend gauge), and **against the
  200-day average** (the long-term trend gauge). Above its average means an uptrend; below means a downtrend.

**How to use it.**
- Look for the greenest industries, which are the strongest. Note that big green tiles matter more than small ones.
- Click an industry tile to open that industry's own carpet of NSE and BSE companies. Then look for the large tiles
  that are green: large, strong companies in a strong industry. Use "Back to all industries" to return.
- To study a company, search for it at the top of the page and use the other tabs.

**What it cannot tell you.** It shows what has *already* happened. A green tile is not a prediction. Yahoo's industry
labels are broad and sometimes debatable. Each industry shows its largest companies only (the screen says how many are
listed in total), and very small companies are missing. Prices can be delayed by about 15 minutes. The chapter's own
version uses a six-month look-back; the three measures here are the closest ones the free data allows.
"""

PLAIN = (
    "- Imagine a map where every company is a patch of carpet. **Big patch = big company.** **Green = going up, red = going down.**\n"
    "- First you see whole **industries** (banks, technology, energy...). The greenest ones are doing best right now.\n"
    "- **Click an industry** to see the companies inside it, in the same way.\n"
    "- The idea: first find the strong industries, then look for the strong companies inside them.\n"
    "- It shows the past, not the future.")


@st.cache_data(ttl=900, show_spinner=False)
def _load():
    return mc.get_data()


def _clicked_sector(event, data):
    """The industry the visitor clicked on the main carpet (None if nothing was clicked)."""
    try:
        points = event["selection"]["points"]
    except (KeyError, TypeError):
        return None
    names = {mc.SECTORS.get(k, k): k for k in data["sectors"]}
    for p in points:
        for candidate in (p.get("id"), p.get("label"), p.get("customdata")):
            if candidate in data["sectors"]:
                return candidate
            if candidate in names:
                return names[candidate]
    return None


@guard()
def render():
    st.header("Market carpet")
    st.markdown("**In short:** a colourful map of the whole market. Big tiles are big companies, green means going up, red "
                "means going down. Spot the strong industries first, then open one to see its companies.")
    c1, c2 = st.columns([8, 1])
    metric = c1.radio("How should performance be measured?", list(mc.METRICS), format_func=lambda k: mc.METRICS[k][0],
                      horizontal=True, key="carpet_metric")
    with c2:
        help_bubble("market_carpet")

    with st.spinner("Building the market carpet from Yahoo Finance..."):
        data, source = _load()
    if not data:
        notice("The market carpet could not be built right now because market data could not be reached. "
               "Please try again in a moment.")
        return
    if source == "saved":
        asof = datetime.fromisoformat(data["asof"]).strftime("%d %b %Y")
        notice(f"Live data could not be reached, so a saved copy from {asof} is shown. Colours may be out of date.")

    table = mc.sector_table(data, metric)
    best, worst = table.iloc[0], table.iloc[-1]
    label = mc.METRICS[metric][0].lower()
    if best["Performance"] is not None:
        callout(f"Measured <b>{label}</b>, the strongest industry is <b>{best['Industry']}</b> "
                f"({best['Performance']:+.1f}%) and the weakest is <b>{worst['Industry']}</b> ({worst['Performance']:+.1f}%).")

    keys = list(table["Key"])
    nonce = st.session_state.setdefault("carpet_nonce", 0)
    opened = st.session_state.get("carpet_open")
    if opened not in keys:
        opened = None

    if opened is None:
        # ---------- the main carpet: industries only ----------
        st.subheader("Industries")
        st.caption(f"{len(table)} industries that have NSE or BSE companies. Size = combined market value of the "
                   "companies; colour = performance. **Click an industry** to open its own carpet of NSE and BSE companies.")
        pick = st.selectbox("Choose an industry here, or click a tile on the carpet below", ["-"] + keys, format_func=lambda k: "-" if k == "-" else mc.SECTORS.get(k, k),
                            key=f"carpet_pick_{nonce}")
        if pick != "-":
            st.session_state["carpet_open"] = pick
            st.session_state["carpet_nonce"] = nonce + 1
            st.rerun()
        event = st.plotly_chart(mc.carpet(data, metric), width="stretch", on_select="rerun", selection_mode="points",
                                key=f"carpet_main_{nonce}")
        clicked = _clicked_sector(event, data)
        if clicked:
            st.session_state["carpet_open"] = clicked
            st.session_state["carpet_nonce"] = nonce + 1               # a fresh chart next time, so nothing stays selected
            st.rerun()
        st.subheader("Industry ranking (strongest first)")
        show = table.drop(columns=["Key"]).rename(columns={"Performance": f"Performance ({label})"})
        st.dataframe(show, hide_index=True, width="stretch", column_config={
            "Combined size (Rs crore)": st.column_config.NumberColumn(format="%.0f"),
            f"Performance ({label})": st.column_config.NumberColumn(format="%+.2f%%")})
        st.caption("'Companies shown' are the largest companies of the industry on the NSE and BSE together (no company "
                   "twice). 'Listed' is how many the two exchanges list in total.")
    else:
        # ---------- one industry: its own carpet ----------
        info = data["sectors"][opened]
        if st.button("Back to all industries", key="carpet_back"):
            st.session_state["carpet_open"] = None
            st.session_state["carpet_nonce"] = nonce + 1
            st.rerun()
        perf = table.loc[table["Key"] == opened, "Performance"].iloc[0]
        st.subheader(f"{mc.SECTORS.get(opened, opened)} carpet")
        st.caption(f"{len(info['companies'])} companies shown (NSE and BSE together, no company twice) of "
                   f"{info['listed']['NSE']} listed on the NSE and {info['listed']['BSE']} on the BSE. Size = market value; "
                   f"colour = performance {label}. The whole industry is {perf:+.1f}% {label}. BSE-only companies are marked (BSE).")
        st.plotly_chart(mc.carpet(data, metric, opened), width="stretch", key=f"carpet_ind_{opened}_{metric}")
        companies = mc.company_table(data, opened, metric)
        st.dataframe(companies, hide_index=True, width="stretch", column_config={
            "Price": st.column_config.NumberColumn(format="Rs %.2f"),
            "Size (Rs crore)": st.column_config.NumberColumn(format="%.0f"),
            "Performance": st.column_config.NumberColumn(f"Performance ({label})", format="%+.2f%%")})
        st.caption("To study one of these companies, search for it at the top of the page, then use the Overview, "
                   "Strategy tests and Paper trading tabs. This shows what has already happened and is not a prediction.")

    plain_english(PLAIN, "What is a market carpet? (plain English)")
    know_how_button("kh_carpet", "Market carpet", KNOW_HOW)
