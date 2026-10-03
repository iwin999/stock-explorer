# Presenting Stock Explorer

*Educational project. Not investment advice.* Say this first, every time.

## 30-second pitch
"Pick any big Indian company. The app draws its price history, tells you in plain English what the
indicators say, shows a range of things that *might* happen next, tests a simple trading rule on
the past, and lets you practise buying and selling with pretend money."

## Suggested demo (3 minutes)
1. Type **"tata motors"** (then a misspelling like "relience") -> search understands names and typos.
2. **Chart:** orange = 50-day average, purple = 200-day, grey band = Bollinger Bands (wide = bumpy).
3. **Indicators:** read one meaning out loud (e.g. "RSI below 30: may be oversold").
4. **What might happen:** point at the fan; press "Run the simulation again" to show it's random.
5. **Backtest:** "Would a simple rule have beaten just holding?" - compare the two lines.
6. **Paper trading:** buy 5 shares, show the profit/loss table. Close and reopen: it's still there.
7. (Optional wow) Turn off Wi-Fi: the banner appears and everything still works.

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

**Why does the simulation not say up or down?** We assume no direction on purpose; only the *size* of daily moves comes from history. Otherwise last year's fall would "predict" more falling.

**Are the prices live?** From Yahoo Finance, can be ~15 minutes late; after market hours it shows the last close.

**Is the money real?** No. Rs 1,00,000 of virtual cash. Nothing is connected to a broker.

**What did you change from last year's app?** See `CHANGES.md`: saved portfolio, real company names, no freezing, faster price lookups, friendly errors, offline mode, and the whole analysis side is new.

**Why Tata Motors twice?** The company split into passenger vehicles (TMPV) and commercial vehicles (TMCV).

**What are the limits?** Daily data only, NSE only, no fees/taxes in the backtest, the normal-distribution simulation under-estimates rare big moves.

## If something goes wrong on the day
- Page shows an error: refresh the browser. Still broken: Ctrl+C in Terminal, run `start.command` again.
- No internet: nothing to do; the yellow banner means it switched to saved data.
- Account looks odd: Paper trading -> Account options -> Reset.
