# Presenting Stock Explorer

*This is an educational project, not investment advice, and no real money is involved.* Say this first, every time. The full disclaimer is in the footer.

## 30-second pitch
"Pick any big Indian company. The app draws its price history, tells you in plain English what the
indicators say, shows a range of things that *might* happen next, tests a simple trading rule on
the past, and lets you practise buying and selling with pretend money."

## Suggested demo (3 minutes)
The page has four tabs: **Overview, Possible outcomes, Strategy test, Paper trading.**
1. Type **"tata motors"** (then a misspelling like "relience") -> search understands names and typos.
2. **Overview:** the chart (amber/navy lines = 50- and 200-day average price, grey band = usual range), then read one of the four signal cards out loud.
3. **Possible outcomes:** point at the gauge ("out of 2,000 simulated futures, this many ended higher"), then the fan chart. Press **Re-run simulation** to show it is random.
4. **Strategy test:** "Would a simple rule have beaten just holding?" - compare the two lines.
5. **Paper trading:** buy 5 shares, show the profit/loss table. (Online, each visitor has a private account that resets on refresh.)
6. (Optional) Turn off Wi-Fi on the local version: a notice appears and everything still works.

## The ideas in one line each
- **Moving average:** the average of the last N closing prices; smooths out day-to-day noise.
- **Bollinger Bands:** a 20-day average with a band 2 standard deviations either side; wide = volatile.
- **RSI (0-100):** compares recent up-days with down-days. >70 "overbought", <30 "oversold".
- **MACD:** fast average (12 days) minus slow average (26 days); above its 9-day signal line = upward momentum.
- **Volatility:** how much the price swings in a year, as a percentage.
- **Monte Carlo:** make 2,000 imaginary futures using the stock's past bumpiness; the middle 70% of end prices is the "likely range".
- **Backtest:** replay history with a fixed rule. Acts on *tomorrow's* price after a signal (no peeking).

## Questions people may ask
**Is this a prediction?** No. It only shows how bumpy the price *has been*. It cannot know news, results or crashes.

**Why does it say "oversold" for a stock that keeps falling?** RSI only says it has fallen fast. Falling stocks can keep falling.

**The rule beat buy-and-hold, so is it a good strategy?** One stock over 5 years proves little. It tends to lag in steady uptrends. Try a few companies.

**What does the gauge mean?** Of 2,000 simulated futures built from the stock's past year (its average direction and its day-to-day swings), it is the share that ended higher than today. A stock that fell last year leans 'lower'. It describes the past year, not the future.

**Are the prices live?** From Yahoo Finance, can be ~15 minutes late; after market hours it shows the last close.

**Is the money real?** No. Rs 1,00,000 of virtual cash. Nothing is connected to a broker.

**What did you change from last year's app?** See `CHANGES.md`: saved portfolio, real company names, no freezing, faster price lookups, friendly errors, offline mode, and the whole analysis side is new.

**Why Tata Motors twice?** The company split into passenger vehicles (TMPV) and commercial vehicles (TMCV).

**What are the limits?** Daily data only, NSE only, no fees/taxes in the backtest, the normal-distribution simulation under-estimates rare big moves.

## If something goes wrong on the day
- Page shows an error: refresh the browser. Still broken: Ctrl+C in Terminal, run `start.command` again.
- No internet: nothing to do; the yellow banner means it switched to saved data.
- Account looks odd: Paper trading -> Account options -> Reset.
