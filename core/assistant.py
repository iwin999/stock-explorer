"""The "Ask the bot" brain: finds the best answer in the site's own notes (core/knowledge.py).

How it works, in plain terms:
  1. The question is cleaned up: lower case, filler words removed ("what", "the", "does"...), plurals trimmed,
     obvious spelling slips fixed ("shrpe" becomes "sharpe").
  2. It is compared with every way every note can be asked. The note whose wording overlaps most (counting
     rare, meaningful words more than common ones) wins.
  3. If the best match is strong enough, its answer is shown. If it is only a possible match, the bot says what it
     thinks you meant. If nothing matches, the bot says it does not know and lists what it can help with.

The bot only ever repeats the notes, or numbers taken straight from the page. It cannot make things up, never needs
the internet and costs nothing to run.
"""
import difflib
import math
import re

from core import companies, knowledge as kb
from core.market_hours import status_message

MAX_QUESTION_CHARS = 300
STRONG, MAYBE = 0.60, 0.30      # how well a question must match to be answered / suggested

STOPWORDS = set("""
a an the is are was were be been am do does did what whats how why when where which who whom can could would will shall
i me my you your we us our it its this that these those of to in on at for with about and or please tell explain mean means
meaning define simple simply words kindly hello hi hey there some any get got want like just also so if then than as by
from into up out one
""".split())
SYNONYMS = {"shares": "stock", "share": "stock", "stocks": "stock", "equity": "stock", "equities": "stock",
            "colour": "color", "gsec": "gsec", "g-sec": "gsec", "pnl": "profit", "p&l": "profit", "yearly": "annual",
            "annually": "annual", "worst": "worst", "decline": "fall", "drop": "fall", "loss": "loss", "losses": "loss"}


def _stem(word):
    for suffix in ("ing", "ed", "es", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            return word[: -len(suffix)]
    return word


def tokens(text):
    out = []
    for w in re.findall(r"[a-z0-9]+", text.lower().replace("&", " and ").replace("'", "")):
        if w in STOPWORDS:
            continue
        out.append(_stem(SYNONYMS.get(w, w)))
    return out


# ---------------- index built once from the notes ----------------
def _phrasings(entry):
    return [entry["title"]] + entry["questions"]


_INDEX = []                      # (entry, [token lists])
_DF = {}                         # token -> number of entries using it
for _e in kb.ENTRIES:
    _toks = [tokens(p) for p in _phrasings(_e)]
    _INDEX.append((_e, _toks))
    for _t in {t for ts in _toks for t in ts}:
        _DF[_t] = _DF.get(_t, 0) + 1
_N = len(kb.ENTRIES)
_VOCAB = sorted(_DF)
# company names and common finance words count as "on topic" when judging whether a question is off-topic
_DOMAIN = {t for name, symbol, extra in companies.COMPANIES for t in tokens(f"{name} {symbol.replace('.NS', '')} {extra}")}
_DOMAIN |= set(tokens("invest investing investment investor money rupee rupees profit loss gain return risk market price prices "
                      "buy sell hold trade trading portfolio cash fund funds dividend interest rate rates chart charts "
                      "percent percentage average ratio index indices sensex nifty nse bse sebi broker demat ipo"))


def _idf(token):
    return math.log(1 + _N / (1 + _DF.get(token, 0)))


# finance and app terms people are likely to misspell: unknown words are snapped to these generously,
# but only to ordinary words very strictly (otherwise "pasta" would become "past")
_TECH = {t for term in kb.glossary.TERMS.values() for t in tokens(term["title"])} | set(tokens(
    "sharpe sortino calmar treynor beta alpha macd rsi drawdown volatility bollinger candlestick monte carlo option future "
    "margin expiry strike premium leverage diversification backtest benchmark correlation etf bond nifty dividend portfolio "
    "leaderboard simulation strategy crossover momentum"))


def _correct(toks):
    """Fix small spelling slips by snapping unknown words to the closest word the notes know."""
    fixed = []
    for t in toks:
        if t in _DF or t.isdigit() or len(t) < 4:
            fixed.append(t)
            continue
        close = difflib.get_close_matches(t, sorted(_TECH & set(_DF)), n=1, cutoff=0.78)
        if not close and len(t) >= 6:
            close = difflib.get_close_matches(t, _VOCAB, n=1, cutoff=0.85)
        fixed.append(close[0] if close else t)
    return fixed


def _similarity(query, phrase):
    """Weighted overlap (like Dice) between two token lists: 1.0 for identical, 0 for nothing in common."""
    if not query or not phrase:
        return 0.0
    common = set(query) & set(phrase)
    if not common:
        return 0.0
    num = 2 * sum(_idf(t) for t in common)
    den = sum(_idf(t) for t in set(query)) + sum(_idf(t) for t in set(phrase))
    return num / den


def unknown_share(question):
    """0 to 1: how much of the question (counting rarer words more) uses words the notes have never seen.
    Off-topic questions ("write me a poem") score high; real questions about finance or the app score near 0."""
    q = _correct(tokens(question))
    total = sum(_idf(t) for t in q) or 1.0
    unknown = [t for t in q if t not in _DF and t not in _DOMAIN and not t.isdigit()]
    return sum(_idf(t) for t in unknown) / total


def has_finance_word(question):
    """True if the question contains at least one finance or app word (not just everyday words that happen to appear in notes)."""
    return any(t in _TECH or t in _DOMAIN for t in _correct(tokens(question)))


def rank(question, limit=4):
    """Best matching notes as [(score, entry), ...], highest first."""
    q = _correct(tokens(question))
    scored = []
    low = question.lower()
    for entry, phrase_tokens in _INDEX:
        # the tiny second term only breaks ties: of two notes that match equally, the one whose wording is closer wins
        best = 0.0
        for p, raw in zip(phrase_tokens, _phrasings(entry)):
            sim = _similarity(q, p)
            if sim > 0.3:
                sim += 0.01 * difflib.SequenceMatcher(None, low, raw.lower()).ratio()
            best = max(best, sim)
        scored.append((best, entry))
    scored.sort(key=lambda x: -x[0])
    return scored[:limit]


# ---------------- live answers from the page ----------------
_PAT_COMPANY = re.compile(r"\b(this|current|selected|chosen)\s+(stock|company|share)\b|what am i looking at|"
                          r"\b(signals?|rsi|macd|trend)\b.*\b(now|today|currently|right now)\b|"
                          r"\b(now|today|currently)\b.*\b(signals?)\b|summar(y|ise|ize)\b.*\b(page|stock|company)\b")
_PAT_PORTFOLIO = re.compile(r"how am i doing|what do i (own|hold)|\bdo i (own|hold)\b|\bmy (current )?(holdings|cash|balance|"
                            r"portfolio value|positions)\b|how much (cash|money) do i have|\bmy portfolio (now|today)\b")
_PAT_FUSION = re.compile(r"\b(which|what)\b.*\b(group|winner'?s circle)\b.*\b(this|current|selected|it)\b|"
                         r"\b(is|in)\b.*\b(this|the selected|current)\b.*\b(winner'?s circle|group 1|group one)\b|"
                         r"\bfusion\b.*\b(this|current|selected)\b.*\b(stock|company|verdict|group)\b")
_PAT_MARKET = re.compile(r"\bis the (stock )?market (open|closed)\b|\bmarket (open|closed) (now|today)\b|"
                         r"\b(open|closed) right now\b")


def live_answer(question, ctx):
    """An answer built from numbers on the page, or None if the question is not about the page."""
    q = question.lower()
    if _PAT_MARKET.search(q):
        return f"{status_message()}. The NSE and BSE trade Monday to Friday, 9:15 AM to 3:30 PM Indian time."
    if ctx and _PAT_FUSION.search(q) and ctx.get("fusion"):
        f = ctx["fusion"]
        return (f"{ctx['company']} is in fusion group {f['group']} ({f['stage_name'].lower()}). {f['verdict']}. "
                "Open the Fusion analysis tab for the three circles and the scores. This is a way to organise ideas, not advice.")
    if ctx and _PAT_COMPANY.search(q) and ctx.get("company"):
        lines = [f"You are looking at {ctx['company']}. Its last close was Rs {ctx['last_close']:,.2f}."]
        for title, value, meaning in ctx.get("signals", []):
            lines.append(f"- {title}: {value}. {meaning}")
        lines.append("These describe the past; they do not predict the future, and this is not investment advice.")
        return "\n".join(lines)
    if ctx and _PAT_PORTFOLIO.search(q) and ctx.get("portfolio"):
        p = ctx["portfolio"]
        held = ", ".join(f"{s.replace('.NS', '')} ({n})" for s, n in p["holdings"].items()) or "no shares or ETFs"
        return (f"Your cash is Rs {p['cash']:,.0f}. You hold {held}, and have {p['derivatives']} open futures or options. "
                "For live values and profit or loss, open the Your Portfolio tab.")
    return None


GREETING = re.compile(r"^\s*(hi|hello|hey|namaste|good (morning|afternoon|evening)|help|menu)\b[!. ]*$", re.I)
THANKS = re.compile(r"^\s*(thanks?|thank you|thx|ok(ay)?|cool|great|nice|got it)\b[!. ]*$", re.I)


def topics():
    """{category: [note titles]} for the 'browse topics' menu."""
    out = {c: [] for c in kb.CATEGORY_ORDER}
    for e in kb.ENTRIES:
        out[e["category"]].append(e["title"])
    return out


STARTERS = ["What does the RSI number mean?", "Explain the Sharpe ratio like I'm 10",
            "How does the Monte Carlo simulation work?", "What is the difference between a future and an option?"]


_AGE_PATTERNS = [re.compile(p, re.I) for p in (
    r"\b(?:like\s+)?(?:i\s*am|i'm|im)\s+(\d{1,3})(?:\s*(?:years?|yrs?)(?:\s*old)?)?\b",
    r"\b(\d{1,3})[\s-]*(?:years?|yrs?)[\s-]*old\b", r"\bage[d]?\s+(\d{1,3})\b", r"\beli\s*(\d{1,3})\b")]
LEVEL_NAMES = {"age_5": "Tiny (age 7 and under)", "age_10": "Simple (8 to 10)", "age_15": "Teen (11 to 15)", "adult": "Adult (16 and over)"}


def level_for_age(age):
    for band in kb.NOTES_META["age_bands"]:
        if band["min_age"] <= age <= band["max_age"]:
            return band["level"]
    return None


def split_level(question, selected="age_15"):
    """(question without any age phrase, level). An age in the question ("explain like I'm 8") beats the selected level."""
    level = selected if selected in kb.LEVELS else "age_15"
    stripped = question
    for pat in _AGE_PATTERNS:
        m = pat.search(stripped)
        if m:
            lv = level_for_age(int(m.group(1)))
            if lv:
                level = lv
            stripped = (stripped[:m.start()] + " " + stripped[m.end():]).strip(" ,.?!")
            stripped = re.sub(r"[\s,]*\b(explain|like|as|to|for|a|an|if)\s*$", "", stripped, flags=re.I).strip(" ,.?!")
            break
    else:
        low = question.lower()
        for lv, words in kb.NOTES_META["word_hints"].items():
            if any(re.search(rf"\b{re.escape(w)}\b", low) for w in words):
                level = lv
                break
    return stripped, level


LEAD = {"age_5": "Let's forget about money for a moment.",
        "age_10": "Okay, here is the simple version, with an everyday picture:",
        "age_15": "Here is how it works:",
        "adult": "Here is the fuller explanation:"}
NEXT = {"age_5": "That is the simplest I can make it. Want a bit more? Say \"more detail\", or tap a connected idea below.",
        "age_10": "Still tricky? Say \"even simpler\", or tap one of the connected ideas below. For the grown-up version, pick Adult above the chat.",
        "age_15": "Want it simpler or more detailed? Say \"simpler\" or \"more detail\", or tap a connected idea below.",
        "adult": "For a plainer picture, say \"simpler\" or \"like I'm 10\". Tap a connected idea below to go further."}
_ORDER = list(kb.LEVELS)


def _first_sentence(text):
    m = re.match(r"(.+?[.!?])(\s|$)", text.strip())
    return m.group(1) if m else text.strip()


def render(entry, level):
    """The answer text for an entry at a level. Notes with levels give a lead-in, the explanation at that level, what it
    means in this app, a line on each connected idea (same level) and a next step."""
    if "levels" not in entry:
        return entry["answer"]
    if level == "age_5":
        simple = entry.get("simple")
        if simple:
            parts = [LEAD[level], simple["story"], f"**Now back to the market:** {simple['link']}",
                     f"**In this app:** {entry['in_app']}", f"_{NEXT[level]}_"]
            return "\n\n".join(parts)
        parts = ["I do not have a story for this one, so here is my simplest version:", entry["levels"]["age_10"],
                 f"**In this app:** {entry['in_app']}", f"_{NEXT[level]}_"]
        return "\n\n".join(parts)
    parts = [LEAD[level], entry["levels"][level], f"**In this app:** {entry['in_app']}"]
    links = [kb.BY_ID[r] for r in entry.get("related_ids", []) if r in kb.BY_ID and "levels" in kb.BY_ID[r]][:3]
    if links:
        parts.append("**Connected ideas**\n" + "\n".join(f"- **{e['title'].split(' (')[0]}**: {_first_sentence(e['levels'][level])}"
                                                         for e in links))
    parts.append(f"_{NEXT[level]}_")
    return "\n\n".join(parts)


_GENERIC = {"simpl", "simple", "simpler", "simplest", "simply", "easier", "again", "detail", "detailed", "deeper", "more", "differently", "slowly", "eli", "eli5",
            "kid", "child", "little", "baby", "adult", "expert", "teen", "even", "plain", "plainer", "technical", "advanced"}


def follow_up(question, level_before, level, last, last_level=None):
    """If the visitor only asked for a different level or amount of detail ("like I'm 5", "simpler", "more detail"),
    return the reply re-explaining the previous topic. Otherwise None."""
    stripped, _ = split_level(question, level_before)
    rest = [t for t in tokens(stripped) if t not in _GENERIC]
    low = question.lower()
    if rest or not re.search(r"\bi\s*am\b|i'm|\bim\b|\blike\b|\beli\b|simpl|easier|detail|deeper|again|kid|child|baby|adult|expert|"
                              r"teen|technical|advanced|plain", low):
        return None
    if not last or last not in kb.BY_ID or "levels" not in kb.BY_ID[last]:
        return {"kind": "chat", "related": STARTERS, "text":
                "Happy to! Which term should I explain? Try \"explain RSI like I'm 5\" or \"explain beta simply\"."}
    i = _ORDER.index(level)
    if level == level_before and last_level in _ORDER:
        i = _ORDER.index(last_level)                 # "simpler" / "more detail" step from the level I last answered at
    if re.search(r"simpl|easier|plain", low) and level == level_before:
        i = max(0, i - 1)
    elif re.search(r"detail|deeper|technical|advanced", low) and level == level_before:
        i = min(len(_ORDER) - 1, i + 1)
    entry = kb.BY_ID[last]
    return {"kind": "notes", "text": render(entry, _ORDER[i]), "related": related_titles(entry, []), "source": last,
            "level": _ORDER[i]}


def related_titles(entry, ranked, limit=4):
    """Follow-up buttons: the entry's own related terms first, then other close matches."""
    out = [kb.BY_ID[r]["title"] for r in entry.get("related_ids", []) if r in kb.BY_ID]
    out += [e["title"] for s, e in ranked if s >= MAYBE and e["title"] != entry["title"] and e["title"] not in out]
    return out[:limit]


def clean_question(text):
    q = " ".join((text or "").split())
    if not q:
        return "", "Please type a question."
    if len(q) > MAX_QUESTION_CHARS:
        return "", f"Please keep your question under {MAX_QUESTION_CHARS} characters."
    return q, None


def _verdict(score, unknown):
    """Decide how to respond from two numbers: how well the best note matches, and how much of the question is about
    things the notes know nothing about. Tuned against tests/bot_eval_data.py."""
    if score >= STRONG:
        return "notes" if unknown <= 0.35 else "maybe"       # a good match, but much of the question is about something else
    if score >= 0.45:
        return "notes" if unknown <= 0.2 else "maybe" if unknown <= 0.5 else "unknown"
    if score >= MAYBE:
        return "maybe" if unknown <= 0.3 else "unknown"
    return "unknown"


IDENTITY = re.compile(r"\b(your name|who are you|what are you|are you (a )?(bot|robot|ai|human)|what can you do|"
                      r"what do you do|what can i ask)\b", re.I)


def answer(question, ctx=None, level="age_15", last=None, last_level=None):
    """The reply to a question: {"text", "related" (list of note titles), "kind"}.

    kind is "notes" (found in the notes), "live" (numbers from the page), "maybe" (a guess at what was meant),
    "chat" (greeting/thanks) or "unknown".
    """
    if GREETING.match(question):
        return {"kind": "chat", "related": STARTERS,
                "text": "Hello! I can explain finance terms (like RSI or the Sharpe ratio), how the simulations and "
                        "strategy tests work, and how to use this app. What would you like to know?"}
    if THANKS.match(question):
        return {"kind": "chat", "related": [], "text": "You're welcome! Ask me anything else about the app or finance basics."}

    if IDENTITY.search(question):
        return {"kind": "chat", "related": STARTERS,
                "text": "I am the assistant on this site. I am not a person and I am not connected to the internet: I answer "
                        "only from notes written for this app about finance basics, the simulations and strategy tests, "
                        "futures and options, and how to use the site. If something is not in my notes, I will say so."}
    original, level_before = question, level
    question, level = split_level(question, level)
    follow = follow_up(original, level_before, level, last, last_level)
    if follow:
        return follow
    question = question or original
    live = live_answer(question, ctx)
    if live:
        return {"kind": "live", "text": live, "related": []}

    ranked = rank(question)
    best_score, best = ranked[0]
    related = [e["title"] for s, e in ranked[1:] if s >= MAYBE][:3]
    verdict = _verdict(best_score, unknown_share(question))
    if verdict == "maybe" and best_score < 0.45 and not has_finance_word(question):
        verdict = "unknown"                      # a weak guess on everyday words alone is not worth showing
    if verdict == "notes":
        return {"kind": "notes", "text": render(best, level), "related": related_titles(best, ranked) or related,
                "source": best["id"], "level": level}
    if verdict == "maybe":
        guesses = [best["title"]] + related
        return {"kind": "maybe", "related": guesses[:3],
                "text": "I am not completely sure what you mean. Did you mean one of these?"}
    return {"kind": "unknown", "related": STARTERS,
            "text": "I don't have that in my notes yet, so I would rather not guess. I can help with finance terms, how "
                    "the simulations and strategy tests work, futures and options basics, and how to use this app. "
                    "Try one of these, or browse the topics below."}
