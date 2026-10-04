# Presenting Stock Explorer

*This is an educational project, not investment advice, and no real money is involved.* Say this first, every time. The full disclaimer is in the footer.

## 30-second pitch
"Pick any big Indian company. The app draws its price history, tells you in plain English what the
indicators say, shows a range of things that *might* happen next, tests a simple trading rule on
the past, and lets you practise buying and selling with pretend money."

## Suggested demo (3 minutes)
The first screen asks for a starting capital. During market hours (Mon-Fri 9:15-15:30 IST) the price and profit/loss update by themselves; outside those hours it shows the last close.
The page has four tabs: **Overview, Possible outcomes, Strategy tests, Paper trading.**
1. Type **"tata motors"** (then a misspelling like "relience") -> search understands names and typos.
2. **Overview:** the chart (amber/navy lines = 50- and 200-day average price, grey band = usual range), then read one of the four signal cards out loud.
3. **Possible outcomes:** point at the gauge ("out of 2,000 simulated futures, this many ended higher"), then the fan chart. Press **Re-run simulation** to show it is random.
4. **Strategy test:** "Would a simple rule have beaten just holding?" - compare the two lines.
5. **Paper trading:** buy shares, an ETF or bond fund; try a future and an option. Futures and options prices are calculated, not exchange quotes: say so.
6. **Your Portfolio:** a visitor creates a name, builds a portfolio with the sliders, and later comes back to check its value. Show the leaderboard.
7. (Optional) Turn off Wi-Fi on the local version: a notice appears and everything still works.

## New ideas, one line each
- **Sharpe ratio:** return earned per unit of risk, after the safe rate. Above 1 is generally considered good.
- **Sortino ratio:** like Sharpe, but only the falls count as risk.
- **Calmar ratio:** yearly return divided by the worst fall.
- **Treynor ratio and beta:** how strongly the stock moves with the Nifty 50, and the return per unit of that market risk.
- **Alpha:** return beyond what the stock's market risk alone would explain.
- **Max drawdown / VaR:** the worst fall from a peak / the loss on a bad day (1 in 20).
- **Monte Carlo strategy test:** reshuffle the last 5 years into 2,000 alternative histories to see how much a result depended on luck.
- Every rule has a **Know how** button with the exact method, so any detail can be shown on request.

## The ideas in one line each
- **Moving average:** the average of the last N closing prices; smooths out day-to-day noise.
- **Bollinger Bands:** a 20-day average with a band 2 standard deviations either side; wide = volatile.
- **RSI (0-100):** compares recent up-days with down-days. >70 "overbought", <30 "oversold".
- **MACD:** fast average (12 days) minus slow average (26 days); above its 9-day signal line = upward momentum.
- **Volatility:** how much the price swings in a year, as a percentage.
- **Monte Carlo:** make 2,000 imaginary futures using the stock's past bumpiness; the middle 70% of end prices is the "likely range".
- **Backtest:** replay history with a fixed rule. Acts on *tomorrow's* price after a signal (no peeking).

## Fusion analysis (CMT Level III, Chapter 8) in one line each
- **P = (F x V)^S:** a price is built from fundamentals, valuation and sentiment; the price trend is the market's own opinion of all of it.
- **Winner's Circle:** three circles (trend and momentum, quality of fundamentals, valuation). Trend is non-negotiable. Group 1 = all three, 2 = trend plus one, 3 = trend only, 4 = watchlist.
- **Confirm, delay or reject:** let the price trend check a fundamental view; when they disagree, take more care with risk.
- **Expectancy:** (win rate x average win) - (loss rate x average loss). Shown for every strategy test.
- **Trend following vs swing trading:** big winners and bigger falls vs small losses and smaller gains.
- **Be upfront:** the chapter's scores are its authors' own models, so ours are simple open versions; the test covers only about 3 years of published results and today's listed companies.

## Futures, options and bonds in one line each
- **Future:** an agreement to buy or sell at a set price on a set date. Only a margin (15% here) is paid up front, so gains and losses are magnified.
- **Option:** the right (not obligation) to buy (call) or sell (put) at a set price. The most you can lose is the premium paid.
- **Bond fund (ETF):** a fund holding government or company bonds that pays interest; usually steadier than shares.
- **Why are futures and options "calculated"?** No free source has real NSE or BSE derivative prices, so we use the standard formulas from the live share price.

## Questions people may ask
**Is this a prediction?** No. It only shows how bumpy the price *has been*. It cannot know news, results or crashes.

**Why does it say "oversold" for a stock that keeps falling?** RSI only says it has fallen fast. Falling stocks can keep falling.

**The rule beat buy-and-hold, so is it a good strategy?** One stock over 5 years proves little. It tends to lag in steady uptrends. Try a few companies.

**What does the gauge mean?** Of 2,000 simulated futures built from the stock's past year (its average direction and its day-to-day swings), it is the share that ended higher than today. A stock that fell last year leans 'lower'. It describes the past year, not the future.

**Are the prices live?** From Yahoo Finance, can be ~15 minutes late; after market hours it shows the last close.

**Is the money real?** No. Visitors choose their own virtual starting amount (default Rs 1,00,000). Nothing is connected to a broker.

**What did you change from last year's app?** See `CHANGES.md`: saved portfolio, real company names, no freezing, faster price lookups, friendly errors, offline mode, and the whole analysis side is new.

**Why Tata Motors twice?** The company split into passenger vehicles (TMPV) and commercial vehicles (TMCV).

**What are the limits?** Daily data only, NSE and BSE listings (not other markets), no fees/taxes in the backtest, the normal-distribution simulation under-estimates rare big moves.

## If something goes wrong on the day
- Page shows an error: refresh the browser. Still broken: Ctrl+C in Terminal, run `start.command` again.
- No internet: nothing to do; the yellow banner means it switched to saved data.
- Account looks odd: Paper trading -> Account options -> Reset.
