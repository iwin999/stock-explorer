"""The "Ask the bot" tab: a chat that answers from the site's own notes (free, no outside service)."""
import streamlit as st

from core import assistant as ai
from core import branding
from core import knowledge as kb
from core.errors import guard


def render(ctx):
    """ctx: what the visitor is looking at (see core.assistant.live_answer)."""
    st.header("Ask the bot")
    st.caption("A helper that answers from this site's own notes about finance terms, the simulations and strategy tests, "
               "futures and options, and how to use the app. If something is not in its notes, it says so. It teaches; it "
               "does not give investment advice or predict prices.")

    st.radio("Explain at this level", list(ai.LEVEL_NAMES), index=2, horizontal=True, key="chat_level",
             format_func=ai.LEVEL_NAMES.get,
             help="Pick how simply I explain things. You can also type an age, like \"explain beta like I'm 8\".")
    history = st.session_state.setdefault("chat", [])
    question = None

    # ---- the conversation so far ----
    for i, message in enumerate(history):
        with st.chat_message(message["role"]):
            st.markdown(branding.apply(message["content"]))
            if message["role"] == "assistant" and i == len(history) - 1:
                for j, title in enumerate(message.get("related", [])):
                    if st.button(branding.apply(title), key=f"rel_{i}_{j}"):
                        question = title

    # ---- starter questions on a fresh chat ----
    if not history:
        st.markdown("**Try asking:**")
        for row in (ai.STARTERS[:2], ai.STARTERS[2:]):
            for col, text in zip(st.columns(2), row):
                if col.button(branding.apply(text), key=f"starter_{text}", width="stretch"):
                    question = text

    typed = st.chat_input("Ask about a term, a chart or how the app works", max_chars=ai.MAX_QUESTION_CHARS, key="chat_input")
    question = typed or question

    if question:
        _reply(question, history, ctx)
        st.rerun()                      # redraw the chat so the newest answer and its follow-up buttons appear

    # ---- browse instead of typing ----
    with st.expander("Browse all topics"):
        topics = ai.topics()
        category = st.selectbox("Topic", [c for c in kb.CATEGORY_ORDER if topics[c]], key="browse_cat")
        title = st.selectbox("Question", topics[category], key="browse_q", format_func=branding.apply)
        if st.button("Show answer", key="browse_go"):
            _reply(title, history, ctx)
            st.rerun()

    if history and st.button("Clear chat", key="chat_clear"):
        st.session_state["chat"] = []
        st.rerun()
    st.caption("Answers come from notes written for this site, so they can be incomplete. Educational only; not investment advice.")


@guard()
def _reply(raw_question, history, ctx):
    question, problem = ai.clean_question(branding.unapply(raw_question))
    if problem:
        history.append({"role": "assistant", "content": problem, "related": []})
        return
    last = next((m.get("source") for m in reversed(history) if m["role"] == "assistant" and m.get("source")), None)
    last_level = next((m.get("level") for m in reversed(history) if m["role"] == "assistant" and m.get("source")), None)
    result = ai.answer(question, ctx, st.session_state.get("chat_level", "age_15"), last, last_level)
    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": result["text"], "related": result["related"],
                    "source": result.get("source"), "level": result.get("level")})


# ---------------- the small chat bubble (bottom corner of the dashboard) ----------------
BUBBLE_CSS = """<style>
body:has([data-testid="stDialog"]) .st-key-ask_bubble, body:has([data-testid="stDialog"]) .st-key-guide_btn { display: none !important; }
.st-key-guide_btn { position: fixed !important; right: 0.95rem; bottom: 8.4rem; z-index: 990; width: auto !important; }
.st-key-guide_btn a.guide-link { display: flex; align-items: center; justify-content: center; width: 2.9rem; height: 2.9rem; border-radius: 50%; background: #ffffff;
    box-shadow: 0 3px 12px rgba(0,0,0,0.28), 0 0 0 1px rgba(60,100,200,0.18); transition: transform .15s ease, box-shadow .15s ease; text-decoration: none; }
.st-key-guide_btn a.guide-link:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(0,0,0,0.32), 0 0 0 2px rgba(66,133,244,0.5); }
.st-key-guide_btn svg { width: 1.55rem; height: 1.55rem; display: block; }     /* out of the way while a pop-up is open */
.st-key-ask_bubble { position: fixed !important; right: 0.6rem; bottom: 3.7rem; z-index: 990; width: auto !important; }     /* at the right edge, above Streamlit's Manage app bar; stays put while the page scrolls */
.st-key-ask_bubble [data-testid="stPopoverButton"] { width: 3.6rem; height: 3.6rem; min-height: 3.6rem; padding: 0 !important; border-radius: 50%;
    background: radial-gradient(circle at 35% 28%, #6f9bff 0%, #3f74e6 55%, #2f5fcf 100%) !important; border: none !important;
    box-shadow: 0 0 0 4px rgba(79,126,238,0.22), 0 0 22px 4px rgba(79,126,238,0.55); animation: askglow 3.2s ease-in-out infinite;
    display: flex; align-items: center; justify-content: center; }
.st-key-ask_bubble [data-testid="stPopoverButton"]:hover { filter: brightness(1.08); }
@keyframes askglow { 0%,100% { box-shadow: 0 0 0 4px rgba(79,126,238,0.20), 0 0 18px 3px rgba(79,126,238,0.45); }
                     50% { box-shadow: 0 0 0 6px rgba(79,126,238,0.28), 0 0 28px 7px rgba(79,126,238,0.65); } }
.st-key-ask_bubble [data-testid="stPopoverButton"] > div { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; gap: 0 !important; padding: 0 !important; margin: 0 !important; }
.st-key-ask_bubble [data-testid="stPopoverButton"] [aria-hidden="true"], .st-key-ask_bubble [data-testid="stPopoverButton"] [data-testid="stIconMaterial"] { display: none !important; }
.st-key-ask_bubble [data-testid="stPopoverButton"] > div > div, .st-key-ask_bubble [data-testid="stPopoverButton"] span, .st-key-ask_bubble [data-testid="stPopoverButton"] [data-testid="stMarkdownContainer"] {
    margin: 0 !important; padding: 0 !important; display: flex; align-items: center; justify-content: center; }
.st-key-ask_bubble [data-testid="stPopoverButton"] p { display: none !important; }     /* the word is only for screen readers; the picture below is what you see */
.st-key-ask_bubble [data-testid="stPopoverButton"] { position: relative; }
.st-key-ask_bubble [data-testid="stPopoverButton"]::after { content: ""; position: absolute; inset: 0; margin: auto; width: 2rem; height: 2rem;
    background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Cpath d='M32 10C17.6 10 8 19 8 30c0 6 2.9 11.2 7.6 14.7-.4 3.3-1.9 6.2-4.1 8.5 5.6-.3 10.2-2.2 13.4-4.6 2.3.6 4.7.9 7.1.9 14.4 0 24-9 24-20S46.4 10 32 10z' fill='white'/%3E%3Ccircle cx='21.5' cy='30' r='3.6' fill='%233f74e6'/%3E%3Ccircle cx='32' cy='30' r='3.6' fill='%233f74e6'/%3E%3Ccircle cx='42.5' cy='30' r='3.6' fill='%233f74e6'/%3E%3C/svg%3E") center / contain no-repeat; filter: drop-shadow(0 1px 3px rgba(20,40,110,0.35)); }
.st-key-ask_bubble [data-testid="stPopoverButton"] * { color: #ffffff !important; }
[data-testid="stPopoverBody"]:has(.ask-head) { width: min(380px, 92vw) !important; max-height: 72vh; overflow-y: auto; }
[data-testid="stPopoverBody"]:has(.ask-head) [data-testid="InputInstructions"] span:first-child { display: none; }     /* just the 0/300 count, below the box */
[data-testid="stPopoverBody"]:has(.ask-head) [data-testid="InputInstructions"] span::before { content: none !important; }
[data-testid="stPopoverBody"]:has(.ask-head) div:has(> [data-testid="InputInstructions"]) { position: static !important; }
[data-testid="stPopoverBody"]:has(.ask-head) [data-testid="InputInstructions"] { display: flex; justify-content: flex-end; padding: 0.3rem 0.15rem 0 0; position: static !important; }
.ask-head { font-weight: 800; font-size: 1.1rem; margin-bottom: .1rem; }
.ask-sub { font-size: .82rem; opacity: .7; margin-bottom: .5rem; }
</style>"""


GUIDE_ICON = ('<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M10 3h19l11 11v29a2 2 0 0 1-2 2H10a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z" fill="#4285f4"/>'
              '<path d="M29 3l11 11H31a2 2 0 0 1-2-2z" fill="#a8c7fa"/>'
              '<rect x="14" y="22" width="20" height="3" rx="1.5" fill="#ffffff"/><rect x="14" y="29" width="20" height="3" rx="1.5" fill="#ffffff"/>'
              '<rect x="14" y="36" width="13" height="3" rx="1.5" fill="#ffffff"/></svg>')


def bubble(ctx):
    """A round chat button fixed to the bottom-right corner. Click it and an 'Ask me anything' panel opens above it. Above it sits a
    small document button that opens the presenter's guide (a PDF) in a new tab."""
    st.markdown(BUBBLE_CSS, unsafe_allow_html=True)
    with st.container(key="guide_btn"):
        st.markdown(f'<a class="guide-link" href="{branding.guide_url()}" target="_blank" rel="noopener" '
                    f'title="Read the presenter\'s guide (PDF)" aria-label="Read the presenter\'s guide (PDF)">{GUIDE_ICON}</a>', unsafe_allow_html=True)
    with st.container(key="ask_bubble"):
        with st.popover("AI", help="Ask me anything"):
            _bubble_chat(ctx)


def _ask_later(text):
    st.session_state["bub_q"] = text


def _clear_chat():
    st.session_state["chat"] = []


@st.fragment
def _bubble_chat(ctx):
    """The chat itself. It is a fragment, so asking a question redraws only this panel and not the whole page."""
    st.session_state.setdefault("chat_level", "age_15")
    history = st.session_state.setdefault("chat", [])
    st.markdown('<div class="ask-head">Ask me anything</div><div class="ask-sub">About a term, a chart or how this app works. '
                'I teach; I do not give investment advice.</div>', unsafe_allow_html=True)
    with st.form("bubble_form", clear_on_submit=True, border=False):          # the box stays at the top, so it is always in view
        typed = st.text_input("Your question", max_chars=ai.MAX_QUESTION_CHARS, label_visibility="collapsed",
                              placeholder="Type a question and press Enter")
        asked = st.form_submit_button("Ask", type="primary", width="stretch")
    question = st.session_state.pop("bub_q", None) or (typed if asked and typed.strip() else None)     # answer first, then draw the chat
    if question:
        _reply(question, history, ctx)
    if not history:
        for text in ai.STARTERS[:3]:
            st.button(branding.apply(text), key=f"bub_starter_{text}", width="stretch", on_click=_ask_later, args=(text,))
    for message in history[-2:]:                                       # only the latest question and answer, right under the box
        with st.chat_message(message["role"]):
            st.markdown(branding.apply(message["content"]))
    last = history[-1] if history else None
    if last and last["role"] == "assistant":
        for j, title in enumerate(last.get("related", [])[:3]):
            st.button(branding.apply(title), key=f"bub_rel_{len(history)}_{j}", width="stretch", on_click=_ask_later, args=(title,))
    if history:
        st.button("Clear chat", key="bub_clear", on_click=_clear_chat)
