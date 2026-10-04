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
    assert "Level II" in about.creator_markdown() and "Level III" in about.creator_markdown()
    assert "AI coding assistant" in about.creator_markdown()                  # honest about the build
    assert "school" in about.gratitude_markdown() and "teachers" in about.gratitude_markdown()


def test_creator_text_does_not_reveal_personal_details_by_default():
    text = (about.creator_markdown() + about.gratitude_markdown()).lower()
    for private in ("class 11", "grade", "years old", "phone", "address", "mumbai", "delhi"):
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
