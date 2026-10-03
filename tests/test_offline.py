import numpy as np
import pandas as pd

from core import market_data as md


def fake_history(n=50):
    idx = pd.bdate_range("2024-01-01", periods=n)
    return pd.DataFrame({"Open": 1.0, "High": 2.0, "Low": 0.5, "Close": np.linspace(1, 2, n),
                         "Volume": 100}, index=idx)


def test_save_and_load_roundtrip(tmp_path):
    h = fake_history()
    md.save_offline("M&M.NS", h, str(tmp_path))
    back = md.load_offline("M&M.NS", str(tmp_path))
    assert (tmp_path / "M_and_M.NS.csv").exists()          # '&' replaced in the file name
    assert len(back) == len(h) and abs(back["Close"].iloc[-1] - 2.0) < 1e-9


def test_missing_or_damaged_file_gives_none(tmp_path):
    assert md.load_offline("NOPE.NS", str(tmp_path)) is None
    (tmp_path / "BAD.NS.csv").write_text("this is not,a price file\n")
    assert md.load_offline("BAD.NS", str(tmp_path)) is None


def test_falls_back_to_offline_when_internet_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(md, "OFFLINE_DIR", str(tmp_path))
    md.save_offline("A.NS", fake_history())
    monkeypatch.setattr(md, "get_history", lambda symbol, period="7y": None)   # pretend: no internet
    hist, source, last = md.get_history_with_source("A.NS")
    assert source == "offline" and hist is not None and last == hist.index[-1]
    assert md.get_history_with_source("UNKNOWN.NS")[1] == "none"


def test_uses_online_when_available(monkeypatch):
    monkeypatch.setattr(md, "get_history", lambda symbol, period="7y": fake_history())
    assert md.get_history_with_source("A.NS")[1] == "online"
