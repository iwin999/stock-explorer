# Stock Explorer

An educational stock-analysis app for Indian (NSE and BSE) companies, built for a school exhibition.
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
Online, visitors choose a name and capital and their portfolio is saved under that name (set up the free Supabase database in DEPLOY.md so portfolios are never lost). Locally, portfolios are saved as files in `data/accounts/`.

## Before the exhibition
1. **Refresh the offline backup** (needs internet, ~30 seconds):
   `.venv/bin/python scripts/download_offline_data.py`
   and, for the Fusion analysis tab (3-5 minutes): `.venv/bin/python scripts/download_fundamentals.py`
2. **Clear test portfolios** before the exhibition: Your Portfolio tab -> Organiser tools -> Delete (or delete the files in `data/accounts/` when running locally).
3. **Test offline mode once:** turn off Wi-Fi, restart the app. A yellow "saved data" banner should appear.
4. Press `F11` / full-screen the browser; use `Cmd` `+` to zoom if the room is big.

## What it does
| # | Feature | File |
|---|---|---|
| 1 | One search box that suggests companies as you type: about 7,200 NSE and BSE companies (the 119 popular ones first) | `core/companies.py` |
| 2 | Interactive chart with 50/200-day averages and Bollinger Bands | `core/charts.py` |
| 3 | RSI, MACD, trend, volatility with plain-English meanings | `core/indicators.py` |
| 4 | Possible outcomes tab: Monte Carlo simulation, fan chart and a gauge of the chance of ending higher or lower | `core/simulation.py` |
| 5 | Strategy tests tab: four rules (moving-average, RSI, MACD, Bollinger) vs buy-and-hold over 5 years, plus a Monte Carlo test | `core/strategies.py`, `core/backtest.py` |
| 3b | Risk and return ratios (Sharpe, Sortino, Calmar, Treynor, beta, alpha, drawdown, VaR) | `core/ratios.py` |
| 6 | Paper trading: stocks, ETFs, bond funds, futures and options, with a starting capital the visitor chooses | `core/trading.py`, `core/trading_ui.py`, `core/derivatives.py` |
| 11 | Fusion analysis tab (CMT Level III, Chapter 8): Winner's Circle groups, screen of all companies, model-portfolio test | `core/fusion.py`, `core/fusion_ui.py`, `core/fundamentals.py` |
| 10 | Ask the bot: a free helper that answers from the site's own notes | `core/knowledge.py`, `core/assistant.py` |
| 9 | Your Portfolio tab: many named users, a portfolio builder, live value, leaderboard, look-up, organiser tools | `core/portfolio_ui.py`, `core/accounts.py`, `core/builder.py`, `core/valuation.py` |
| 7 | Offline backup + automatic fallback | `scripts/download_offline_data.py`, `core/market_data.py` |
| 8 | Disclaimer in the footer of the page | `core/ui.py` |

`app.py` starts the app inside a safety net (friendly error messages); `stock_page.py` is the page itself; everything in `core/` is a separate, testable piece.
`CHANGES.md` lists what was kept from last year's `senior_app.py` and what was improved.
`PRESENTING.md` has talking points and likely questions.

## Check that everything works
```bash
.venv/bin/python -m pytest -q      # 71 tests
```

## Troubleshooting
| Problem | Fix |
|---|---|
| "I couldn't load price data" | Check the internet; the app should switch to saved data automatically. If a company has no saved file, run the backup script. |
| A company shows odd/empty results | Tickers change (Tata Motors split into TMPV/TMCV; LTIMindtree is now LTM). Re-run the backup script and see if it reports FAILED. |
| `streamlit: command not found` | Use `.venv/bin/streamlit run app.py` (the virtual environment's copy). |
| Page looks stale after editing code in `core/` | Stop with Ctrl+C and start again. |
