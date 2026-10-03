"""Plotly charts. Plotly charts are interactive: hover, zoom, drag, double-click to reset."""
import plotly.graph_objects as go

from core import indicators as ind
from core import simulation as sim

# Colours chosen to stay readable on a projector
BLUE, ORANGE, PURPLE, GREY = "#1f77b4", "#ff7f0e", "#7b2cbf", "#888888"


def price_chart(hist, symbol, name):
    """Candlesticks + 50/200-day averages + Bollinger Bands.

    `hist` must contain enough earlier history for the averages to be warmed up;
    the caller decides how much to *show* via x-axis range (see app.py).
    """
    close = hist["Close"]
    ma50, ma200 = ind.sma(close, 50), ind.sma(close, 200)
    _, upper, lower = ind.bollinger(close)

    fig = go.Figure()

    # Bollinger Bands: draw the lower line first, then the upper line filled down to it.
    fig.add_trace(go.Scatter(x=hist.index, y=lower, line=dict(width=0),
                             showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=hist.index, y=upper, line=dict(width=0), fill="tonexty",
                             fillcolor="rgba(120,120,120,0.15)", name="Bollinger Bands (20-day, 2 SD)",
                             hoverinfo="skip"))

    fig.add_trace(go.Candlestick(x=hist.index, open=hist["Open"], high=hist["High"],
                                 low=hist["Low"], close=close, name="Price",
                                 increasing_line_color="#2e9e5b", decreasing_line_color="#d64545"))
    fig.add_trace(go.Scatter(x=hist.index, y=ma50, name="50-day average",
                             line=dict(color=ORANGE, width=2.5)))
    fig.add_trace(go.Scatter(x=hist.index, y=ma200, name="200-day average",
                             line=dict(color=PURPLE, width=2.5)))

    fig.update_layout(
        title=dict(text=f"{name} ({symbol})", font=dict(size=24)),
        height=560,
        font=dict(size=16),
        xaxis_rangeslider_visible=False,
        yaxis=dict(title="Price (Rs)", tickprefix="Rs "),
        legend=dict(orientation="h", y=-0.12),
        margin=dict(l=10, r=10, t=60, b=10),
        hovermode="x unified",
    )
    return fig


def fan_chart(hist, paths, calendar_days, symbol, name):
    """Fan chart: recent real prices, then shaded bands that widen into the future.

    Darker band = more likely region (50% of futures), lighter = wider (90%).
    """
    recent = hist["Close"].iloc[-90:]  # last ~4 months of real prices for context
    dates = sim.future_dates(recent.index[-1], paths.shape[1] - 1)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=recent.index, y=recent, name="Past price",
                             line=dict(color=BLUE, width=3)))

    # Widest band first so narrower ones draw on top of it.
    for prob, shade in [(0.90, "rgba(31,119,180,0.15)"), (0.70, "rgba(31,119,180,0.30)"),
                        (0.50, "rgba(31,119,180,0.45)")]:
        low, high = sim.band(paths, prob)
        fig.add_trace(go.Scatter(x=dates, y=low, line=dict(width=0), showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=dates, y=high, line=dict(width=0), fill="tonexty", fillcolor=shade,
                                 name=f"{int(prob * 100)}% of simulated futures",
                                 hovertemplate="Rs %{y:,.0f}<extra>upper edge</extra>"))

    fig.add_trace(go.Scatter(x=dates, y=sim.band(paths, 0.0)[0], name="Middle (median)",
                             line=dict(color="black", width=2, dash="dash")))

    fig.update_layout(
        title=dict(text=f"{name}: possible price paths over the next {calendar_days} days",
                   font=dict(size=22)),
        height=500, font=dict(size=16),
        yaxis=dict(title="Price (Rs)", tickprefix="Rs "),
        legend=dict(orientation="h", y=-0.15),
        margin=dict(l=10, r=10, t=60, b=10), hovermode="x unified",
    )
    return fig


def backtest_chart(result):
    """Two lines showing what Rs 1,00,000 would have become, with buy/sell markers."""
    eq = result["equity"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=eq.index, y=eq["Buy and hold"], name="Buy and hold",
                             line=dict(color=GREY, width=3)))
    fig.add_trace(go.Scatter(x=eq.index, y=eq["Crossover strategy"], name="50/200-day crossover",
                             line=dict(color=ORANGE, width=3)))
    # Triangles on the strategy line where it bought (up, green) and sold (down, red).
    for dates, symbol_, colour, label in [(result["buys"], "triangle-up", "#2e9e5b", "Buy signal"),
                                          (result["sells"], "triangle-down", "#d64545", "Sell signal")]:
        if len(dates):
            fig.add_trace(go.Scatter(x=dates, y=eq.loc[dates, "Crossover strategy"], mode="markers",
                                     name=label, marker=dict(symbol=symbol_, size=14, color=colour)))
    fig.update_layout(
        height=480, font=dict(size=16), yaxis=dict(title="Portfolio value (Rs)", tickprefix="Rs "),
        legend=dict(orientation="h", y=-0.15), margin=dict(l=10, r=10, t=30, b=10), hovermode="x unified",
    )
    return fig
