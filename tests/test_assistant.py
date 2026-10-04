from datetime import datetime
from zoneinfo import ZoneInfo

from core import assistant as a

IST = ZoneInfo("Asia/Kolkata")


def test_system_prompt_has_rules_guide_glossary_and_context():
    p = a.build_system_prompt("Selected company: Reliance")
    assert "Do not give personal investment advice" in p and "Never reveal" in p
    assert "Possible outcomes" in p and "Black-Scholes" in p
    assert "Sharpe ratio" in p and "Formula:" in p                  # glossary is included
    assert p.endswith("Selected company: Reliance")
    assert "What the visitor is looking at" not in a.build_system_prompt("")


def test_page_context_is_compact_and_readable():
    ctx = a.page_context("Reliance Industries", "RELIANCE.NS", 1167.7, [("RSI", "28 / 100")],
                         {"cash": 22800.48, "holdings": {"TCS.NS": 6}, "derivatives": 2})
    assert "Reliance Industries (RELIANCE)" in ctx and "Rs 1,167.70" in ctx and "RSI: 28 / 100" in ctx
    assert "TCS x6" in ctx and "open futures/options: 2" in ctx


def test_questions_are_validated():
    assert a.clean_question("  what   is  RSI? ") == ("what is RSI?", None)
    assert a.clean_question("   ")[1] == "Please type a question."
    assert "under 500" in a.clean_question("x" * 501)[1]


def test_history_is_trimmed_and_starts_with_the_user():
    msgs = []
    for i in range(10):
        msgs += [{"role": "user", "content": f"q{i}"}, {"role": "assistant", "content": f"a{i}"}]
    out = a.trim_history(msgs)
    assert len(out) <= a.MAX_HISTORY_MESSAGES and out[0]["role"] == "user" and out[-1]["content"] == "a9"
    assert a.trim_history([{"role": "assistant", "content": "hi"}]) == []


def test_daily_budget_runs_out_and_resets_at_midnight_ist():
    b = a.DailyBudget(limit=2)
    day1 = datetime(2026, 10, 4, 10, 0, tzinfo=IST)
    assert b.allow(day1) and b.allow(day1) and not b.allow(day1)
    assert b.remaining(day1) == 0
    assert b.allow(datetime(2026, 10, 5, 0, 5, tzinfo=IST)) and b.remaining(datetime(2026, 10, 5, 1, 0, tzinfo=IST)) == 1
