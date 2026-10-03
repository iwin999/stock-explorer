"""Is the Indian stock market open right now?

NSE trades Monday to Friday, 9:15 AM to 3:30 PM Indian time (IST). We use this to
decide whether to refresh prices automatically. (Exchange holidays are not
included, so on a weekday holiday the app may say "open" while prices stay still.)
"""
from datetime import datetime, time
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
OPEN_TIME = time(9, 15)
CLOSE_TIME = time(15, 30)


def now_ist():
    return datetime.now(IST)


def is_market_open(now=None):
    now = now or now_ist()
    return now.weekday() < 5 and OPEN_TIME <= now.time() < CLOSE_TIME


def status_message(now=None):
    """A short sentence for the screen."""
    now = now or now_ist()
    if is_market_open(now):
        return "Market open"
    if now.weekday() < 5 and now.time() < OPEN_TIME:
        return "Market closed (opens today at 9:15 AM IST)"
    if now.weekday() in (4, 5, 6):
        return "Market closed (opens Monday at 9:15 AM IST)"
    return "Market closed (opens tomorrow at 9:15 AM IST)"
