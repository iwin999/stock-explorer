"""The "Market today" strip at the top of the page: market status, the two main indices, your portfolio and the
biggest movers. Everything here is a quick look; the detail lives in the tabs below."""
import streamlit as st

from core import companies
from core.errors import guard
from core.formatting import format_inr
from core.live import REFRESH_SECONDS, live_quote
from core.market_data import load_offline
from core.market_hours import is_market_open, now_ist, status_message


@st.cache_data(ttl=3600, show_spinner=False)
def biggest_movers(n=3):
    """(date, risers, fallers) from the saved prices: the companies that moved most in the last saved session.
    Each is a list of (name, percent change)."""
    changes, last = [], None
    for name, symbol, _ in companies.COMPANIES:
        df = load_offline(symbol)
        if df is None or len(df) < 3:
            continue
        close = df["Close"]
        changes.append((name, float(close.iloc[-1] / close.iloc[-2] - 1) * 100))
        last = close.index[-1] if last is None or close.index[-1] > last else last
    changes.sort(key=lambda x: x[1])
    return last, changes[::-1][:n], changes[:n]


def _short(amount):
    """Rupees in lakh / crore so it fits a small card: 1,00,000 -> 'Rs 1.00 lakh'."""
    if amount >= 1e7:
        return f"{amount / 1e7:.2f} cr"
    if amount >= 1e5:
        return f"{amount / 1e5:.2f} lakh"
    return format_inr(amount, 0)


def _index_card(col, label, symbol):
    quote = live_quote(symbol)
    if quote:
        move = (f"{(quote['price'] / quote['previous_close'] - 1) * 100:+.2f}%" if quote.get("previous_close") else None)
        col.metric(label, f"{quote['price']:,.0f}", move)
    else:
        col.metric(label, "n/a")


@guard()
def _strip(portfolio_fn, rank_fn):
    now = now_ist()
    # One row. The column widths follow how much each card has to show, so the cards are only as wide as they
    # need to be and the fifth (leaderboard) fits into the space that used to sit empty.
    c1, c2, c3, c4, c5 = st.columns([1.25, 1, 1, 1.45, 1.2], gap="small")
    c1.metric("Market", "Open" if is_market_open() else "Closed", f"{now:%a %H:%M} IST", delta_color="off")
    _index_card(c2, "Nifty 50", "^NSEI")
    _index_card(c3, "Bank Nifty", "^NSEBANK")
    snap = portfolio_fn()
    if snap:
        c4.metric("Your portfolio", _short(snap["total"]), f"{snap['return_pct']:+.2f}% overall")
    rank = rank_fn()
    c5.metric("Leaderboard", f"#{rank[0]} of {rank[1]}" if rank else "n/a", "your rank" if rank else None, delta_color="off")
    st.caption(status_message() + ". " + ("Updating automatically." if is_market_open() else "Showing the last closing levels."))


def render(portfolio_fn, rank_fn):
    """portfolio_fn() returns the valuation snapshot of the signed-in account (or None); rank_fn() returns (rank, total) or None."""
    st.markdown("""<style>
.st-key-market_strip [data-testid="stMetricValue"], .st-key-market_strip [data-testid="stMetricValue"] * { font-size: 1.9rem !important; }
.st-key-market_strip [data-testid="stMetric"] { padding: 0.8rem 0.9rem; }
</style>""", unsafe_allow_html=True)
    with st.container(key="market_strip"):
        st.fragment(run_every=REFRESH_SECONDS if is_market_open() else None)(_strip)(portfolio_fn, rank_fn)
    last, risers, fallers = biggest_movers()
    if last is not None:
        with st.expander(f"Biggest movers in the last saved session ({last:%d %b %Y})"):
            up, down = st.columns(2)
            up.markdown("**Rose the most**\n\n" + "\n".join(f"- {n}: **{p:+.2f}%**" for n, p in risers))
            down.markdown("**Fell the most**\n\n" + "\n".join(f"- {n}: **{p:+.2f}%**" for n, p in fallers))
            st.caption("From the saved prices of the companies in this app. Choose one in the box below to look closer.")
