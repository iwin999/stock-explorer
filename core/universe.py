"""Every NSE and BSE company, for the search box that suggests companies as you type.

The list lives in data/offline/company_universe.json (made by scripts/download_company_universe.py from Yahoo
Finance's screener). The popular companies we know best come first; everything else follows in name order.
"""
import json
import os

from core import companies

PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "offline", "company_universe.json")


def _load():
    try:
        with open(PATH) as f:
            return json.load(f)                         # [{"s": symbol, "n": name, "x": exchange, "i": industry}, ...]
    except (OSError, ValueError):
        return []


ROWS = _load()
for _r in ROWS:
    companies.NAME_BY_SYMBOL.setdefault(_r["s"], _r["n"])    # so every company shows its name in dropdowns, trades and holdings


def _options():
    popular = [x for _, s, _ in companies.COMPANIES for x in companies.listings(s)]
    seen = set(popular)
    rest = [r["s"] for r in ROWS if r["s"] not in seen]
    return popular + rest


OPTIONS = _options()
INDUSTRY_OF = {r["s"]: r["i"] for r in ROWS}


# ---------------- forgiving search ----------------
import difflib
import re

_RANK_OF = {s: i for i, s in enumerate(OPTIONS)}                 # popular companies first
_TOKENS = {}                                                     # symbol -> list of words (name words plus ticker)
_INDEX = {}                                                      # word -> symbols that contain it
_JOINED = {}                                                     # symbol -> name without spaces ('tatamotors')


def _words(text):
    return re.findall(r"[a-z0-9]+", (text or "").lower().replace("&", " and "))


_NICKNAMES = {sym: extra for _, sym, extra in companies.COMPANIES}      # e.g. 'zomato blinkit' for Eternal
for _r in ROWS:
    _w = (_words(_r["n"]) + _words(companies.NAME_BY_SYMBOL.get(_r["s"], "")) + _words(_r["s"].rsplit(".", 1)[0])
          + _words(_NICKNAMES.get(_r["s"], "")))
    _TOKENS[_r["s"]] = _w
    _JOINED[_r["s"]] = "".join(_words(companies.NAME_BY_SYMBOL.get(_r["s"], _r["n"])))
    for _t in set(_w):
        _INDEX.setdefault(_t, set()).add(_r["s"])
_VOCAB = list(_INDEX)


def _word_scores(word):
    """{vocabulary word: how well it matches what was typed (0 to 1)}: exact, starts-with, contains, or a close spelling."""
    scores = {}
    for v in _VOCAB:
        if v == word:
            scores[v] = 1.0
        elif v.startswith(word):
            scores[v] = 0.93 - min(0.1, (len(v) - len(word)) * 0.01)
        elif len(word) >= 3 and word in v:
            scores[v] = 0.8
    if len(word) >= 3:
        for v in difflib.get_close_matches(word, _VOCAB, n=12, cutoff=0.6):
            scores[v] = max(scores.get(v, 0), difflib.SequenceMatcher(None, word, v).ratio() * 0.9)
    return scores


def rank(query, limit=8):
    """The companies that best match what was typed, best first. Forgives spelling slips ('relience', 'infosis',
    'tata motor') and runs words together ('tatamotors'). Returns a list of symbols."""
    words = _words(query)
    if not words:
        return []
    per_word = [_word_scores(w) for w in words]
    score = {}
    for sym, tokens in _TOKENS.items():
        total = 0.0
        for w, table in zip(words, per_word):
            best = max((table.get(t, 0.0) for t in tokens), default=0.0)
            if best == 0.0 and len(w) >= 4 and w in _JOINED[sym]:
                best = 0.85
            total += best
        if total:
            score[sym] = total / len(words) - (0.0 if all(any(table.get(t, 0) for t in tokens) for table in per_word) else 0.25)
    joined = "".join(words)
    if len(joined) >= 5:                                         # 'tatamotors' typed as one word
        for sym, name in _JOINED.items():
            if joined in name or name in joined and len(name) >= 5:
                score[sym] = max(score.get(sym, 0), 0.9)
    ranked = sorted((s for s, v in score.items() if v >= 0.65),
                    key=lambda s: (-round(score[s], 2), _RANK_OF.get(s, 10**6), len(companies.NAME_BY_SYMBOL.get(s, ""))))
    return ranked[:limit]


# Old names: companies that were renamed, merged or taken over. Typing the old name finds the company as it is now.
OLD_NAMES = {
    "hdfc ltd": "HDFCBANK.NS", "hdfc limited": "HDFCBANK.NS", "housing development finance": "HDFCBANK.NS",
    "centurion bank of punjab": "HDFCBANK.NS", "ing vysya": "KOTAKBANK.NS",
    "cadila healthcare": "ZYDUSLIFE.NS", "cadila": "ZYDUSLIFE.NS", "bharti infratel": "INDUSTOWER.NS", "infratel": "INDUSTOWER.NS",
    "adani transmission": "ADANIENSOL.NS", "adani gas": "ATGL.NS", "inox leisure": "PVRINOX.NS", "pvr": "PVRINOX.NS",
    "burger king india": "RBA.NS", "motherson sumi": "MOTHERSON.NS", "indiabulls housing": "SAMMAANCAP.NS",
    "indiabulls housing finance": "SAMMAANCAP.NS", "gmr infrastructure": "GMRAIRPORT.NS", "gmr infra": "GMRAIRPORT.NS",
    "essel propack": "EPL.NS", "andhra bank": "UNIONBANK.NS", "corporation bank": "UNIONBANK.NS", "syndicate bank": "CANBK.NS",
    "allahabad bank": "INDIANB.NS", "oriental bank of commerce": "PNB.NS", "united bank of india": "PNB.NS",
    "vijaya bank": "BANKBARODA.NS", "dena bank": "BANKBARODA.NS", "gruh finance": "BANDHANBNK.NS",
    "tata global beverages": "TATACONSUM.NS", "tata global": "TATACONSUM.NS", "idfc bank": "IDFCFIRSTB.NS",
    "ranbaxy": "SUNPHARMA.NS", "hero honda": "HEROMOTOCO.NS", "crompton greaves": "CGPOWER.NS",
}


def renamed(query):
    """(old name, symbols of the company as it is now) if the query is a former company name, else None."""
    q = " ".join(_words(query))
    for old, sym in OLD_NAMES.items():
        if q == old or (len(q) >= 5 and (q in old.split() or q == old.replace(" ", ""))) or (len(old) >= 5 and old in q):
            if sym in _TOKENS:
                return old, companies.listings(sym)
    return None


_plain_rank = rank


def rank(query, limit=8):                                         # noqa: F811  (adds old-name handling to the search above)
    """Best matches first. A former company name puts the company's current listing(s) at the top."""
    hit = renamed(query)
    first = [s for s in hit[1] if s in _TOKENS] if hit else []
    return (first + [s for s in _plain_rank(query, limit) if s not in first])[:limit]
