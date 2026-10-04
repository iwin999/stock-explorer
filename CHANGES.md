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

## New in Step 9 (professional redesign)
| Change | Where |
|---|---|
| All emojis removed; calm light theme (navy accent), thin-bordered cards, no developer toolbar for visitors | `core/ui.py`, `.streamlit/config.toml` |
| Four clear tabs: Overview, Possible outcomes, Strategy test, Paper trading | `app.py` |
| Plain-English wording: "Recent strength (RSI)", "Momentum (MACD)", "Trend direction", "Price swings (volatility)", "Moving-average rule"; every signal explained in a sentence | `core/indicators.py`, `app.py` |
| New gauge on the Possible outcomes tab: chance of ending higher/lower, plus up more than 5% / within 5% / down more than 5% | `outlook_gauge` in `core/charts.py`, `outcome_chances` in `core/simulation.py` |
| Simulation now includes the stock's own past-year direction (previously direction-neutral), so the gauge is informative; pass `include_trend=False` for the neutral version | `core/simulation.py` |
| Disclaimer moved from the top banner to a small footer, with fuller wording | `core/ui.py` |
| Price chart's vertical axis now fits the period shown | `zoom_to_window` in `core/charts.py` |

## New in Step 10 (choose your own capital)
| Change | Where |
|---|---|
| Visitors choose their starting capital (Rs 1,000 to Rs 10 crore, default Rs 1,00,000) until their first trade; profit is measured against the chosen amount | `core/trading_ui.py`, `check_capital` in `core/trading.py` |
| "Add virtual cash" takes any amount; "Start over" lets you pick a new capital | `core/trading_ui.py` |

## New in Step 11 (capital first, live prices)
| Change | Where |
|---|---|
| The first screen asks how much virtual money to practise with (presets Rs 50,000 / 1,00,000 / 5,00,000 / 10,00,000 or any amount) before anything else | `capital_gate` in `core/trading_ui.py`, `app.py` |
| Live prices: during NSE hours (Mon-Fri 9:15-15:30 IST) the headline price, account value, profit/loss and holdings refresh themselves every 15 seconds, with a "last updated" time; when the market is closed the last close is shown with a plain note | `core/market_hours.py`, `core/live.py`, `st.fragment(run_every=...)` in `app.py` and `core/trading_ui.py` |
| One shared 15-second price cache so many visitors do not flood Yahoo | `core/live.py` |
| Buy/Sell use a fresh price at the moment of the order | `core/trading_ui.py` |
| Bug fix: Yahoo's quick quote uses camelCase keys (`lastPrice`, `previousClose`); the old code asked for the wrong names and always took the slow route | `get_quote` in `core/market_data.py` |
| Previous-close change now comes from Yahoo's own previous close | `app.py` |

Known limits: NSE holidays are not in the calendar (the app says "open" but prices stay still); the price chart and strategy tab update when the page is used, not every few seconds.

## New in Step 12 (strategy tests, ratios, explanations)
| Change | Where |
|---|---|
| **Strategy tests** tab now has a sub-tab per rule: Moving-average crossover, RSI rule, MACD rule, Bollinger Bands rule, and a Monte Carlo test. Each shows the verdict, growth chart, rule-vs-buy-and-hold table, then "In plain English" and a **Know how** pop-up with the rules, factors, calculation steps and limits | `app.py`, `core/strategies.py` |
| **Possible outcomes** tab now has sub-tabs: Price only, and what each rule would do across the same 2,000 simulated futures (chance of a gain, typical/poor/good case, chance of beating holding) | `strategy_outcomes` in `core/simulation.py` |
| Risk and return ratios under Key signals: yearly return, volatility, max drawdown, VaR; Sharpe, Sortino, Calmar, Treynor; beta, alpha, information ratio, correlation vs the Nifty 50 (3-year default), with a plain-English glossary | `core/ratios.py` |
| Monte Carlo strategy test: 2,000 reshuffled 5-year histories (10-day block bootstrap) show how much a result depends on luck | `bootstrap_test` in `core/backtest.py` |
| Trading cost per switch (default 0.10%) is charged in every test and simulation | `core/backtest.py` |
| Every rule is written once on 2-D arrays and reused for the backtest and the simulation; unit tests check it matches the pandas indicators exactly | `core/strategies.py`, `tests/test_strategies.py` |
| Nifty 50 index added to the offline backup | `scripts/download_offline_data.py` |
| Plain-English drop-downs and Know how pop-ups | `core/ui.py` |

**Adding a rule later (e.g. Fusion analysis):** write a function that takes a price array and returns 1/0 positions, add a `Strategy(...)` entry to `STRATEGIES` in `core/strategies.py` with its plain-English and Know-how text, and it appears automatically in the Strategy tests tab, the Monte Carlo test and the Possible outcomes tab.

## New in Step 13 (multi-asset paper trading and Your Portfolio)
| Change | Where |
|---|---|
| "?" bubble next to every financial term (use, formula, how to read it): signals, ratios, strategy tables, simulation results | `core/glossary.py`, `core/ui.py` |
| First screen: choose a name and starting capital (new user) or reopen a saved portfolio (returning user); Switch user button | `core/trading_ui.py` |
| Paper trading now has Stocks, ETFs and bonds, Futures and Options. Bonds are real NSE bond ETFs (Bharat Bond, G-Sec, liquid) with live prices | `core/instruments.py`, `core/trading_ui.py` |
| Futures and options are **modelled** (Yahoo has no NSE derivatives data): futures = spot x e^(r t), options = Black-Scholes with last-year volatility, lots about Rs 2 lakh, 15% margin, monthly expiry on the last Tuesday. Option buying only; futures long or short. Expired contracts settle automatically; futures that lose all their margin are closed | `core/derivatives.py`, `core/valuation.py` |
| Your Portfolio tab: live value, ring chart of allocation, holdings table, portfolio builder (percentages and picks become orders), leaderboard, look-up of any user, organiser tools (PIN-protected delete, backup, restore) | `core/portfolio_ui.py`, `core/builder.py` |
| Portfolios saved per name: Supabase online database (never lost until deleted) or files on this computer | `core/accounts.py` |
| 27 new tests, including put-call parity for the option formula and a fake Supabase server | `tests/` |

**Not tested against the real Supabase service** (needs your account and keys); the code path is tested against a fake copy of its web interface. Follow DEPLOY.md Step 3 and run the 'Test it' check.

## New in Step 14 (fixes from the flaw review)
| Problem found | Fix | Where |
|---|---|---|
| A deleted portfolio came back when its owner next clicked something | Saving only updates an existing account; if it is gone the user is signed out with a message | `core/accounts.py`, `core/trading_ui.py` |
| Two people choosing the same new name at the same moment could overwrite each other | New accounts use an insert that the database refuses for an existing name | `core/accounts.py` |
| Strategy comparison table became an unlabelled list on phones | Rows stay side by side on small screens | `core/ui.py` |
| Phone tab bar hid "Paper trading" and "Your Portfolio" | Tabs wrap onto extra lines on phones; tab text size now applies on current Streamlit | `core/ui.py` |
| Library versions were not fixed, so a future update could break the online app | Versions pinned to the ones tested; pytest moved to `requirements-dev.txt` | `requirements.txt` |
| Refreshing the browser signed the visitor out | Name is kept in the page address (`?user=Name`), so a refresh signs back in | `core/trading_ui.py` |
| Futures/options silently used the last saved price when no live price was available | A visible note says so | `core/trading_ui.py` |
| Organiser could not tell why the database was not connecting | Organiser tools explain what is missing | `core/portfolio_ui.py` |
| Supabase secret keys in the new `sb_secret_` format were sent the old way | Sent in the apikey header only | `core/accounts.py` |

## New in Step 15 (friendly errors)
| Change | Where |
|---|---|
| Visitors never see a technical error box. Three short messages instead: **Network issue** (with a Try again button), **The app is being updated** (about 2 minutes; contact the admin if longer), and **Congratulations! You have found an error** (contact the admin, with a short reference code such as E-954C1D). The full technical details go only to the server log | `core/errors.py` |
| The page itself moved to `stock_page.py`; `app.py` is now a small safety-net wrapper that runs it. Streamlit still starts from `app.py` | `app.py`, `stock_page.py` |
| The parts that refresh on their own (live prices, dashboard, leaderboard) have the same safety net | `core/trading_ui.py`, `core/portfolio_ui.py` |
| Admin contact shown in the messages: `shahfreya002@gmail.com` (can be overridden with `admin_email` in the app's secrets) | `core/errors.py` |

Limit: while Streamlit is actually rebuilding the app after a push, its own "updating" page is shown by the hosting platform, so it cannot be customised from the app. The in-app "being updated" message appears only for the brief moments when the code changes under a running page.

## New in Step 16 (Ask the bot - free, from the site's own notes)
| Change | Where |
|---|---|
| New **Ask the bot** tab. It answers only from about 100 written notes (finance terms, the simulations and strategy tests, futures and options, how to use the app). No outside service, no key, no cost | `core/knowledge.py`, `core/assistant.py`, `core/assistant_ui.py` |
| Notes for every financial term are generated from the same text as the "?" bubbles, so they always agree | `core/knowledge.py` |
| Finds the closest note by comparing the question with every way each note can be asked (rarer words count more), fixes small spelling slips, and judges whether the question is on-topic. If unsure it asks "did you mean...?"; if it has no note it says so instead of guessing | `core/assistant.py` |
| Live answers from the page: the signals for the selected company, the user's own cash and holdings, whether the market is open | `core/assistant.py` |
| "Should I buy...?", "will it go up?" and similar always get the same careful answer: it cannot advise or predict | `core/knowledge.py` |
| Measured on 112 real questions (including misspellings) and 28 off-topic ones: 112/112 answered with the right note, 28/28 off-topic refused | `tests/bot_eval_data.py`, `tests/test_assistant.py` |
| Follow-up buttons, starter questions, a "Browse all topics" menu and a Clear chat button | `core/assistant_ui.py` |

## New in Step 17 (Fusion analysis, CMT Level III Chapter 8)
Based on the user's own course file (Chapter 8: 8.1 Lundgren, "Bridging the Fundamental Gap"; 8.5 Letizia, "Technicians and Fundamentalists Working Together"). Explanations are paraphrased, not copied, and credit the authors.

| Chapter idea | In the app | Where |
|---|---|---|
| P = (F x V)^S and "the market is the best fundamental analyst" | Explained in the Fusion tab, Know how, and the bot | `core/fusion_ui.py`, `core/knowledge.py` |
| The Winner's Circle (Figure 8.1.2): trend and momentum non-negotiable; groups 1-4 | Group for every company, three circle cards with the numbers, and a screen of all 119 | `core/fusion.py` (`group_of`, `classify`) |
| Four trend stages (Figure 8.1.6) | Counted per company; bar of all companies by stage | `technical_table`, `stage_bar` |
| Technical overlay: confirm / delay / reject, and the divergence rule (8.5) | Verdict and a divergence warning on each company | `verdict_for` |
| Expectancy = win rate x average win - loss rate x average loss | New rows (trades, win rate, average win, average loss, expectancy) in every strategy test | `core/ratios.py`, `core/backtest.py` |
| Trend following vs swing trading | Each rule is labelled; moving-average and MACD = trend following, RSI and Bollinger = swing | `core/strategies.py` |
| 50/50 "never works", top-down approach | Bot notes only | `core/knowledge.py` |
| Model-portfolio test | Monthly-rebuilt equal-weight portfolios of group 1 and groups 1+2, compared with all companies equally and the Nifty 50, about 3 years, trades the day after the rating, with costs | `run_fusion_backtest` |

How it is scored (the chapter's own scores are its authors' proprietary models, so these are open stand-ins): each company is ranked 0-100 against the other companies in our list. Quality = average of growth (revenue and profit growth), returns (ROE and operating margin) and low debt (skipped for banks and lenders). Valuation = low P/E and low price-to-book. 50 or more passes. "In the trend circle" = clear uptrend (price above 200-day average, 50-day above 200-day, 200-day rising) AND positive 6-month return AND 6-month return ahead of the Nifty 50. (RSI was tried and dropped: it left almost no companies in the circle in the current market.)

Data: Yahoo Finance yearly statements (about 4 years) saved in `data/offline/fundamentals.json` by `scripts/download_fundamentals.py`. A year's results are used only 75 days after the year ended. NSE was not scraped because its Terms of Use forbid automated collection. The test starts about mid-2023 because that is how far free published results reach. It is short, covers only today's listed companies (survivorship bias), and uses results as currently reported; the page says so.

Result on the saved data (3 Jul 2023 to 1 Oct 2026, 0.10% cost): group 1 +72.3%, groups 1 and 2 +54.1%, all companies equally +59.3%, Nifty 50 +15.6%.

## New in Step 18 (About page)
| Change | Where |
|---|---|
| A small circled **i** at the top right of every page (also on the first screen). Clicking it opens the **About** page over the current page, not in a new tab | `core/about.py`, `core/ui.py` |
| About has: what the project is, how to use it, limitations, sources and credits (Yahoo Finance, the CMT Level III Chapter 8 authors, standard formulas, software), Meet the creator, and a thank-you note to the school, teachers, family and the community | `core/about.py` |
| Personal touches can be set without editing code: `[about]` in the app's secrets with `creator` (first name), `reason` and `thanks_extra`. By default nothing identifying is shown | `core/about.py` |

## New in Step 19 (creator details and the full bot notes)
| Change | Where |
|---|---|
| About now names the creator: Freya Shah, PreSC Commerce - B, Mayo College Girls School; CMT Level I and II passed, Level III appearing; EPAT Batch 72. Two **?** bubbles explain what CMT and EPAT are. Gratitude thanks the school, its IT department and the visitor | `core/about.py`, `core/ui.py` |
| The bot now has the full notes (about 100 terms and 13 common questions) in one editable file. Every term is explained at three levels (age 10 and under, 11 to 15, 16 and over) plus what it means in this app | `data/bot_notes.json`, `core/knowledge.py` |
| Pick a level above the chat, or type an age ("explain beta like I'm 8", "eli5", "I am 40"). Under each answer, buttons open the related terms | `core/assistant.py`, `core/assistant_ui.py` |
| Notes that no longer matched the app were corrected (futures, options and ETFs now exist; strategy tests do show win rate; creator name filled in) | `data/bot_notes.json` |

The bot remembers the last topic: "explain like I'm 5", "even simpler" or "more detail" re-explain it at the new level. Answers are longer: a lead-in, the explanation, what it means in the app, one line on each connected idea, and a next step.

**Even simpler.** There is now a fourth level for ages 7 and under (`data/bot_simple.json`, about 60 terms). It tells a short everyday story with no finance in it (a cake for a share, a bent coin for the gauge), then says "Now back to the market" and links it. Saying "simpler" steps down one level from the last answer, so teen, then simple, then tiny.

**Colour scales in Risk and return.** The grey sentence under each ratio is replaced by a red-to-green bar with a pointer and a verdict (Poor, Weak, Fair, Good, Excellent). Volatility, worst fall and bad-day loss are flipped, so low is green. Beta and correlation use a blue bar and a description, because they are not good or bad. Ranges are in `SCALES` in `core/ratios.py`.

To change what the bot says, edit `data/bot_notes.json` only. Entries marked "verify" in the original notes were checked against the app.

## New in Step 20 (easier trading, every rule compared, tracking each holding)
| Change | Where |
|---|---|
| **Paper trading, Stocks and ETFs tabs:** choose Buy or Sell, then pick any company or fund from a searchable list (Sell lists only what you own). Quick amounts (Rs 5,000 to 50,000) or Quarter / Half / All for selling, a plain preview ("You will pay about..., cash left after...") and a button that says exactly what it will do | `core/trading_ui.py` |
| **Possible outcomes:** new "All rules side by side" tab: every rule and plain holding in one table (chance of a gain, typical, poor and good case, beats holding), with a "waiting for a signal" label for rules currently in cash | `stock_page.py` |
| **How each holding is doing** (Paper trading and Your Portfolio): per holding the value, gain or loss, today's move, share of the portfolio, effect on total return in points and days held; a green/red contribution chart; pick one holding for a price chart since you bought it, trend, recent speed and a one-line verdict | `core/holdings.py`, `core/holdings_ui.py` |
| **Less jargon:** plain wording first on the ratio cards ("Reward for risk (Sharpe)"), a one-line "In short" at the top of Overview, Possible outcomes, Strategy tests and Paper trading | `stock_page.py`, `core/trading_ui.py` |

## New in Step 21 (hover-to-translate terms, side-by-side outcomes first, fusion rule)
| Change | Where |
|---|---|
| Finance terms on the ratio cards, key signals and strategy tables show the real term (Sharpe ratio, Max drawdown...). Hold the pointer over one for about 2 seconds and it slides smoothly into plain words ("Reward for the risk taken", "The worst fall it had"). On a phone, tap it | `core/ui.py` (`LAYMAN`, `jargon`) |
| **Possible outcomes** now opens with every rule side by side (plus plain holding). Underneath, one expandable item per rule, and one for the price alone, hold the chart, plain English and exact method | `stock_page.py` |
| **New fusion rule** in Possible outcomes: hold only while the price is in a clear uptrend with positive 6-month return AND the company's quality or valuation score passes (groups 1 and 2). The fundamentals gate is today's rating; the trend part is run on each simulated future. Companies with no results data do not get this row | `core/strategies.py` (`fusion_trend`, `FUSION_RULE`), `core/simulation.py` |

## New in Step 22 (Mayo ribbon)
A thin four-colour ribbon (crimson, gold, sky blue, green, taken from the Mayo College crest) runs across the top of every page. Nothing else about the look was changed. `core/ui.py`.

## New in Step 23 (leaderboard rank in the market strip)
The strip at the top now has a fifth card, **Leaderboard**, showing your rank (for example "#2 of 14"). The cards were made a little smaller so every number fits. `core/market_strip.py`, `core/portfolio_ui.py` (`my_rank`).

## New in Step 24 (NSE and BSE)
| Change | Where |
|---|---|
| Search now covers **every NSE and BSE company Yahoo Finance knows**, not just the built-in 119. Type any name; ours come first, then Yahoo's NSE and BSE listings (BSE shown as "Name (BSE: CODE)") | `core/companies.py` (`search`, `code_of`, `label`) |
| Any company you search for can be analysed (charts, signals, risk, simulations, strategy tests) and **bought and sold in paper trading**. The trade picker starts on the company chosen at the top and follows it | `core/trading_ui.py` |
| Names of companies outside the list are looked up once and remembered, so holdings and trades show names, not tickers | `core/instruments.py` (`name_of`) |

Honest limits: Yahoo has no "list every stock" call (BSE has about 5,000), so companies are found as they are searched for, not downloaded in bulk. The 119 built-in companies keep their saved backup prices and the Fusion rating; other companies need Yahoo to be reachable and have no Fusion rating. The portfolio builder and the Nifty/Bank Nifty futures and options still use the built-in lists.

## New in Step 25 (Market carpet, school crest)
| Change | Where |
|---|---|
| New **Market carpet** tab (CMT Level III Ch. 2.3, top-down analysis). The main carpet shows only the industries that have NSE or BSE companies; tile size = combined market value, colour = performance (today, or against the 50-day or 200-day average). Click an industry to open its own carpet of NSE and BSE companies (no company counted twice), with a table and a Back button | `core/market_carpet.py`, `core/carpet_ui.py` |
| Data from Yahoo's screener (11 industries x NSE and BSE, the largest 60 each), with a saved snapshot as fallback. A "Know how", plain-English box and "?" bubble explain it; the bot knows it | `data/offline/market_carpet.json`, `core/knowledge.py`, `core/glossary.py` |
| The Mayo College Girls School crest now sits beside the page title | `assets/mayo-crest.png`, `core/about.py` |
| Market strip cards wrap onto a second row on narrow screens instead of being cut off | `core/market_strip.py` |

## New in Step 26 (NSE and BSE as equals)
Every feature that worked for an NSE company now works for the same company's BSE listing, and wherever NSE is named, BSE is named too.
| Change | Where |
|---|---|
| All 119 built-in companies have a validated BSE twin. Dropdown, search, paper trading, the portfolio builder and futures/options list both listings ("Name (RELIANCE)" and "Name (BSE: RELIANCE)") | `data/offline/bse_twins.json`, `core/companies.py`, `core/instruments.py` |
| A BSE listing is compared with the **Sensex** (an NSE listing with the Nifty 50). Sensex also added to the market strip, and as a futures/options underlying | `core/companies.py` (`benchmark_for`), `stock_page.py`, `core/market_strip.py` |
| Saved prices work for BSE twins (they use the NSE twin's file) and for the Sensex | `core/market_data.py`, `data/offline/IDX_BSESN.csv` |
| Fusion analysis works for BSE listings (via the NSE twin's rating) and now rates **any** NSE or BSE company on demand from Yahoo, ranked against the saved companies | `core/fusion_ui.py` (`rating_row`) |
| Wording: About, bot notes, captions, README and presenting notes now say NSE and BSE; the bot explains the BSE and the Sensex | `core/about.py`, `core/knowledge.py`, `data/bot_notes.json` |

Limits: the Fusion screen and model-portfolio test still use the 119 saved companies (NSE listings); futures and options use the same simplified expiry rule for the Sensex.

## New in Step 27 (gratitude)
The About page Gratitude note now gives Mr. Prashant Kulshrestha a special mention for his guidance, between the thanks to the school and the thanks to the visitor. `core/about.py`.

## New in Step 28 (exit all positions)
| Change | Where |
|---|---|
| A big **Exit all positions** button is the first thing in both the **Paper trading** and **Your Portfolio** tabs. It is greyed out until something is held and turns on as soon as there is a position | `core/trading_ui.py` (`exit_all_control`), `core/portfolio_ui.py` |
| Pressing it opens a simple "Exit all positions?" pop-up with Yes and Cancel. Yes sells every share, ETF and bond fund and closes every future and option at current prices (last close when the market is closed). The money stays as cash with profit or loss included; the starting capital is never reset. A "Last exit" list shows what was sold | `core/valuation.py` (`exit_all`) |
| The page now **stays on the tab you are using** after a click (before, a Buy or Sell jumped back to Overview) | `stock_page.py` (`key="main_tabs"`) |

## New in Step 29 (one search box with suggestions)
| Change | Where |
|---|---|
| The two boxes at the top (a text box and a dropdown) are now **one search box**: start typing and matching companies drop down instantly, NSE and BSE listings together (for example "suzl" shows Suzlon on both). About 7,200 NSE and BSE companies are in it, with the popular ones first | `stock_page.py`, `core/universe.py` |
| The list comes from Yahoo's screener, saved with the app so suggestions are instant and work offline. Run `scripts/download_company_universe.py` now and then to add newly listed companies | `scripts/download_company_universe.py`, `data/offline/company_universe.json` |
| A small "Cannot find a company? Search Yahoo Finance live" box remains for anything newer than the saved list | `stock_page.py` |

## Status
All 8 features are built.
