import os
import tempfile
from unittest import mock

from streamlit.testing.v1 import AppTest

from core import about, accounts as acc

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")


def test_about_covers_everything_requested():
    assert "educational website" in about.WHAT_IT_IS and "nothing here is investment advice" in about.WHAT_IT_IS
    assert "Returning user" in about.HOW_TO_USE and "Ask the bot" in about.HOW_TO_USE and "Know how" in about.HOW_TO_USE
    for needle in ("Not advice", "calculated", "short", "passwords", "own simple versions"):
        assert needle in about.LIMITATIONS, needle
    for needle in ("Yahoo Finance", "Lundgren", "Letizia", "Black-Scholes", "Streamlit", "not affiliated"):
        assert needle in about.SOURCES, needle
    assert "AI coding assistant" in about.creator_story()                       # honest about the build


def test_creator_details_are_exactly_as_given():
    assert about.CREATOR_NAME == "Freya Shah"
    assert about.CREATOR_CLASS == "PreSC Commerce - B" and about.CREATOR_SCHOOL == "Mayo College Girls School"
    assert dict(about.CREDENTIALS) == {"CMT Level I": "Passed", "CMT Level II": "Passed", "CMT Level III": "Appearing"}
    assert about.EPAT_BATCH == "EPAT Batch 72"
    assert about._initials("Freya Shah") == "FS"


def test_explainers_say_what_cmt_and_epat_are():
    assert "Chartered Market Technician" in about.CMT_EXPLAINER and "technical analysis" in about.CMT_EXPLAINER
    assert "Level I" in about.CMT_EXPLAINER and "Level III" in about.CMT_EXPLAINER
    assert "Executive Programme in Algorithmic Trading" in about.EPAT_EXPLAINER and "QuantInsti" in about.EPAT_EXPLAINER
    assert "Batch 72" in about.EPAT_EXPLAINER


def test_gratitude_thanks_the_school_it_department_and_the_visitor():
    g = about.gratitude_markdown()
    assert "Mayo College Girls School" in g and "IT department" in g and "visitor" in g and "opportunity" in g


def test_no_phone_address_or_age_is_shown():
    text = (about.creator_story() + about.gratitude_markdown() + about.CMT_EXPLAINER + about.EPAT_EXPLAINER).lower()
    for private in ("phone", "address:", "years old", "born", "home"):
        assert private not in text


def test_the_icon_is_on_the_first_screen_and_the_main_page_and_opens_without_errors():
    store = acc.FileStore(tempfile.mkdtemp())
    acc.create_account(store, "Reader", 100000)
    with mock.patch("core.trading_ui.get_store", lambda: store), mock.patch("core.portfolio_ui.get_store", lambda: store):
        first = AppTest.from_file(APP, default_timeout=120).run()               # not signed in: the welcome screen
        assert first.button(key="about_btn").label == "i" and not first.exception
        first.button(key="about_btn").click().run()
        assert not first.exception
        main = AppTest.from_file(APP, default_timeout=240)
        main.query_params["user"] = "Reader"
        main.run()
        assert main.button(key="about_btn").label == "i" and not main.exception
        main.button(key="about_btn").click().run()
        assert not main.exception


def _error_cards(app):
    """Text of any friendly error screen the page showed (these hide real errors from visitors, so tests look for them)."""
    texts = [m.value for m in app.markdown] + [m.value for m in app.error]
    return [t for t in texts if "found an error" in t or "Something went wrong" in t or "Reference: E-" in t]


def test_the_signed_in_page_shows_no_error_screens_in_any_tab():
    store = acc.FileStore(tempfile.mkdtemp())
    acc.create_account(store, "Reader2", 100000)
    with mock.patch("core.trading_ui.get_store", lambda: store), mock.patch("core.portfolio_ui.get_store", lambda: store):
        main = AppTest.from_file(APP, default_timeout=240)
        main.query_params["user"] = "Reader2"
        main.run()
        assert not main.exception
        assert _error_cards(main) == [], _error_cards(main)


def test_gratitude_gives_mr_prashant_a_special_mention():
    g = about.gratitude_markdown()
    assert "special mention" in g.lower() and "Mr. Prashant Kulshrestha" in g and "guidance" in g
    assert g.index("IT department") < g.index("Mr. Prashant Kulshrestha") < g.index("visitor")      # school first, then him, then the visitor


def test_exit_all_button_sells_everything_without_errors_and_keeps_the_capital():
    from core.trading import Portfolio
    store = acc.FileStore(tempfile.mkdtemp())
    acc.create_account(store, "Exiter", 200000)
    pf = acc.load_account(store, "Exiter")
    pf.buy("TCS.NS", 10, 100.0)
    pf.buy("INFY.NS", 5, 100.0)
    acc.save_account(store, pf)
    with mock.patch("core.trading_ui.get_store", lambda: store), mock.patch("core.portfolio_ui.get_store", lambda: store), \
            mock.patch("core.trading_ui.spot_price", lambda s: 120.0):
        app = AppTest.from_file(APP, default_timeout=240)
        app.query_params["user"] = "Exiter"
        app.run()
        assert not app.exception and _error_cards(app) == []
        assert app.button(key="exit_all_go").disabled                      # nothing happens until the box is ticked
        app.checkbox(key="exit_all_sure").check().run()
        app.button(key="exit_all_go").click().run()
        assert not app.exception and _error_cards(app) == [], _error_cards(app)
    after = acc.load_account(store, "Exiter")
    assert not after.holdings and not after.derivatives
    assert after.deposited == 200000                                     # the starting capital is not reset
    assert abs(after.balance - (200000 - 10 * 100 - 5 * 100 + 15 * 120)) < 1e-6      # cash plus the sale proceeds
