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
    for entry, phrase_tokens in _INDEX:
        best = max((_similarity(q, p) for p in phrase_tokens), default=0.0)
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
        return f"{status_message()}. The NSE trades Monday to Friday, 9:15 AM to 3:30 PM Indian time."
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


STARTERS = ["What does the RSI number mean?", "Explain the Sharpe ratio in simple words",
            "How does the Monte Carlo simulation work?", "What is the difference between a future and an option?"]


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
        return "notes"
    if score >= 0.45:
        return "notes" if unknown <= 0.2 else "maybe" if unknown <= 0.5 else "unknown"
    if score >= MAYBE:
        return "maybe" if unknown <= 0.3 else "unknown"
    return "unknown"


IDENTITY = re.compile(r"\b(your name|who are you|what are you|are you (a )?(bot|robot|ai|human)|what can you do|"
                      r"what do you do|what can i ask)\b", re.I)


def answer(question, ctx=None):
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
        return {"kind": "notes", "text": best["answer"], "related": related, "source": best["id"]}
    if verdict == "maybe":
        guesses = [best["title"]] + related
        return {"kind": "maybe", "related": guesses[:3],
                "text": "I am not completely sure what you mean. Did you mean one of these?"}
    return {"kind": "unknown", "related": STARTERS,
            "text": "I don't have that in my notes yet, so I would rather not guess. I can help with finance terms, how "
                    "the simulations and strategy tests work, futures and options basics, and how to use this app. "
                    "Try one of these, or browse the topics below."}
