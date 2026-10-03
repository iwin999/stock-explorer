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
