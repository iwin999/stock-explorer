"""Plotly charts. Plotly charts are interactive: hover, zoom, drag, double-click to reset."""
import plotly.graph_objects as go

from core import indicators as ind
from core import simulation as sim

# Colours chosen to stay readable on a projector
NAVY, AMBER, GREY = "#1d3557", "#d98e04", "#8a93a0"
UP_COLOUR, DOWN_COLOUR = "#2a9d6f", "#c8553d"


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
                             fillcolor="rgba(120,130,145,0.16)", name="Usual price range",
                             hoverinfo="skip"))

    fig.add_trace(go.Candlestick(x=hist.index, open=hist["Open"], high=hist["High"],
                                 low=hist["Low"], close=close, name="Price",
                                 increasing_line_color=UP_COLOUR, decreasing_line_color=DOWN_COLOUR))
    fig.add_trace(go.Scatter(x=hist.index, y=ma50, name="50-day average",
                             line=dict(color=AMBER, width=2.5)))
    fig.add_trace(go.Scatter(x=hist.index, y=ma200, name="200-day average",
                             line=dict(color=NAVY, width=2.5)))

    fig.update_layout(
        title=dict(text=f"{name} ({symbol.replace('.NS', '')})", font=dict(size=22)),
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
                             line=dict(color=NAVY, width=3)))

    # Widest band first so narrower ones draw on top of it.
    for prob, shade in [(0.90, "rgba(29,53,87,0.12)"), (0.70, "rgba(29,53,87,0.24)"),
                        (0.50, "rgba(29,53,87,0.40)")]:
        low, high = sim.band(paths, prob)
        fig.add_trace(go.Scatter(x=dates, y=low, line=dict(width=0), showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=dates, y=high, line=dict(width=0), fill="tonexty", fillcolor=shade,
                                 name=f"{int(prob * 100)}% of simulated outcomes",
                                 hovertemplate="Rs %{y:,.0f}<extra>upper edge</extra>"))

    fig.add_trace(go.Scatter(x=dates, y=sim.band(paths, 0.0)[0], name="Middle outcome (median)",
                             line=dict(color="black", width=2, dash="dash")))

    fig.update_layout(
        title=dict(text=f"{name}: range of possible prices over the next {calendar_days} days",
                   font=dict(size=20)),
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
    fig.add_trace(go.Scatter(x=eq.index, y=eq["Crossover strategy"], name="Moving-average rule",
                             line=dict(color=AMBER, width=3)))
    # Triangles on the strategy line where it bought (up, green) and sold (down, red).
    for dates, symbol_, colour, label in [(result["buys"], "triangle-up", UP_COLOUR, "Buy signal"),
                                          (result["sells"], "triangle-down", DOWN_COLOUR, "Sell signal")]:
        if len(dates):
            fig.add_trace(go.Scatter(x=dates, y=eq.loc[dates, "Crossover strategy"], mode="markers",
                                     name=label, marker=dict(symbol=symbol_, size=14, color=colour)))
    fig.update_layout(
        height=480, font=dict(size=16), yaxis=dict(title="Portfolio value (Rs)", tickprefix="Rs "),
        legend=dict(orientation="h", y=-0.15), margin=dict(l=10, r=10, t=30, b=10), hovermode="x unified",
    )
    return fig


def outlook_gauge(chance_up, calendar_days):
    """Half-circle gauge: how many of the simulated futures end higher than today.

    Left side (red) = mostly falls, right side (green) = mostly rises.
    The needle position is the share of simulated outcomes that ended higher.
    """
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=chance_up * 100,
        number=dict(suffix="%", valueformat=".0f", font=dict(size=54, color="#1b2430")),
        title=dict(text=f"Chance of ending higher in {calendar_days} days", font=dict(size=18)),
        gauge=dict(
            axis=dict(range=[0, 100], tickvals=[0, 25, 50, 75, 100], ticksuffix="%"),
            bar=dict(color=NAVY, thickness=0.28),
            bgcolor="white",
            steps=[dict(range=[0, 40], color="#f3d6cf"),
                   dict(range=[40, 60], color="#e6e9ee"),
                   dict(range=[60, 100], color="#cde8dc")],
        ),
    ))
    fig.update_layout(height=330, margin=dict(l=30, r=30, t=70, b=10), font=dict(size=15))
    return fig


def zoom_to_window(fig, hist, days):
    """Show only the last `days` trading days, with the price axis fitted to that window.

    The averages are calculated on ALL the data (they need the warm-up), but the chart only
    displays the chosen period. Plotly will not re-fit the vertical axis by itself when we
    only set the date range, so we work out the highest and lowest values in view.
    """
    close = hist["Close"]
    _, upper, lower = ind.bollinger(close)
    n = min(days, len(hist))
    view = slice(len(hist) - n, None)
    lows = [hist["Low"].iloc[view].min(), lower.iloc[view].min(),
            ind.sma(close, 50).iloc[view].min(), ind.sma(close, 200).iloc[view].min()]
    highs = [hist["High"].iloc[view].max(), upper.iloc[view].max(),
             ind.sma(close, 50).iloc[view].max(), ind.sma(close, 200).iloc[view].max()]
    low = min(v for v in lows if v == v)     # v == v is False for NaN, so NaNs are skipped
    high = max(v for v in highs if v == v)
    pad = (high - low) * 0.05
    fig.update_xaxes(range=[hist.index[-n], hist.index[-1]])
    fig.update_yaxes(range=[low - pad, high + pad])
    return fig
