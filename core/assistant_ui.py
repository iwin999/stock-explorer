"""The "Ask the bot" tab: a chat with Claude about finance terms and how to read this app."""
import logging
import os
import uuid

import anthropic
import streamlit as st

from core import assistant as ai
from core import errors as er
from core.ui import notice

log = logging.getLogger("stock_explorer.assistant")


def _secret(name, default=None):
    """A value from the app's secrets: [anthropic] name = ...  (or None/default if it is not set)."""
    try:
        return st.secrets["anthropic"][name]
    except Exception:
        return default


def settings():
    """(api_key, model, session_limit, daily_limit). The key may be in the secrets or in ANTHROPIC_API_KEY."""
    key = _secret("api_key") or os.environ.get("ANTHROPIC_API_KEY")
    model = str(_secret("model", ai.DEFAULT_MODEL))
    session_limit = int(_secret("session_limit", ai.DEFAULT_SESSION_LIMIT))
    daily_limit = int(_secret("daily_limit", ai.DEFAULT_DAILY_LIMIT))
    return key, model, session_limit, daily_limit


@st.cache_resource
def _budget(limit):
    """One shared daily counter for the whole site."""
    return ai.DailyBudget(limit)


def make_client(api_key):
    """Separate function so tests can swap in a fake client."""
    return anthropic.Anthropic(api_key=api_key)


def render(company, symbol, last_close, signals, portfolio=None):
    st.header("Ask the bot")
    st.caption("A friendly AI assistant that explains finance terms and helps you read this app. It teaches; it does not "
               "give investment advice or predict prices.")

    api_key, model, session_limit, daily_limit = settings()
    if not api_key:
        notice(f"The assistant is not switched on yet. Please contact the admin at {er.admin_email()} to enable it.")
        return

    history = st.session_state.setdefault("chat", [])
    asked = sum(1 for m in history if m["role"] == "user")
    left = session_limit - asked

    for message in history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    question = None
    if not history:
        st.markdown("**Try asking:**")
        for col, text in zip(st.columns(2), ai.STARTER_QUESTIONS[:2]):
            if col.button(text, key=f"starter_{text}", width="stretch"):
                question = text
        for col, text in zip(st.columns(2), ai.STARTER_QUESTIONS[2:]):
            if col.button(text, key=f"starter_{text}", width="stretch"):
                question = text

    typed = st.chat_input("Ask about a term, a chart or how the app works", max_chars=ai.MAX_QUESTION_CHARS,
                          disabled=left <= 0, key="chat_input")
    question = typed or question

    if question:
        _answer(question, history, left, api_key, model, daily_limit,
                ai.page_context(company, symbol, last_close, signals, portfolio))
        left = session_limit - sum(1 for m in history if m["role"] == "user")

    if left <= 0:
        notice("You have used all your questions for this visit. Refresh the page for a fresh start, "
               f"or contact the admin at {er.admin_email()}.")
    st.caption(f"{max(left, 0)} question(s) left in this visit. Answers are written by an AI and can contain mistakes. "
               "Educational only; not investment advice. Your question and the page you are viewing are sent to an AI service.")


def _answer(raw_question, history, left, api_key, model, daily_limit, context):
    question, problem = ai.clean_question(raw_question)
    if problem:
        st.warning(problem)
        return
    if left <= 0:
        return
    if not _budget(daily_limit).allow():
        notice("The assistant has answered a lot of questions today and is resting until tomorrow. "
               f"Please contact the admin at {er.admin_email()} if you need it sooner.")
        return

    with st.chat_message("user"):
        st.markdown(question)
    messages = ai.trim_history(history) + [{"role": "user", "content": question}]

    with st.chat_message("assistant"):
        try:
            client = make_client(api_key)
            with client.messages.stream(
                model=model,
                max_tokens=ai.MAX_ANSWER_TOKENS,
                system=ai.build_system_prompt(context),
                messages=messages,
                output_config={"effort": "low"},          # quick, short answers for a chat box
            ) as stream:
                text = st.write_stream(stream.text_stream)
                final = stream.get_final_message()
        except anthropic.APIConnectionError:
            er.show(er.NETWORK)
            return
        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError, anthropic.NotFoundError) as exc:
            log.error("Assistant is not configured correctly: %s", type(exc).__name__)   # never log the key itself
            notice(f"The assistant is not available right now. Please contact the admin at {er.admin_email()}.")
            return
        except anthropic.RateLimitError:
            notice("The assistant is very busy at the moment. Please try again in a minute.")
            return
        except anthropic.APIStatusError as exc:
            if exc.status_code in (429, 500, 502, 503, 504, 529):
                notice("The assistant is temporarily unavailable. Please try again in a minute.")
                return
            reference = "E-" + uuid.uuid4().hex[:6].upper()
            log.exception("Assistant error %s", reference)
            er.show(er.UNEXPECTED, reference)
            return
        except Exception:
            reference = "E-" + uuid.uuid4().hex[:6].upper()
            log.exception("Assistant error %s", reference)
            er.show(er.UNEXPECTED, reference)
            return

        if final.stop_reason == "refusal":
            text = ("I can't help with that one. I can explain finance terms and how to use Stock Explorer, "
                    "so feel free to ask about those.")
            st.markdown(text)
        elif final.stop_reason == "max_tokens":
            text += "\n\n(That answer was cut short. Ask me to continue if you would like more.)"
            st.markdown("(That answer was cut short. Ask me to continue if you would like more.)")

    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": text})
