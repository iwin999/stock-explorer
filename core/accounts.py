"""Saving and loading every visitor's account.

Two storage back-ends with the same methods:
  * FileStore     - one small file per account in data/accounts/. Used when running on a laptop.
  * SupabaseStore - a free online database (Supabase). Used online so that accounts are never lost,
                    even when the app restarts. Chosen automatically when the secrets are set.

An account is stored under a "key" (the name in lower case with tidy spacing), so "Asha" and
"asha" are the same person.
"""
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from urllib.parse import quote

import requests

ACCOUNTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "accounts")


class StorageError(Exception):
    """Something went wrong saving or loading. The message is safe to show on screen."""


# ---------------- names ----------------
def clean_name(raw):
    """Tidy a name typed by a visitor; raises StorageError (friendly text) if it is not usable."""
    name = re.sub(r"\s+", " ", (raw or "").strip())
    if not (2 <= len(name) <= 24):
        raise StorageError("Please choose a name between 2 and 24 characters.")
    if not re.fullmatch(r"[\w .'\-]+", name):
        raise StorageError("Names can use letters, numbers, spaces and . ' - _ only.")
    return name


def make_key(name):
    return re.sub(r"\s+", " ", name.strip()).casefold()


def _file_name(key):
    return re.sub(r"[^\w\-]+", "_", key) + "_" + format(abs(hash_key(key)) % 10**6, "06d") + ".json"


def hash_key(key):
    """A stable number from text (Python's own hash() changes between runs)."""
    import zlib
    return zlib.crc32(key.encode())


# ---------------- local files ----------------
class FileStore:
    label = "files on this computer"

    def __init__(self, folder=ACCOUNTS_DIR):
        self.folder = folder

    def _path(self, key):
        return os.path.join(self.folder, _file_name(key))

    def put(self, key, name, data):
        os.makedirs(self.folder, exist_ok=True)
        payload = {"key": key, "name": name, "updated_at": _now(), "data": data}
        fd, tmp = tempfile.mkstemp(dir=self.folder, suffix=".tmp")      # write then swap: never half-saved
        with os.fdopen(fd, "w") as f:
            json.dump(payload, f)
        os.replace(tmp, self._path(key))

    def get(self, key):
        try:
            with open(self._path(key)) as f:
                return json.load(f)["data"]
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return None

    def all(self):
        """[{'key', 'name', 'data', 'updated_at'}, ...] for every saved account."""
        out = []
        if os.path.isdir(self.folder):
            for fname in sorted(os.listdir(self.folder)):
                if fname.endswith(".json"):
                    try:
                        with open(os.path.join(self.folder, fname)) as f:
                            out.append(json.load(f))
                    except (json.JSONDecodeError, OSError):
                        continue
        return out

    def names(self):
        return sorted((r["name"] for r in self.all()), key=str.casefold)

    def delete(self, key):
        try:
            os.remove(self._path(key))
        except FileNotFoundError:
            pass


# ---------------- Supabase (online database) ----------------
class SupabaseStore:
    """Talks to a Supabase table through its plain web (REST) interface.

    One-time setup is in DEPLOY.md: a table called `accounts` with columns key, name, data, updated_at.
    """
    label = "online database (Supabase)"

    def __init__(self, url, key, table="accounts", session=None):
        self.base = f"{url.rstrip('/')}/rest/v1/{table}"
        self.headers = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        self.http = session or requests

    def _call(self, method, params="", **kw):
        try:
            resp = getattr(self.http, method)(f"{self.base}{params}", headers=kw.pop("headers", self.headers),
                                              timeout=15, **kw)
            resp.raise_for_status()
            return resp
        except Exception as e:
            raise StorageError("Could not reach the online database. Please try again in a moment.") from e

    def put(self, key, name, data):
        headers = {**self.headers, "Prefer": "resolution=merge-duplicates,return=minimal"}
        row = {"key": key, "name": name, "data": data, "updated_at": _now()}
        self._call("post", "?on_conflict=key", headers=headers, data=json.dumps([row]))

    def get(self, key):
        rows = self._call("get", f"?key=eq.{quote(key, safe='')}&select=data").json()
        return rows[0]["data"] if rows else None

    def all(self):
        return self._call("get", "?select=key,name,data,updated_at&order=name.asc").json()

    def names(self):
        rows = self._call("get", "?select=name&order=name.asc").json()
        return sorted((r["name"] for r in rows), key=str.casefold)

    def delete(self, key):
        self._call("delete", f"?key=eq.{quote(key, safe='')}")


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------- account helpers (work with either store) ----------------
def name_taken(store, name):
    return make_key(name) in {make_key(n) for n in store.names()}


def save_account(store, pf):
    store.put(make_key(pf.name), pf.name, pf.to_dict())


def load_account(store, name):
    """The Portfolio for a name, or None if there is no such account."""
    from core.trading import Portfolio
    data = store.get(make_key(name))
    return Portfolio.from_dict(data) if data else None


def create_account(store, raw_name, capital):
    """Make a new account. Raises StorageError if the name is invalid or already used."""
    from core.trading import Portfolio, check_capital
    name = clean_name(raw_name)
    if name_taken(store, name):
        raise StorageError(f"The name “{name}” is already taken. If that is you, use “Returning user”.")
    pf = Portfolio(balance=check_capital(capital), name=name)
    save_account(store, pf)
    return pf
