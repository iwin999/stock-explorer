# Stock Explorer

An educational stock-analysis app for Indian (NSE) companies, built for a school exhibition.
**Educational project. Not investment advice.**

## Run it (Mac)
Easiest: double-click **`start.command`**. (First time only: right-click it -> Open, if macOS asks.)

Or in Terminal, from this folder:
```bash
python3 -m venv .venv                       # first time only
.venv/bin/pip install -r requirements.txt   # first time only
.venv/bin/streamlit run app.py
```
Your browser opens at http://localhost:8501. Press `Ctrl+C` in Terminal to stop.
(`requirements-lock.txt` lists the exact versions this was built and tested with.)

## Put it online
See **`DEPLOY.md`** to host it on Streamlit Community Cloud so it opens on any computer.
Online, each visitor gets their own private paper-trading account (resets on refresh); running locally with `start.command` saves it to disk.

## Before the exhibition
1. **Refresh the offline backup** (needs internet, ~30 seconds):
   `.venv/bin/python scripts/download_offline_data.py`
2. **Start with a fresh account** if you want: open the Paper trading tab -> Account options -> Reset
   (or delete `data/portfolio.json`).
3. **Test offline mode once:** turn off Wi-Fi, restart the app. A yellow "saved data" banner should appear.
4. Press `F11` / full-screen the browser; use `Cmd` `+` to zoom if the room is big.

## What it does
| # | Feature | File |
|---|---|---|
| 1 | Company search (name/nickname/typos) + dropdown of 119 NSE companies | `core/companies.py` |
| 2 | Interactive chart with 50/200-day averages and Bollinger Bands | `core/charts.py` |
| 3 | RSI, MACD, trend, volatility with plain-English meanings | `core/indicators.py` |
| 4 | Possible outcomes tab: Monte Carlo simulation, fan chart and a gauge of the chance of ending higher or lower | `core/simulation.py` |
| 5 | Strategy test tab: moving-average rule vs buy-and-hold, 5 years | `core/backtest.py` |
| 6 | Paper trading with virtual Rs 1,00,000 (saved between sessions) | `core/trading.py`, `core/trading_ui.py` |
| 7 | Offline backup + automatic fallback | `scripts/download_offline_data.py`, `core/market_data.py` |
| 8 | Disclaimer in the footer of the page | `core/ui.py` |

`app.py` is the page itself; everything in `core/` is a separate, testable piece.
`CHANGES.md` lists what was kept from last year's `senior_app.py` and what was improved.
`PRESENTING.md` has talking points and likely questions.

## Check that everything works
```bash
.venv/bin/python -m pytest -q      # 28 tests
```

## Troubleshooting
| Problem | Fix |
|---|---|
| "I couldn't load price data" | Check the internet; the app should switch to saved data automatically. If a company has no saved file, run the backup script. |
| A company shows odd/empty results | Tickers change (Tata Motors split into TMPV/TMCV; LTIMindtree is now LTM). Re-run the backup script and see if it reports FAILED. |
| `streamlit: command not found` | Use `.venv/bin/streamlit run app.py` (the virtual environment's copy). |
| Page looks stale after editing code in `core/` | Stop with Ctrl+C and start again. |
