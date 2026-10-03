"""Monte Carlo simulation: "what could the price do, if the future bumps around like the past?"

IDEA (explain this at the exhibition):
  1. Look at how much the stock moved each day over the last year -> its volatility.
  2. Imagine 2,000 possible futures. In each one, every day gets a random
     up/down move whose typical size matches that volatility.
  3. Line up the 2,000 end prices. The middle 70% of them gives a "likely range".

This is NOT a prediction. We deliberately do not assume the stock will keep
rising or falling - only that its bumps stay about the same size as before.
Real markets can jump far more than this model allows (it ignores surprises
like results announcements or crashes).
"""
import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR = 252
LOOKBACK_DAYS = 252  # use the last year of moves to measure volatility


def calendar_to_trading_days(calendar_days):
    """30 calendar days is only about 21 market days (weekends/holidays are closed)."""
    return max(1, round(calendar_days * TRADING_DAYS_PER_YEAR / 365))


def simulate(close, calendar_days=30, n_paths=2000, seed=None):
    """Return an array shaped (n_paths, trading_days + 1). Column 0 is today's price.

    Each day: price_tomorrow = price_today * exp(random move)
    where random move ~ Normal(-0.5 * sigma^2, sigma). The -0.5*sigma^2 is a small
    correction that makes the *average* price stay flat instead of drifting up
    (this is the standard 'geometric Brownian motion' set-up with zero drift).
    """
    daily = np.log(close / close.shift(1)).dropna().iloc[-LOOKBACK_DAYS:]
    sigma = float(daily.std())  # typical size of one day's move

    steps = calendar_to_trading_days(calendar_days)
    rng = np.random.default_rng(seed)  # same seed -> same random numbers (repeatable)
    moves = rng.normal(-0.5 * sigma**2, sigma, size=(n_paths, steps))

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
