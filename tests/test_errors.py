import socket

import requests

from core import errors as er


def test_network_problems_are_recognised_even_when_wrapped():
    assert er.classify(requests.exceptions.ConnectionError("boom")) == er.NETWORK
    assert er.classify(requests.exceptions.ReadTimeout("slow")) == er.NETWORK
    assert er.classify(ConnectionResetError()) == er.NETWORK
    assert er.classify(socket.gaierror(-2, "Name or service not known")) == er.NETWORK
    assert er.classify(RuntimeError("HTTPSConnectionPool: Max retries exceeded with url")) == er.NETWORK
    assert er.classify(Exception("429 Too Many Requests")) == er.NETWORK
    try:
        try:
            raise TimeoutError("read timed out")
        except TimeoutError as inner:
            raise RuntimeError("could not load prices") from inner      # a network error hidden one level down
    except RuntimeError as outer:
        assert er.classify(outer) == er.NETWORK


def test_update_in_progress_is_recognised():
    assert er.classify(ModuleNotFoundError("No module named 'core.something'")) == er.UPDATING
    assert er.classify(ImportError("cannot import name x")) == er.UPDATING
    assert er.classify(SyntaxError("invalid syntax")) == er.UPDATING


def test_everything_else_is_unexpected():
    assert er.classify(ValueError("bad value")) == er.UNEXPECTED
    assert er.classify(KeyError("missing")) == er.UNEXPECTED
    assert er.classify(ZeroDivisionError()) == er.UNEXPECTED


def test_streamlit_control_signals_are_not_swallowed():
    from streamlit.runtime.scriptrunner_utils.exceptions import RerunException, StopException
    assert not issubclass(RerunException, Exception) and not issubclass(StopException, Exception)
