"""The company search box (one box, ranked suggestions, old names, live Yahoo search), shared by the tabbed view and the
Terminal view."""
import streamlit as st

from core import companies, universe


@st.cache_data(ttl=600, show_spinner=False)
def run_search(query):
    return companies.search(query)


def _use_found_company(symbol):
    """Button callback: make a company found by the live Yahoo search the chosen one."""
    st.session_state.setdefault("extra_companies", [])
    if symbol not in st.session_state["extra_companies"]:
        st.session_state["extra_companies"].append(symbol)
    st.session_state["company"] = symbol


def _pick_company(symbol):
    """Button callback: choose one of the suggested companies."""
    st.session_state["company"] = symbol


def choose(compact=False):
    """Draw the search box and return the chosen company symbol.

    compact=True is the one-row version for the dashboard: just a SEARCH STOCK box, no live-search drawer and no explanatory lines;
    close matches appear as a single row of small buttons."""
    company_options = list(st.session_state.get("extra_companies", [])) + universe.OPTIONS
    typed_or_picked = st.selectbox("Search stock" if compact else "Search any NSE or BSE company (start typing a name)", company_options,
                                   format_func=companies.label, key="company", accept_new_options=True, index=None,
                                   placeholder="SEARCH STOCK" if compact else "Type a company name, for example Tata, Suzlon or HDFC",
                                   label_visibility="collapsed" if compact else "visible",
                                   help=f"{len(universe.OPTIONS):,} companies listed on the NSE and the BSE. Type part of a name, "
                                        "for example 'tata', 'suzlon' or 'bank'. A small spelling slip is fine: type the name, "
                                        "press Enter, and the closest matches are listed best first.")
    symbol = typed_or_picked
    if typed_or_picked is None:                                # nothing typed yet: start with a well-known company
        symbol = company_options[0]
        if not compact:
            st.caption(f"Showing {companies.label(symbol)} to start with. Click the box to browse the list, or type a name to find another company.")
    elif typed_or_picked not in company_options:               # something was typed and entered: find the closest companies
        suggestions = universe.rank(typed_or_picked, 8)
        if suggestions:
            symbol = suggestions[0]
            old = universe.renamed(typed_or_picked)
            if old and compact:
                st.caption(f"“{typed_or_picked}” is an old name; now listed as {companies.NAME_BY_SYMBOL.get(suggestions[0], suggestions[0])}.")
            elif old:
                st.info(f"“{typed_or_picked}” is an old name. The company is now listed as "
                        f"**{companies.NAME_BY_SYMBOL.get(suggestions[0], suggestions[0])}**.")
            if compact:                                         # one row: the best matches side by side
                best = []                                       # one entry per company (its NSE listing), shown by name
                for sug in suggestions:
                    nse = companies.to_nse(sug)
                    if nse not in best:
                        best.append(nse)
                best = best[:4]
                for col, sug in zip(st.columns(len(best)), best):
                    col.button(companies.NAME_BY_SYMBOL.get(sug, sug), key=f"sug_{sug}", width="stretch",
                               type="primary" if sug == best[0] else "secondary", on_click=_pick_company, args=(sug,))
            else:
                st.caption(f"Closest matches for “{typed_or_picked}”, best first. Showing the first one; tap another to switch.")
                for i in range(0, len(suggestions), 2):
                    cols = st.columns(2)
                    for col, sug in zip(cols, suggestions[i:i + 2]):
                        col.button(("1. " if sug == suggestions[0] else "") + companies.label(sug), key=f"sug_{sug}", width="stretch",
                                   type="primary" if sug == suggestions[0] else "secondary", on_click=_pick_company, args=(sug,))
        else:
            symbol = company_options[0]
            st.warning(f"No company looks like “{typed_or_picked}”. Try another spelling." if compact
                       else f"No company looks like “{typed_or_picked}”. Try another spelling, or search Yahoo Finance below.")
    if compact:
        return symbol
    with st.expander("Cannot find a company? Search Yahoo Finance live"):
        live_query = st.text_input("Company name", key="live_query", placeholder="e.g. a company that listed very recently")
        if live_query.strip():
            found, _src = run_search(live_query.strip())
            if not found:
                st.warning(f"Nothing found for “{live_query}”. Try another spelling.")
            for r in found[:8]:
                c1, c2 = st.columns([5, 1])
                c1.write(companies.label(r["symbol"]) if r["symbol"] in companies.NAME_BY_SYMBOL else f"{r['name']} ({r['symbol']})")
                c2.button("Use", key=f"use_{r['symbol']}", on_click=_use_found_company, args=(r["symbol"],))

    return symbol
