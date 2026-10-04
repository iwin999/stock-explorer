"""The 'How each holding is doing' section, shown in Paper trading and Your Portfolio."""
import plotly.graph_objects as go
import streamlit as st

from core import holdings as hd
from core import indicators as ind
from core import instruments as ins
from core.errors import guard
from core.formatting import format_inr
from core.live import _closes, live_quote
from core.ui import callout


def contribution_chart(df):
    """Horizontal bars: how many points each holding added to (green) or took off (red) the total return."""
    data = df.sort_values("Contribution")
    fig = go.Figure(go.Bar(
        x=data["Contribution"], y=data["Instrument"], orientation="h",
        marker_color=["#2a9d6f" if v >= 0 else "#c8553d" for v in data["Contribution"]],
        text=[f"{v:+.2f}" for v in data["Contribution"]], textposition="outside",
        hovertemplate="%{y}: %{x:+.2f} points<extra></extra>"))
    fig.update_layout(height=max(160, 46 * len(data) + 70), margin=dict(l=0, r=30, t=10, b=0), showlegend=False,
                      xaxis_title="Points added to (or taken off) your total return", yaxis_title=None,
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    fig.add_vline(x=0, line_color="#8a96a3")
    return fig


def since_buy_chart(closes, since, avg_price, name):
    """Price since the first purchase, with the buy price marked."""
    data = closes[closes.index >= since.strftime("%Y-%m-%d")] if since is not None else closes
    if len(data) < 2:
        data = closes.iloc[-60:]
    fig = go.Figure(go.Scatter(x=data.index, y=data.values, mode="lines", line=dict(color="#1f3a5f", width=2.5),
                               name="Price", hovertemplate="%{x|%d %b %Y}: Rs %{y:,.2f}<extra></extra>"))
    fig.add_hline(y=avg_price, line_dash="dash", line_color="#c8553d",
                  annotation_text=f"You bought at {format_inr(avg_price)}", annotation_position="top left")
    fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), showlegend=False, yaxis_title="Price (Rs)",
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    return fig


@guard()
def render(pf, snap, key):
    """Table, contribution chart and a detail view for one holding."""
    df = hd.analyse(pf, snap, live_quote)
    st.subheader("How each holding is doing")
    if df.empty:
        st.info("Once you buy something, you will see here how each holding is doing and how much it matters to your portfolio.")
        return
    st.caption("**Weight** is its share of your whole portfolio. **Effect on total** is how many percentage points it added "
               "to (or took off) your overall return. Add the effects up and you get your total profit or loss.")
    best_worst = hd.biggest_effects(df)
    if best_worst:
        best, worst = best_worst
        callout(f"Helping most: <b>{best['Instrument']}</b> ({best['Contribution']:+.2f} points). "
                f"Hurting most: <b>{worst['Instrument']}</b> ({worst['Contribution']:+.2f} points).")

    show = df[["Instrument", "Class", "Details", "Value", "P&L", "P&L %", "Today %", "Weight %", "Contribution", "Days held"]]
    st.dataframe(
        show, hide_index=True, width="stretch",
        column_config={
            "Value": st.column_config.NumberColumn("Value", format="Rs %.0f"),
            "P&L": st.column_config.NumberColumn("Profit / loss", format="Rs %.0f"),
            "P&L %": st.column_config.NumberColumn("Gain / loss", format="%+.1f%%"),
            "Today %": st.column_config.NumberColumn("Today", format="%+.2f%%"),
            "Weight %": st.column_config.ProgressColumn("Share of portfolio", format="%.0f%%", min_value=0, max_value=100),
            "Contribution": st.column_config.NumberColumn("Effect on total", format="%+.2f pts"),
            "Days held": st.column_config.NumberColumn("Days held", format="%d"),
        })
    st.plotly_chart(contribution_chart(df), width="stretch", key=f"contrib_{key}")

    pick = st.selectbox("Look closer at one holding", list(df.index),
                        format_func=lambda i: f"{df.loc[i, 'Instrument']}  ({df.loc[i, 'Details']})", key=f"pick_{key}")
    row = df.loc[pick]
    callout(hd.verdict(row))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Value now", format_inr(row["Value"], 0))
    c2.metric("Profit / loss", format_inr(row["P&L"], 0), f"{row['P&L %']:+.1f}%")
    c3.metric("Share of portfolio", f"{row['Weight %']:.1f}%")
    c4.metric("Effect on total return", f"{row['Contribution']:+.2f} pts")

    if row["Class"] in ("Futures", "Options"):
        st.caption("Futures and options are valued by formula, so there is no price chart. Their profit or loss is "
                   "settled when you close them or they expire.")
        return
    closes = _closes(row["Symbol"])
    if closes is None or len(closes) < 30:
        st.caption("A price chart is not available for this right now.")
        return
    first = hd.first_buy_dates(pf).get(row["Symbol"])
    avg = pf.holdings[row["Symbol"]]["avg_price"]
    st.plotly_chart(since_buy_chart(closes, first, avg, row["Instrument"]), width="stretch", key=f"since_{key}")
    trend, trend_note = ind.describe_trend(closes)
    rsi_value, rsi_note = ind.describe_rsi(closes)
    t1, t2 = st.columns(2)
    t1.markdown(f"**Direction: {trend}.** {trend_note}")
    t2.markdown(f"**Recent speed (RSI) {rsi_value}.** {rsi_note}")
    st.caption("These describe the past and are not predictions.")
