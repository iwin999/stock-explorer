"""Formatting helpers.

Indian number style groups digits as 1,00,000 (last 3 digits, then pairs)
instead of the Western 100,000. Python has no built-in for this, so we write it.
"""


def format_inr(amount, decimals=2):
    """Turn a number into 'Rs 1,00,000.00'. Returns 'Rs --' if amount is None."""
    if amount is None:
        return "Rs --"

    negative = amount < 0
    # Round first, then split into whole part and decimal part as text.
    text = f"{abs(amount):.{decimals}f}"
    whole, _, frac = text.partition(".")

    # Last 3 digits stay together; everything before them is grouped in 2s.
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        pairs = []
        while len(head) > 2:
            pairs.insert(0, head[-2:])
            head = head[:-2]
        if head:
            pairs.insert(0, head)
        whole = ",".join(pairs) + "," + tail

    result = f"Rs {whole}" + (f".{frac}" if decimals > 0 else "")
    return f"-{result}" if negative else result


def format_ist(timestamp):
    """Turn a stored time such as '2026-10-03T15:32:22+00:00' into Indian time: '03 Oct 2026, 9:02 PM'.

    Times without a time zone are taken to be UTC (what the database stores). Returns 'not recorded' if empty.
    """
    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo

    if not timestamp:
        return "not recorded"
    try:
        moment = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
    except ValueError:
        return "not recorded"
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    ist = moment.astimezone(ZoneInfo("Asia/Kolkata"))
    return f"{ist:%d %b %Y}, {ist.hour % 12 or 12}:{ist:%M} {ist:%p}"
