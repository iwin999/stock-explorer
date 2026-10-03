import json
from datetime import date, datetime

import pytest

from core import accounts as acc, derivatives as dv, instruments as ins, valuation as val
from core.trading import Portfolio, TradingError

NOW = datetime(2026, 10, 5, 11, 0, tzinfo=dv.IST)


# ---------------- storage ----------------
def test_names_are_cleaned_and_validated():
    assert acc.clean_name("  Asha   Rao ") == "Asha Rao"
    for bad in ["", "A", "x" * 25, "<script>"]:
        with pytest.raises(acc.StorageError):
            acc.clean_name(bad)
    assert acc.make_key("Asha  Rao") == acc.make_key("asha rao")


def test_file_store_roundtrip_unique_names_and_delete(tmp_path):
    store = acc.FileStore(str(tmp_path))
    pf = acc.create_account(store, "Asha", 250000)
    assert pf.balance == 250000 and store.names() == ["Asha"]
    with pytest.raises(acc.StorageError):
        acc.create_account(store, "ASHA", 1000)                      # same person, different case
    pf.buy("A.NS", 5, 100.0)
    acc.save_account(store, pf)
    again = acc.load_account(store, "asha")
    assert again.holdings["A.NS"]["quantity"] == 5 and again.name == "Asha"
    acc.create_account(store, "Ravi", 50000)
    assert store.names() == ["Asha", "Ravi"] and len(store.all()) == 2
    store.delete(acc.make_key("Asha"))
    assert store.names() == ["Ravi"] and acc.load_account(store, "Asha") is None


class FakeResp:
    def __init__(self, payload=None, fail=False, status=200):
        self.payload, self.fail, self.status_code = payload, fail, status

    def raise_for_status(self):
        if self.fail:
            raise RuntimeError("boom")

    def json(self):
        return self.payload


class FakeHttp:
    """Pretends to be the Supabase web service so the real code path can be tested offline."""
    def __init__(self):
        self.rows, self.calls = {}, []

    def post(self, url, headers=None, timeout=None, data=None):
        self.calls.append(("post", url, headers))
        upsert = "on_conflict" in url
        for r in json.loads(data):
            if not upsert and r["key"] in self.rows:
                return FakeResp(status=409)                  # a plain insert of an existing key is refused
            self.rows[r["key"]] = r
        return FakeResp()

    def patch(self, url, headers=None, timeout=None, data=None):
        self.calls.append(("patch", url, headers))
        key = url.split("key=eq.")[1].split("&")[0]
        if key not in self.rows:
            return FakeResp([])                              # nothing matched: nothing is created
        self.rows[key]["data"] = json.loads(data)["data"]
        return FakeResp([{"key": key}])

    def get(self, url, headers=None, timeout=None):
        self.calls.append(("get", url, headers))
        if "key=eq." in url:
            key = url.split("key=eq.")[1].split("&")[0]
            return FakeResp([{"data": self.rows[key]["data"]}] if key in self.rows else [])
        return FakeResp(list(self.rows.values()))

    def delete(self, url, headers=None, timeout=None):
        self.calls.append(("delete", url, headers))
        self.rows.pop(url.split("key=eq.")[1], None)
        return FakeResp()


def test_supabase_store_speaks_the_right_requests():
    http = FakeHttp()
    store = acc.SupabaseStore("https://x.supabase.co/", "SECRET", session=http)
    pf = acc.create_account(store, "Meera", 100000)
    method, url, headers = http.calls[-1]
    assert method == "post" and url == "https://x.supabase.co/rest/v1/accounts"      # plain insert, not an upsert
    assert headers["apikey"] == "SECRET" and "merge-duplicates" not in headers["Prefer"]
    assert acc.load_account(store, "meera").balance == 100000
    pf.add_funds(500)
    acc.save_account(store, pf)
    assert http.calls[-1][0] == "patch" and acc.load_account(store, "meera").balance == 100500
    assert store.names() == ["Meera"]
    store.delete(acc.make_key("Meera"))
    assert acc.load_account(store, "Meera") is None


def test_new_style_secret_keys_are_sent_only_as_apikey():
    new = acc.SupabaseStore("https://x.supabase.co", "sb_secret_abc123", session=FakeHttp())
    assert new.headers["apikey"] == "sb_secret_abc123" and "Authorization" not in new.headers
    old = acc.SupabaseStore("https://x.supabase.co", "eyJhbGciOi.payload.sig", session=FakeHttp())
    assert old.headers["Authorization"] == "Bearer eyJhbGciOi.payload.sig"


def test_supabase_failure_becomes_a_friendly_error():
    class Down:
        def get(self, *a, **k):
            return FakeResp(fail=True)
    with pytest.raises(acc.StorageError):
        acc.SupabaseStore("https://x.supabase.co", "k", session=Down()).names()


# ---------------- valuation ----------------
def spots(prices):
    return lambda s: prices.get(s)


def test_snapshot_values_every_asset_class():
    pf = Portfolio(balance=500000)
    pf.buy("RELIANCE.NS", 10, 1000.0)                 # stock
    pf.buy("GOLDBEES.NS", 100, 100.0)                 # ETF
    pf.buy("EBBETF0430.NS", 2, 1500.0)                # bond ETF
    pf.open_future("RELIANCE.NS", "2026-10-27", "LONG", 1, 1000.0, 200, 0.15)
    pf.buy_option("RELIANCE.NS", "2026-10-27", 1000.0, "CALL", 1, 30.0, 200)
    prices = {"RELIANCE.NS": 1100.0, "GOLDBEES.NS": 110.0, "EBBETF0430.NS": 1500.0}
    snap = val.snapshot(pf, spots(prices), lambda s: 0.25, NOW)
    bc = snap["by_class"]
    assert bc[ins.STOCKS] == 11000 and bc[ins.ETFS] == 11000 and bc[ins.BONDS] == 3000
    assert bc[ins.FUTURES] > 30000 and bc[ins.OPTIONS] > 6000      # futures gained, call is now in the money
    assert abs(snap["total"] - sum(bc.values())) < 1e-6 and len(snap["positions"]) == 5
    assert snap["total"] > pf.deposited                             # everything moved in our favour


def test_snapshot_without_prices_shows_no_profit():
    pf = Portfolio(balance=100000)
    pf.buy("A.NS", 10, 100.0)
    pf.buy_option("A.NS", "2026-10-27", 100.0, "CALL", 1, 5.0, 100)
    snap = val.snapshot(pf, spots({}), lambda s: None, NOW)
    assert abs(snap["total"] - 100000) < 1e-6 and (snap["positions"]["P&L"] == 0).all()


def test_expiry_settles_futures_and_options():
    pf = Portfolio(balance=100000)
    pf.open_future("A.NS", "2026-10-27", "LONG", 1, 1000.0, 50, 0.15)
    pf.buy_option("A.NS", "2026-10-27", 1000.0, "CALL", 1, 20.0, 50)
    pf.buy_option("A.NS", "2026-10-27", 1000.0, "PUT", 1, 20.0, 50)
    after = datetime(2026, 10, 27, 16, 0, tzinfo=dv.IST)
    events = val.settle_and_square_off(pf, spots({}), lambda s: 0.25, lambda u, d: 1040.0, after)
    assert len(events) == 3 and pf.derivatives == []
    # future +40*50, call worth 40*50 (paid 20*50), put worthless (paid 20*50)
    assert round(pf.balance, 2) == round(100000 + 40 * 50 + (40 - 20) * 50 - 20 * 50, 2)
    # nothing happens before expiry, or if the settlement price is unknown
    pf2 = Portfolio(balance=100000)
    pf2.buy_option("A.NS", "2026-10-27", 1000.0, "CALL", 1, 20.0, 50)
    assert val.settle_and_square_off(pf2, spots({}), lambda s: 0.25, lambda u, d: 1040.0, NOW) == []
    assert val.settle_and_square_off(pf2, spots({}), lambda s: 0.25, lambda u, d: None, after) == [] and pf2.derivatives


def test_busted_future_is_squared_off_automatically():
    pf = Portfolio(balance=100000)
    pf.open_future("A.NS", "2026-10-27", "LONG", 1, 1000.0, 50, 0.15)     # margin 7,500; 50 units
    events = val.settle_and_square_off(pf, spots({"A.NS": 800.0}), lambda s: 0.25, lambda u, d: None, NOW)
    assert len(events) == 1 and "automatically" in events[0] and pf.derivatives == []
    assert pf.balance == 100000 - 7500


def test_deleted_account_is_not_recreated_by_a_later_save(tmp_path):
    for store in (acc.FileStore(str(tmp_path)), acc.SupabaseStore("https://x.supabase.co", "k", session=FakeHttp())):
        pf = acc.create_account(store, "Ghost", 100000)
        store.delete(acc.make_key("Ghost"))
        pf.add_funds(1000)
        with pytest.raises(acc.AccountGone):
            acc.save_account(store, pf)
        assert store.names() == []                                   # it stayed deleted


def test_two_people_cannot_both_create_the_same_name(tmp_path):
    for store in (acc.FileStore(str(tmp_path / "f")), acc.SupabaseStore("https://x.supabase.co", "k", session=FakeHttp())):
        store.create(acc.make_key("Asha"), "Asha", {"balance": 1})
        with pytest.raises(acc.NameTaken):
            store.create(acc.make_key("asha"), "asha", {"balance": 2})    # the race: skips the name check
        assert store.get(acc.make_key("Asha"))["balance"] == 1            # first person's data untouched


def test_new_accounts_record_when_they_were_created(tmp_path):
    store = acc.FileStore(str(tmp_path))
    pf = acc.create_account(store, "Timed", 100000)
    assert pf.created_at and acc.load_account(store, "Timed").created_at == pf.created_at
