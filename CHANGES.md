# CHANGES.md - What we kept and what we improved

Original: `senior_app.py` (last year's Tkinter paper-trading app).
New version: Streamlit app. *Educational project. Not investment advice.*

## Kept from the original
| Idea | Where it lives now |
|---|---|
| Virtual money to practise with (default Rs 1,00,000) and "add funds" | `core/trading.py` -> `Portfolio`, `add_funds` |
| BUY needs enough cash; SELL needs enough shares | `Portfolio.buy`, `Portfolio.sell` |
| Weighted average buy price when buying more of the same stock | `Portfolio.buy` |
| Profit/loss on a sale = (sell price - average price) x quantity; average stays the same after a partial sale | `Portfolio.sell` |
| Order history that can be exported to CSV | `Portfolio.export_orders_csv` |
| Yahoo Finance search limited to NSE (.NS) / BSE (.BO) | `core/search.py` (will become the *fallback* to our own list of ~100 companies) |

## Improved (Step 1)
| Problem in the original | Fix |
|---|---|
| Trading logic mixed into the screen code | Moved to `core/trading.py` with no screen code, so it can be tested (`tests/test_core.py`, 6 tests) |
| Error handlers used `lambda: show_error(f"...{e}")` - Python deletes `e` when the `except` block ends, so the lambda failed later | No lambdas. Each function catches its own error, logs it, and returns `None`/`[]`; the screen shows a friendly message |
| Company names showed N/A (`fast_info` never has `longName`) | `get_company_name` reads `ticker.info` (long name, then short name, then the ticker) |
| Latest price fetched by downloading 2 days of 1-minute data | `get_latest_price` asks for the single latest price first, then falls back to ~5 daily rows |
| Portfolio and balance lost when the app closed | `Portfolio.save/load` write `data/portfolio.json` (written safely: temp file then swap) |
| Search dropped results that had no long name | Falls back to short name, then the ticker |
| Prices shown as plain 100000 | `core/formatting.py` -> `format_inr` gives Indian style `Rs 1,00,000.00` |
| Whole portfolio re-priced on the main thread every 30 s (window froze) | Streamlit re-runs only on interaction; later we will cache prices (`st.cache_data`) so repeats are instant |
| Unused imports, dead code | Removed |

## New in Step 2 (features 1-3)
| Feature | Where |
|---|---|
| 1. Company list (119 NSE companies, each ticker checked against live data) + search that understands nicknames and spelling mistakes ("relience" finds Reliance). Yahoo search (the senior's) is only the fallback | `core/companies.py` |
| 2. Interactive candlestick chart with 50/200-day averages and Bollinger Bands | `core/charts.py` |
| 3. RSI, MACD, trend, yearly volatility, each with a one-line meaning | `core/indicators.py` (11 tests) |
| Big fonts, Rs formatting, disclaimer top and bottom, friendly errors, cached downloads | `core/ui.py`, `app.py` |

Ticker facts worth knowing: Tata Motors has split (TMPV.NS cars, TMCV.NS trucks) and LTIMindtree is now LTM.NS.

## New in Step 3 (feature 4)
| Feature | Where |
|---|---|
| 4. "What might happen": 2,000 simulated futures from the last year's volatility, a fan chart, and the sentence "roughly a 70% chance the price is between Rs X and Rs Y in N days" (30/60/90 days). Never called a prediction; no up/down drift is assumed | `core/simulation.py` (5 tests), `fan_chart` in `core/charts.py` |

## New in Step 4 (feature 5)
| Feature | Where |
|---|---|
| 5. Backtest: 50/200-day crossover vs buy-and-hold over 5 years, starting with Rs 1,00,000. Shows both equity lines with buy/sell markers, total and yearly return, worst fall, number of switches, and a one-sentence verdict. Signals are acted on the *next* day (no look-ahead); no fees; cash earns 0 | `core/backtest.py` (5 tests), `backtest_chart` in `core/charts.py` |
| Price download is now 7 years (5 to test + 2 to warm up the 200-day average) | `app.py` |

## New in Step 5 (feature 6)
| Feature | Where |
|---|---|
| 6. Paper-trading tab: virtual Rs 1,00,000, BUY/SELL with live price, holdings table with coloured profit/loss, order history (newest first) with CSV download, add-cash and reset buttons. Uses the senior's rules unchanged | `core/trading_ui.py` (screen) + `core/trading.py` (rules) |
| Saved after every trade to `data/portfolio.json`; reloaded when the app opens | `Portfolio.save/load` |
| Profit is measured against money *deposited* (so adding virtual cash isn't counted as profit) | `Portfolio.deposited` |
| Friendly error text in Indian format ("Not enough cash: this order costs Rs ... but you have Rs ...") | `core/trading.py` |
| App split into two tabs: Analyse and Paper trading | `app.py` |

## New in Step 6 (feature 7)
| Feature | Where |
|---|---|
| 7. Offline backup script: downloads 7 years of daily prices for all 119 companies into `data/offline/*.csv` (3 retries each, writes a `_manifest.json` with the download time) | `scripts/download_offline_data.py` |
| Automatic fallback: the app tries the internet first, then the saved file. Visitors see a yellow "saved data up to <date>" warning; analysis, simulation, backtest and paper trading all keep working | `get_history_with_source` in `core/market_data.py` |
| Failed searches offline stay friendly: our own list still works, Yahoo fallback quietly returns nothing | `core/search.py` |
| 4 tests, including one that pretends the internet is down | `tests/test_offline.py` |

Refresh the backup the evening before the exhibition: `.venv/bin/python scripts/download_offline_data.py`

## New in Step 7 (polish)
| Item | Where |
|---|---|
| Larger fonts tuned for an exhibition screen (body, tabs, buttons, metrics, captions) | `core/ui.py` |
| Double-click start script, exact package versions | `start.command`, `requirements-lock.txt` |
| Setup/run/troubleshooting guide and presenting notes | `README.md`, `PRESENTING.md` |

## New in Step 8 (cloud)
| Item | Where |
|---|---|
| Cloud-safe paper trading: per-visitor account kept in memory; saving to disk only when `STOCK_APP_SAVE=1` (set by `start.command`) | `core/trading.py`, `core/trading_ui.py` |
| Banner wording no longer assumes the user's internet is down (cloud servers can be blocked by Yahoo) | `app.py` |
| Deployment guide for Streamlit Community Cloud | `DEPLOY.md` |

## Status
All 8 features are built.
