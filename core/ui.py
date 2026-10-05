"""Shared screen pieces: styling, the summary callout and the footer disclaimer."""
import streamlit as st

DISCLAIMER = (
    "This is an educational project and not investment advice. No real money is involved. "
    "The information shown is for learning purposes only, and the creator accepts no "
    "responsibility for any decisions made using it. All investments are subject to market "
    "risk; please understand the consequences before investing. Indicators, simulations and "
    "backtests are based on past data and do not predict future results."
)

# CSS = the styling language of web pages. Sizes are generous for a large screen,
# and the look is deliberately plain: white cards, thin borders, one accent colour.
STYLE_CSS = """
<style>
.stApp, .stApp p, .stApp li, .stApp label { font-size: 1.15rem !important; }
.stApp [data-testid="stCaptionContainer"], .stApp [data-testid="stCaptionContainer"] * { font-size: 1.02rem !important; color: #5b6573; }
input, textarea, [data-baseweb="select"] div { font-size: 1.12rem !important; }

h1 { font-size: 2.6rem !important; font-weight: 700 !important; letter-spacing: -0.5px; }
h2 { font-size: 1.8rem !important; font-weight: 650 !important; margin-top: 0.5rem; }
h3 { font-size: 1.35rem !important; font-weight: 600 !important; }
.stApp a.header-anchor, .stApp [data-testid="stHeaderActionElements"] { display: none !important; }

/* Tabs */
.stApp button[data-baseweb="tab"] p, .stApp [data-testid="stTab"], .stApp [data-testid="stTab"] p { font-size: 1.2rem !important; font-weight: 600; }

/* Metric cards */
.stApp [data-testid="stMetric"] { background: #ffffff; border: 1px solid #e1e5ec; border-radius: 8px; padding: 0.9rem 1.1rem; }
.stApp [data-testid="stMetricValue"], .stApp [data-testid="stMetricValue"] * { font-size: 2.1rem !important; font-weight: 650; }
.stApp [data-testid="stMetricLabel"], .stApp [data-testid="stMetricLabel"] * { font-size: 1.02rem !important; color: #5b6573; }
.stApp [data-testid="stMetricDelta"], .stApp [data-testid="stMetricDelta"] * { font-size: 1.0rem !important; }

/* Buttons */
.stApp .stButton button p, .stApp .stDownloadButton button p { font-size: 1.1rem !important; font-weight: 600; }
.stApp .stButton button, .stApp .stDownloadButton button { border-radius: 6px; }

/* Plain-English sentence under each signal */
/* Small "?" bubble next to a financial term */
.stApp [data-testid="stPopover"] button { min-height: 1.7rem; padding: 0 0.55rem; border-radius: 50%;
        border: 1px solid #b8c0cc; color: #1d3557; background: #fff; }
.stApp [data-testid="stPopover"] button p { font-size: 0.9rem !important; font-weight: 700; }
.metric-title { font-size: 1.02rem; color: #5b6573; padding-top: 0.25rem; min-height: 3.1em; }
.term-cell { font-size: 1.05rem; padding-top: 0.3rem; }
.swap { display: inline-grid; align-items: start; overflow: hidden; cursor: help; vertical-align: bottom; }
.swap .fin { border-bottom: 1px dotted #9aa6b2; justify-self: start; }
.swap > span { grid-area: 1 / 1; transition: transform 0.6s cubic-bezier(.4,0,.2,1), opacity 0.6s ease; }
.swap .lay { transform: translateY(100%); opacity: 0; color: #1d5c42; font-weight: 600; }
.swap:hover .fin, .swap:focus .fin { transform: translateY(-100%); opacity: 0; transition-delay: 2s; }
.swap:hover .lay, .swap:focus .lay { transform: none; opacity: 1; transition-delay: 2s; }
@media (hover: none) { .swap:hover .fin, .swap:focus .fin, .swap:hover .lay, .swap:focus .lay { transition-delay: 0.1s; } }
.scale { margin: 0.2rem 0 0.9rem 0; }
.scale-bar { position: relative; height: 0.7rem; border-radius: 999px; background: linear-gradient(90deg, #d9534f 0%, #f0ad4e 50%, #4fae6a 100%); }
.scale-bar.neutral { background: linear-gradient(90deg, #cfe0f1 0%, #8fb4d9 50%, #3f78b0 100%); }
.scale-pin { position: absolute; top: -0.3rem; width: 0.28rem; height: 1.3rem; margin-left: -0.14rem; border-radius: 3px;
             background: #1b2a3a; box-shadow: 0 0 0 2px #ffffff; }
.scale-ends { display: flex; justify-content: space-between; font-size: 0.78rem; color: #6b7785; margin-top: 0.25rem; }
.scale-verdict { font-weight: 700; font-size: 1rem; margin-top: 0.15rem; }
.meaning { font-size: 1.02rem; color: #4a5461; min-height: 5.2em; line-height: 1.45; padding: 0 0.2rem; }

/* Key sentence on a page */
.callout { border-left: 4px solid #1d3557; background: #f3f5f8; padding: 0.9rem 1.2rem;
           border-radius: 4px; font-size: 1.2rem; line-height: 1.5; margin: 0.5rem 0 1rem 0; }
.notice { border-left: 4px solid #b7791f; background: #fdf6e7; padding: 0.7rem 1.1rem;
          border-radius: 4px; font-size: 1.0rem; margin: 0.5rem 0 1rem 0; color: #5b4a1e; }

/* The small circled "i" that opens the About page */
.stApp .st-key-about_btn { display: flex; justify-content: flex-end; margin-top: 0.9rem; }
.stApp .st-key-about_btn button { border-radius: 50%; width: 2.3rem; height: 2.3rem; min-height: 2.3rem; padding: 0;
        border: 2px solid #1d3557; color: #1d3557; background: #fff; }
.stApp .st-key-about_btn button p { font-family: Georgia, 'Times New Roman', serif; font-style: italic; font-weight: 700;
        font-size: 1.25rem !important; line-height: 1; }
.stApp .st-key-about_btn button:hover { background: #1d3557; color: #fff; }
.stApp .st-key-about_btn button:hover p { color: #fff; }

/* About page: creator card */
.monogram { width: 4.2rem; height: 4.2rem; border-radius: 50%; background: #1d3557; color: #fff; display: flex;
        align-items: center; justify-content: center; font-size: 1.6rem; font-weight: 700; letter-spacing: 1px; }
.creator-name { font-size: 1.7rem; font-weight: 700; line-height: 1.2; color: #1d3557; }
.creator-meta { font-size: 1.05rem; color: #5b6573; margin-top: 0.15rem; }
.chip { display: inline-block; padding: 0.3rem 0.8rem; margin: 0 0.4rem 0.4rem 0; border-radius: 999px; font-size: 0.95rem;
        font-weight: 600; border: 1px solid #c9d2e0; background: #f3f5f8; color: #1d3557; }
.chip-done { background: #e6f2ec; border-color: #9fd0b8; color: #1d5c42; }
.chip-next { background: #fdf6e7; border-color: #e6c987; color: #7a5a14; }

/* Friendly error cards */
.error-card { border-radius: 8px; padding: 1.1rem 1.4rem; margin: 1rem 0; border: 1px solid #c9d2e0; background: #f3f5f8; }
.error-card.warn { border-color: #e6c987; background: #fdf6e7; }
.error-card .error-title { font-size: 1.4rem; font-weight: 700; margin-bottom: 0.4rem; color: #1d3557; }
.error-card p { margin: 0.3rem 0; font-size: 1.1rem !important; }
.error-card p.small { font-size: 0.95rem !important; color: #5b6573; }

/* ---- small screens (phones) ---- */
@media (max-width: 640px) {
  /* Tabs wrap onto a second line instead of hiding behind a scroll arrow */
  .stApp [role="tablist"], .stApp [data-baseweb="tab-list"] { flex-wrap: wrap !important; overflow: visible !important; row-gap: 0.15rem; }
  .stApp [data-baseweb="tab-highlight"], .stApp [data-baseweb="tab-border"] { display: none !important; }
  .stApp [data-testid="stTab"], .stApp button[data-baseweb="tab"] { padding: 0.35rem 0.6rem; font-size: 1rem !important; }
  .stApp [data-testid="stTab"] p { font-size: 1rem !important; }
  .stApp [data-testid="stTab"][aria-selected="true"], .stApp button[data-baseweb="tab"][aria-selected="true"] { border-bottom: 3px solid #1d3557; }
  /* The title and the About icon stay on one line */
  .stApp [data-testid="stHorizontalBlock"]:has(.about-row-marker) { flex-wrap: nowrap !important; align-items: center; }
  .stApp [data-testid="stHorizontalBlock"]:has(.about-row-marker) > [data-testid="stColumn"] { min-width: 0 !important; width: auto !important; flex: 1 1 0 !important; }
  .stApp [data-testid="stHorizontalBlock"]:has(.about-row-marker) > [data-testid="stColumn"]:nth-child(2) { flex: 0 0 3rem !important; }
  /* Comparison-table rows stay side by side, so each value stays under its heading */
  .stApp [data-testid="stHorizontalBlock"]:has(.tr-marker) { flex-wrap: nowrap !important; gap: 0.25rem !important; }
  .stApp [data-testid="stHorizontalBlock"]:has(.tr-marker) > [data-testid="stColumn"] { min-width: 0 !important; width: auto !important; flex: 1 1 0 !important; }
  .stApp [data-testid="stHorizontalBlock"]:has(.tr-marker) > [data-testid="stColumn"]:nth-child(1) { flex-grow: 2.6 !important; }
  .stApp [data-testid="stHorizontalBlock"]:has(.tr-marker) > [data-testid="stColumn"]:nth-child(2) { flex-grow: 0.6 !important; }
  .term-cell { font-size: 0.85rem; line-height: 1.25; word-break: break-word; }
}

/* A thin ribbon in the four bands of the Mayo College crest (crimson, gold, sky blue, green) across the top */
.stApp::before { content: ""; position: fixed; top: 0; left: 0; right: 0; height: 6px; z-index: 999999;
  background: linear-gradient(90deg, #C0392B 0 25%, #C8962E 25% 50%, #4FB0DD 50% 75%, #2E7D4F 75% 100%); }

/* the school crest beside the page title */
.brand { display: flex; align-items: center; gap: 0.9rem; }
.brand h1 { margin: 0; padding: 0; }
.brand-crest { height: 4.2rem; width: auto; flex: 0 0 auto; }
@media (max-width: 640px) { .brand-crest { height: 3rem; } .brand h1 { font-size: 1.9rem !important; } }

/* the Key signals cards wrap on narrow screens instead of clipping their words */
.st-key-signals_row [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; }
.st-key-signals_row [data-testid="stColumn"] { min-width: 200px !important; flex: 1 1 200px !important; }
.st-key-signals_row [data-testid="stMetricValue"], .st-key-signals_row [data-testid="stMetricValue"] * { font-size: 1.75rem !important; }

/* less empty space above the title */
.stApp [data-testid="stMainBlockContainer"], .stApp .block-container { padding-top: 2.2rem !important; }

/* Footer disclaimer: small and quiet */
.disclaimer { font-size: 0.82rem; color: #6b7480; line-height: 1.5; border-top: 1px solid #e1e5ec;
              padding-top: 0.9rem; margin-top: 2rem; }
</style>
"""


def setup_page(title):
    st.set_page_config(page_title=title, layout="wide")
    st.markdown(STYLE_CSS, unsafe_allow_html=True)


def callout(text):
    """A highlighted key sentence."""
    st.markdown(f'<div class="callout">{text}</div>', unsafe_allow_html=True)


def notice(text):
    """A muted amber note (used for 'saved data' warnings)."""
    st.markdown(f'<div class="notice">{text}</div>', unsafe_allow_html=True)


def show_disclaimer():
    st.markdown(f'<div class="disclaimer"><b>Disclaimer.</b> {DISCLAIMER}</div>', unsafe_allow_html=True)


def plain_english(markdown, label="In plain English"):
    """A drop-down with a layman's explanation (for visitors who are not finance people)."""
    with st.expander(label):
        st.markdown(markdown)


def _show_know_how(markdown):
    st.markdown(markdown)


def know_how_button(key, title, markdown):
    """A 'Know how' button that opens a pop-up with the full method: rules, factors, calculation."""
    if st.button("Know how", key=key):
        st.dialog(f"Know how: {title}", width="large")(_show_know_how)(markdown)


# ---------------- "?" bubbles for financial terms ----------------
def help_bubble(key):
    """A small "?" button. Clicking it opens a bubble with the term's use, formula and how to read it."""
    from core.glossary import as_markdown
    with st.popover("?"):
        st.markdown(as_markdown(key))


# The same idea in everyday words. A label shows the finance term; hold the pointer over it for about two seconds
# and it slides into the plain-words version (on a phone, tap it).
LAYMAN = {
    "rsi": "How fast it has been rising or falling", "macd": "Is the price speeding up or slowing down?",
    "trend": "Which way the price is heading", "volatility": "How bumpy and risky the ride is",
    "cagr": "How much it grew per year", "max_drawdown": "The worst fall it had", "var95": "How bad a bad day can get",
    "sharpe": "Reward for the risk taken", "sortino": "Reward compared with the falls",
    "calmar": "Reward compared with the worst fall", "treynor": "Reward for riding the market's ups and downs",
    "beta": "Does it swing more than the market?", "alpha": "Extra return beyond the market",
    "information": "Did it beat the market steadily?", "correlation": "Does it move together with the market?",
    "total_return": "Total gain or loss", "volume_confirmation": "Are lots of people behind this move?", "win_rate": "How often a trade made money",
    "avg_win": "Typical winning trade", "avg_loss": "Typical losing trade", "expectancy": "Average gain per trade",
}


def jargon(text, key):
    """HTML for a label: the finance term, sliding into plain words on hover. Plain text if there is no translation."""
    plain = LAYMAN.get(key)
    if not plain:
        return text
    return f'<span class="swap" tabindex="0"><span class="fin">{text}</span><span class="lay">{plain}</span></span>'


def metric_with_help(title, value, key, delta=None):
    """A metric card with its name and a "?" bubble above it."""
    name_col, help_col = st.columns([5, 1])
    name_col.markdown(f'<div class="metric-title">{jargon(title, key)}</div>', unsafe_allow_html=True)
    with help_col:
        help_bubble(key)
    st.metric(title, value, delta, label_visibility="collapsed")


def ratio_scale(key, value):
    """A colour scale (red to green) with a pointer showing how good or bad this ratio is. Empty if there is no scale."""
    from core import ratios
    rating = ratios.rate(key, value)
    if rating is None:
        return ""
    pos = rating["pos"]
    if rating["better"] == "neutral":
        colour, bar = "#2f6496", "scale-bar neutral"
    else:
        colour, bar = f"hsl({int(pos * 125)}, 60%, 33%)", "scale-bar"
    left, right = rating["ends"]
    return (f'<div class="scale"><div class="{bar}"><span class="scale-pin" style="left:{pos * 100:.1f}%"></span></div>'
            f'<div class="scale-ends"><span>{left}</span><span>{right}</span></div>'
            f'<div class="scale-verdict" style="color:{colour}">{rating["label"]}</div></div>')


def term_row(term, key, *cells, header=False):
    """One row of a comparison table: term, "?" bubble, then the values."""
    cols = st.columns([3.2, 0.7] + [2] * len(cells))
    marker = '<span class="tr-marker"></span>'          # lets the phone CSS recognise table rows
    if header:
        cols[0].markdown(f'<div class="term-cell">{marker}<b>{term}</b></div>', unsafe_allow_html=True)
        for c, text in zip(cols[2:], cells):
            c.markdown(f'<div class="term-cell"><b>{text}</b></div>', unsafe_allow_html=True)
        return
    cols[0].markdown(f'<div class="term-cell">{marker}{jargon(term, key)}</div>', unsafe_allow_html=True)
    if key:
        with cols[1]:
            help_bubble(key)
    for c, text in zip(cols[2:], cells):
        c.markdown(f'<div class="term-cell">{text}</div>', unsafe_allow_html=True)
