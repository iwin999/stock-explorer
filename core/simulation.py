"""Monte Carlo simulation: "what could the price do, if the future bumps around like the past?"

IDEA (explain this at the exhibition):
  1. Look at how much the stock moved each day over the last year -> its volatility.
  2. Imagine 2,000 possible futures. In each one, every day gets a random
     up/down move whose typical size matches that volatility.
  3. Line up the 2,000 end prices. The middle 70% of them gives a "likely range".

This is NOT a prediction. By default the simulation assumes the stock keeps
behaving as it did over the last year: the same average drift (up or down)
and the same size of daily bumps. Pass include_trend=False for a "no
direction" version where only the bumps are copied. Real markets can jump far
more than this model allows (it ignores surprises like results announcements
or crashes).
"""
import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR = 252
LOOKBACK_DAYS = 252  # use the last year of moves to measure volatility


def calendar_to_trading_days(calendar_days):
    """30 calendar days is only about 21 market days (weekends/holidays are closed)."""
    return max(1, round(calendar_days * TRADING_DAYS_PER_YEAR / 365))


def simulate(close, calendar_days=30, n_paths=2000, seed=None, include_trend=True):
    """Return an array shaped (n_paths, trading_days + 1). Column 0 is today's price.

    Each day: price_tomorrow = price_today * exp(random move)
    where random move ~ Normal(drift, sigma).
      * include_trend=True : drift = the average daily move over the last year
      * include_trend=False: drift = -0.5 * sigma^2, a small correction that keeps
        the *average* price flat (standard 'geometric Brownian motion', zero drift)
    """
    daily = np.log(close / close.shift(1)).dropna().iloc[-LOOKBACK_DAYS:]
    sigma = float(daily.std())  # typical size of one day's move
    drift = float(daily.mean()) if include_trend else -0.5 * sigma**2

    steps = calendar_to_trading_days(calendar_days)
    rng = np.random.default_rng(seed)  # same seed -> same random numbers (repeatable)
    moves = rng.normal(drift, sigma, size=(n_paths, steps))

    start = float(close.iloc[-1])
    paths = start * np.exp(np.cumsum(moves, axis=1))  # running total of moves
    return np.hstack([np.full((n_paths, 1), start), paths])


def likely_range(paths, probability=0.70):
    """The price range that contains `probability` of the simulated end prices."""
    tail = (1 - probability) / 2 * 100          # 70% -> cut 15% off each end
    low, high = np.percentile(paths[:, -1], [tail, 100 - tail])
    return float(low), float(high)


def band(paths, probability):
    """Lower and upper price line (one value per day) holding `probability` of the paths."""
    tail = (1 - probability) / 2 * 100
    return np.percentile(paths, tail, axis=0), np.percentile(paths, 100 - tail, axis=0)


def future_dates(last_date, steps):
    """Business-day dates for the simulated days (Mon-Fri; holidays ignored)."""
    return pd.bdate_range(last_date, periods=steps + 1)


def outcome_chances(paths, threshold=0.05):
    """Share of simulated futures that end higher / lower, and by how much.

    Returns fractions between 0 and 1:
      up        - ended above today's price
      down      - ended below today's price
      big_up    - ended more than `threshold` (5%) above today
      big_down  - ended more than `threshold` below today
      flat      - ended within +/- threshold of today
    """
    start = paths[0, 0]
    end = paths[:, -1]
    change = end / start - 1
    return {
        "up": float((end > start).mean()),
        "down": float((end < start).mean()),
        "big_up": float((change > threshold).mean()),
        "big_down": float((change < -threshold).mean()),
        "flat": float((np.abs(change) <= threshold).mean()),
    }


def strategy_outcomes(close, strategy_key, paths, cost_pct=0.10, prefix_days=400, rule_fn=None):
    """Apply a trading rule to every simulated future and see how it would have fared.

    For each of the 2,000 simulated price paths we join them onto the last ~400 days of real
    history (so the rule's averages are already warmed up), run the same rule used in the
    backtest, and measure the rule's return over the simulated days. We also measure plain
    buy-and-hold over the same days, so the two can be compared path by path.

    Returns a dict of arrays/numbers (all returns as fractions, 0.05 = +5%).
    """
    from core.strategies import STRATEGIES  # imported here to keep this file importable on its own

    rule_fn = rule_fn or STRATEGIES[strategy_key].fn            # a custom rule (the fusion rule) can be passed in
    prefix = close.to_numpy(dtype=float)[-prefix_days:]
    n_hist = len(prefix)
    n_paths, width = paths.shape
    steps = width - 1

    full = np.hstack([np.tile(prefix, (n_paths, 1)), paths[:, 1:]])      # history + simulated days
    pos = rule_fn(full)

    held = pos[:, n_hist - 1: n_hist - 1 + steps]          # position decided yesterday, held today
    before = pos[:, n_hist - 2: n_hist - 2 + steps]        # the position held the day before
    switches = np.abs(held - before)                       # a change in position costs money
    daily = full[:, n_hist:] / full[:, n_hist - 1:-1] - 1

    strategy_ret = np.prod(1 + held * daily - switches * cost_pct / 100.0, axis=1) - 1
    hold_ret = full[:, -1] / full[:, n_hist - 1] - 1

    return {
        "strategy": strategy_ret,
        "hold": hold_ret,
        "chance_gain": float((strategy_ret > 0).mean()),
        "chance_beats_hold": float((strategy_ret > hold_ret).mean()),
        "median": float(np.median(strategy_ret)),
        "poor": float(np.percentile(strategy_ret, 5)),
        "good": float(np.percentile(strategy_ret, 95)),
        "invested": float(held.mean()),
        "starts_invested": bool(pos[0, n_hist - 1] == 1),
    }
