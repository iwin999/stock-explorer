"""The price chart with its period, Fibonacci and Dark chart controls, shared by the Overview tab and the Terminal view."""
import streamlit as st

from core import indicators as ind
from core.charts import add_fibonacci, price_chart, show as show_chart, zoom_to_window
from core.ui import help_bubble

PERIODS = {"6 months": 126, "1 year": 252, "2 years": 504, "5 years": 1260}


def render(hist, symbol, name, header=True, height=None, explain=True, compact=False):
    """Draw the chart and its controls. compact=True puts the controls in one tidy bar (period buttons and two switches)."""
    if header:
        st.header("Price history")
    if compact:
        with st.container(key="tm_chartbar"):
            c1, c2, c3 = st.columns([3.6, 1.5, 1.5], vertical_alignment="center")
            choice = c1.segmented_control("Period", list(PERIODS), default="1 year", key="period_seg", label_visibility="collapsed")
            period = choice or "1 year"
            show_fib = c2.toggle("Fibonacci", key="show_fib",
                                 help="Draws the Fibonacci retracement and extension lines from the highest and lowest price in the period you are viewing.")
            dark_chart = c3.toggle("Dark chart", key="dark_chart", help="Turns just this chart dark, whatever the rest of the site looks like.")
    else:
        p1, p2, p4, p3 = st.columns([5, 3, 2, 1])
        period = p1.radio("Period", list(PERIODS), index=1, horizontal=True)
        show_fib = p2.checkbox("Show Fibonacci levels", key="show_fib",
                               help="Draws the Fibonacci retracement lines (23.6%, 38.2%, 50%, 61.8%, 78.6%) and the extension lines (127.2%, 161.8%) from the highest and lowest price in the period you are viewing.")
        dark_chart = p4.toggle("Dark chart", key="dark_chart",
                               help="Turns just this price chart into a dark trading screen, whatever the rest of the site looks like.")
        with p3:
            help_bubble("fibonacci")

    fig = price_chart(hist, symbol, name)
    if height:
        fig.update_layout(height=height)
    fib = ind.fibonacci_levels(hist, PERIODS[period]) if show_fib else None
    if show_fib:
        add_fibonacci(fig, fib)
    extra = [price for _, price in fib["extensions"]] if fib else ()      # keep the extension lines inside the chart
    fig = zoom_to_window(fig, hist, PERIODS[period], include=extra)
    show_chart(fig, dark=dark_chart)
    if show_fib:
        st.info(ind.describe_fibonacci(fib) + " They depend on the period chosen and are a visual guide, not a prediction.")
    if explain:
      st.caption("Each bar is one trading day. The amber and navy lines are the average price over the last 50 and "
                 "200 days; they smooth out day-to-day noise. The grey band is the price's usual range, and it "
                 "widens when the price is moving more. The bars underneath are volume, the number of shares traded each day "
                 "(green on days the price rose, red when it fell); the grey line is the usual level. Tall bars mean a busy day.")

