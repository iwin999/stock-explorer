"""The price chart with its period, Fibonacci and Dark chart controls, shared by the Overview tab and the Terminal view."""
import streamlit as st

from core import indicators as ind
from core import multi_chart as mc
from core.charts import add_fibonacci, price_chart, show as show_chart, zoom_to_window
from core.ui import help_bubble

PERIODS = {"6 months": 126, "1 year": 252, "2 years": 504, "5 years": 1260}
SHORT = {"6 months": "6M", "1 year": "1Y", "2 years": "2Y", "5 years": "5Y"}


def render(hist, symbol, name, header=True, height=None, explain=True, compact=False):
    """Draw the chart and its controls. compact=True puts the controls in one tidy bar (period buttons and two switches)."""
    if header:
        st.header("Price history")
    if compact:
        return _workspace(hist, symbol, height)
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



def _workspace(hist, symbol, height=None):
    """The dashboard's chart area: one chart, or two or four side by side, each in the timeframe of your choice."""
    short = symbol.replace(".NS", "").replace(".BO", "")
    with st.container(key="tm_chartbar"):
        c_layout, c_tf, c_period, c_fib, c_dark = st.columns([2.75, 2.7, 2.35, 1.55, 1.15], vertical_alignment="center")
        st.session_state.setdefault("mtf_layout", "1 chart")                     # set here (not as a widget default) so the demo can drive it
        st.session_state.setdefault("mtf_tf", "Daily")
        st.session_state.setdefault("period_seg", "1 year")
        layout = c_layout.segmented_control("Charts", ["1 chart", "2 charts", "4 charts"], key="mtf_layout",
                                            label_visibility="collapsed", format_func=lambda x: x[0], help="How many charts to show: 1, 2 or 4") or "1 chart"
        count = {"1 chart": 1, "2 charts": 2, "4 charts": 4}[layout]
        if count == 1:
            tf = c_tf.segmented_control("Timeframe", mc.TIMEFRAMES, key="mtf_tf", label_visibility="collapsed",
                                        format_func={"Daily": "Day", "Weekly": "Week", "Monthly": "Month"}.get) or "Daily"
            period = c_period.segmented_control("Period", list(PERIODS), key="period_seg", label_visibility="collapsed",
                                                format_func=SHORT.get) or "1 year"
        else:
            c_tf.caption("Pick each chart's view above it")
        show_fib = c_fib.toggle("Fibonacci", key="show_fib")
        dark = c_dark.toggle("Dark", key="dark_chart")

    if count == 1:
        fig = mc.figure(hist, short, tf, mc.PERIOD_BARS[tf][period], label=f"{tf} · {period}", show_fib=show_fib,
                        height=height or 520, title_size=18)
        show_chart(fig, dark=dark, key="mtf_chart_1")
        if show_fib:
            fib = ind.fibonacci_levels(mc.resample(hist, tf), mc.PERIOD_BARS[tf][period])
            st.caption(ind.describe_fibonacci(fib) + " A visual guide, not a prediction.")
        return
    names = list(mc.PRESETS)
    each = (height or 520) - 90 if count == 2 else 270
    picks = []
    rows = [st.columns(2)] if count == 2 else [st.columns(2), st.columns(2)]
    cells = [c for row in rows for c in row]
    for i, cell in enumerate(cells):
        default = mc.DEFAULTS[count][i]
        with cell:
            choice = st.selectbox(f"Chart {i + 1}", names, index=names.index(default), key=f"mtf_{count}_{i}", label_visibility="collapsed")
            tf, bars = mc.PRESETS[choice]
            fig = mc.figure(hist, short, tf, bars, label=choice, show_fib=show_fib, height=each, volume=count == 2, title_size=15)
            show_chart(fig, dark=dark, key=f"mtf_chart_{count}_{i}")
