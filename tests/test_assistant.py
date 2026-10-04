import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from bot_eval_data import NEGATIVE, POSITIVE  # noqa: E402

from core import assistant as a  # noqa: E402
from core import glossary, knowledge as kb  # noqa: E402


# the older notes were joined by richer ones with their own ids; either one is a right answer
ALIASES = {"term_rsi": "n_rsi", "term_macd": "n_macd", "term_sharpe": "n_sharpe_ratio", "term_sortino": "n_sortino_ratio",
           "term_calmar": "n_calmar_ratio", "term_beta": "n_beta", "term_alpha": "n_alpha", "term_max_drawdown": "n_max_drawdown",
           "term_var95": "n_var", "term_volatility": "n_volatility", "term_cagr": "n_average_return",
           "term_information": "n_information_ratio", "monte_carlo": "n_monte_carlo", "gauge": "n_chance_higher",
           "not_prediction": "n_faq_is_prediction", "backtest": "n_backtest", "buy_and_hold": "n_buy_and_hold",
           "next_day": "n_look_ahead_bias", "rule_macd": "n_macd_rule", "rule_bollinger": "n_bollinger_rule", "stock": "n_stock",
           "etf": "n_index_fund", "nse": "n_nse_ticker", "avg_price": "n_average_price", "option": "n_options_futures",
           "real_money": "n_faq_is_money_real", "advice": "n_faq_should_i_buy|n_faq_is_prediction",
           "reset_account": "n_faq_start_over", "paper_trading": "n_paper_trading", "diversification": "n_diversification",
           "candlestick": "n_candlestick", "crossover": "n_golden_cross", "bollinger": "n_bollinger_bands",
           "overbought": "n_overbought_oversold", "last_close": "n_price_close", "trend_up_down": "n_trend", "nifty": "n_nifty50",
           "fusion_what": "n_fusion_analysis", "winners_circle": "n_winners_circle", "fusion_formula": "n_pfvs_formula",
           "overlay": "n_technical_overlay", "fusion_limits": "n_survivorship_bias", "expectancy_why": "n_win_rate",
           "top_down": "n_sector_rotation"}


def accepted(wanted):
    wants = wanted.split("|")
    return wants + [x for w in wants for x in ALIASES.get(w, "").split("|") if x]


def judged_correct(question, wanted):
    r = a.answer(question)
    wants = accepted(wanted)
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
        assert r.get("source") in accepted("advice"), q
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


def test_bot_reports_the_fusion_group_of_the_selected_company():
    ctx = {"company": "Zydus Lifesciences", "symbol": "ZYDUSLIFE.NS", "last_close": 1000.0, "signals": [],
           "portfolio": None, "fusion": {"group": 1, "stage_name": "Clear uptrend", "verdict": "Confirm"}}
    for q in ["what group is this stock in", "which group is this company in", "is this stock in the winner's circle"]:
        r = a.answer(q, ctx)
        assert r["kind"] == "live" and "fusion group 1" in r["text"] and "not advice" in r["text"], q
    assert a.answer("what is the winners circle", ctx)["kind"] == "notes"          # a general question still uses the notes


def test_fusion_notes_answer_the_chapter_questions():
    asks = {"what is fusion analysis": "fusion_what", "what does P = (F * V)^S mean": "fusion_formula",
            "what is the winners circle": "winners_circle", "why is trend non negotiable": "why_trend_first",
            "what does delay mean": "overlay", "what if technicals and fundamentals disagree": "divergence",
            "what are the trend stages": "trend_stages", "why is the fusion test only 3 years": "fusion_window",
            "what is survivorship bias": "fusion_limits", "trend following vs swing trading": "trend_vs_swing",
            "why does expectancy matter": "expectancy_why", "what is the top down approach": "top_down"}
    for q, want in asks.items():
        assert a.answer(q).get("source") in accepted(want), q


def test_age_changes_the_explanation():
    kid = a.answer("what is beta, explain like I'm 8")["text"]
    teen = a.answer("what is beta like I'm 13")["text"]
    adult = a.answer("what is beta, I am 40 years old")["text"]
    assert len({kid, teen, adult}) == 3 and "boat" in kid and "covariance" in adult
    assert a.answer("what is beta", level="adult")["text"] == adult        # the selected level is used when no age is typed
    assert a.split_level("explain rsi eli5")[1] == "age_5" and a.split_level("rsi", "adult")[1] == "adult"
    assert a.split_level("what is rsi, I'm 8")[0] == "what is rsi"


def test_every_note_has_all_levels_and_real_links():
    for e in kb.NOTES:
        if "levels" in e:
            assert all(e["levels"][lv].strip() for lv in kb.LEVELS) and e["in_app"].strip(), e["id"]
            assert all(r in kb.BY_ID for r in e["related_ids"]), (e["id"], e["related_ids"])


def test_new_notes_are_reachable_and_creator_is_filled_in():
    assert "Freya Shah" in a.answer("who made this app")["text"] and "[Her name]" not in kb.BY_ID["n_faq_who_made"]["answer"]
    for q, want in {"what is a whipsaw": "n_whipsaw", "what is slippage": "n_slippage", "what is a stop loss": "n_stop_loss",
                    "what is a demat account": "n_demat_kyc", "what is sebi": "n_sebi", "what is epat": "n_faq_what_is_epat",
                    "what is cmt": "n_faq_what_is_cmt"}.items():
        assert a.answer(q).get("source") == want, q


def test_follow_ups_reexplain_the_last_topic_at_the_new_level():
    simple = a.answer("explain like I am 5", None, "age_15", "n_rsi")
    assert simple["source"] == "n_rsi" and "sprinting" in simple["text"]
    assert "covariance" not in a.answer("even simpler", None, "adult", "n_beta")["text"]
    assert "covariance" in a.answer("more detail", None, "age_15", "n_beta")["text"]
    assert a.answer("explain like I am 5")["kind"] == "chat"            # nothing to re-explain yet: asks which term


def test_answers_are_longer_and_link_connected_ideas():
    text = a.answer("what is the sharpe ratio")["text"]
    assert "**In this app:**" in text and "**Connected ideas**" in text and len(text) > 500


def test_even_simpler_uses_a_new_everyday_story_not_the_same_example():
    first = a.answer("what is beta", None, "age_15")
    second = a.answer("simpler", None, "age_15", first["source"], first["level"])
    third = a.answer("even simpler", None, "age_15", second["source"], second["level"])
    assert (first["level"], second["level"], third["level"]) == ("age_15", "age_10", "age_5")
    assert "paper boat" in third["text"] and "boat" in second["text"] and third["text"] != second["text"]
    assert "forget about money" in third["text"] and "Now back to the market" in third["text"]
    assert a.answer("explain rsi like I'm 5")["text"].count("sprinting") == 1


def test_every_simple_story_matches_a_note_and_has_a_link():
    import json
    simple = json.load(open(kb.SIMPLE_PATH))
    for key, v in simple.items():
        assert "n_" + key in kb.BY_ID and len(v["story"]) > 40 and len(v["link"]) > 30, key
