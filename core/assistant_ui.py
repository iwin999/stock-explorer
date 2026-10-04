"""The "Ask the bot" tab: a chat that answers from the site's own notes (free, no outside service)."""
import streamlit as st

from core import assistant as ai
from core import knowledge as kb
from core.errors import guard


def render(ctx):
    """ctx: what the visitor is looking at (see core.assistant.live_answer)."""
    st.header("Ask the bot")
    st.caption("A helper that answers from this site's own notes about finance terms, the simulations and strategy tests, "
               "futures and options, and how to use the app. If something is not in its notes, it says so. It teaches; it "
               "does not give investment advice or predict prices.")

    st.radio("Explain at this level", list(ai.LEVEL_NAMES), index=1, horizontal=True, key="chat_level",
             format_func=ai.LEVEL_NAMES.get,
             help="Pick how simply I explain things. You can also type an age, like \"explain beta like I'm 8\".")
    history = st.session_state.setdefault("chat", [])
    question = None

    # ---- the conversation so far ----
    for i, message in enumerate(history):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and i == len(history) - 1:
                for j, title in enumerate(message.get("related", [])):
                    if st.button(title, key=f"rel_{i}_{j}"):
                        question = title

    # ---- starter questions on a fresh chat ----
    if not history:
        st.markdown("**Try asking:**")
        for row in (ai.STARTERS[:2], ai.STARTERS[2:]):
            for col, text in zip(st.columns(2), row):
                if col.button(text, key=f"starter_{text}", width="stretch"):
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
        title = st.selectbox("Question", topics[category], key="browse_q")
        if st.button("Show answer", key="browse_go"):
            _reply(title, history, ctx)
            st.rerun()

    if history and st.button("Clear chat", key="chat_clear"):
        st.session_state["chat"] = []
        st.rerun()
    st.caption("Answers come from notes written for this site, so they can be incomplete. Educational only; not investment advice.")


@guard()
def _reply(raw_question, history, ctx):
    question, problem = ai.clean_question(raw_question)
    if problem:
        history.append({"role": "assistant", "content": problem, "related": []})
        return
    last = next((m.get("source") for m in reversed(history) if m["role"] == "assistant" and m.get("source")), None)
    result = ai.answer(question, ctx, st.session_state.get("chat_level", "age_15"), last)
    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": result["text"], "related": result["related"],
                    "source": result.get("source")})
