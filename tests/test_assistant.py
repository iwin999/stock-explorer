import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from bot_eval_data import NEGATIVE, POSITIVE  # noqa: E402

from core import assistant as a  # noqa: E402
from core import glossary, knowledge as kb  # noqa: E402


def judged_correct(question, wanted):
    r = a.answer(question)
    wants = wanted.split("|")
    top = a.rank(question, 1)[0][1]["id"]
    return ((r["kind"] == "notes" and r.get("source") in wants) or (r["kind"] == "live" and "live" in wants)
            or (r["kind"] == "maybe" and top in wants))


def test_real_questions_get_the_right_note():
    misses = [q for q, want in POSITIVE if not judged_correct(q, want)]
    assert len(misses) <= 2, f"{len(misses)} of {len(POSITIVE)} missed: {misses}"      # >= 98% right


def test_off_topic_questions_are_refused_not_invented():
    leaks = [q for q in NEGATIVE if a.answer(q)["kind"] not in ("unknown", "chat")]
    assert leaks == [], f"answered from the notes when it should not have: {leaks}"


def test_every_note_answers_its_own_questions():
    for entry in kb.ENTRIES:
        for phrasing in [entry["title"]] + entry["questions"]:
            top_score, top = a.rank(phrasing, 1)[0]
            assert top_score > 0.5, (entry["id"], phrasing, top_score)


def test_notes_are_complete_and_consistent():
    ids = [e["id"] for e in kb.ENTRIES]
    assert len(ids) == len(set(ids)), "duplicate note ids"
    for e in kb.ENTRIES:
        assert e["category"] in kb.CATEGORY_ORDER and e["answer"].strip() and e["questions"], e["id"]
        assert 40 < len(e["answer"]) < 900, (e["id"], len(e["answer"]))
    for key in glossary.TERMS:                                                       # every "?" bubble term is in the bot
        assert f"term_{key}" in kb.BY_ID


def test_advice_is_never_given():
    for q in ["should I buy reliance", "which stock will go up", "is reliance going to double", "tell me what to buy"]:
        r = a.answer(q)
        assert r.get("source") == "advice", q
    text = kb.BY_ID["advice"]["answer"].lower()
    assert "cannot tell you what to buy" in text and "nobody can predict" in text


def test_greetings_identity_and_thanks():
    assert a.answer("hello")["kind"] == "chat" and a.answer("thanks!")["kind"] == "chat"
    ident = a.answer("who are you")
    assert ident["kind"] == "chat" and "not connected to the internet" in ident["text"]


def test_live_answers_use_the_page_numbers_and_nothing_else():
    ctx = {"company": "Reliance Industries", "symbol": "RELIANCE.NS", "last_close": 1167.7,
           "signals": [("Recent strength (RSI)", "28 / 100", "The stock has fallen quickly.")],
           "portfolio": {"cash": 22800.0, "holdings": {"TCS.NS": 6}, "derivatives": 1}}
    mine = a.answer("how am I doing", ctx)
    assert mine["kind"] == "live" and "Rs 22,800" in mine["text"] and "TCS (6)" in mine["text"]
    page = a.answer("what does this stock say right now", ctx)
    assert page["kind"] == "live" and "28 / 100" in page["text"] and "not investment advice" in page["text"]
    assert a.answer("is the market open now")["kind"] == "live"
    assert a.answer("how am I doing", None)["kind"] != "live"                         # no page, no live numbers
    assert a.answer("how is my profit calculated", ctx)["kind"] == "notes"             # a "how does it work" question


def test_question_validation_and_topics_menu():
    assert a.clean_question("  what   is rsi ")[0] == "what is rsi"
    assert a.clean_question("")[1] and a.clean_question("x" * 400)[1]
    menu = a.topics()
    assert all(menu[c] for c in kb.CATEGORY_ORDER) and sum(len(v) for v in menu.values()) == len(kb.ENTRIES)
