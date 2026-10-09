"""The bot's notes: every question it can answer, with the answer.

The bot never invents anything. It can only reply with one of the entries below (or with live numbers taken straight
from the page). To teach it something new, add an entry here: give it a short title, a few ways people might ask it,
and the answer.

Entries for the financial terms (RSI, Sharpe ratio and so on) are generated automatically from core/glossary.py, so
the "?" bubbles and the bot always agree.
"""
import json
import os

from core import glossary

# ---- categories shown to visitors ----
USING, SIGNALS, RISK, SIMS, TRADING, DERIV, PORTFOLIO, FUSION = (
    "Using the app", "Charts and signals", "Risk and return numbers", "Simulations and strategy tests",
    "Trading basics", "Futures and options", "Your portfolio", "Fusion analysis")
CATEGORY_ORDER = [USING, SIGNALS, RISK, SIMS, TRADING, DERIV, PORTFOLIO, FUSION]


def E(key, category, title, questions, answer):
    return {"id": key, "category": category, "title": title, "questions": questions, "answer": answer}


MANUAL = [
    # ------------------------------------------------------------------ using the app
    E("what_is_app", USING, "What is Stock Explorer?",
      ["what is this app", "what is stock explorer", "what does this site do", "what can i do here", "tell me about this app",
       "what is this website for", "about this project"],
      "Stock Explorer is an educational website for Indian stocks listed on the NSE and the BSE. You can look at price charts and signals, see a range "
      "of possible outcomes from simulations, test simple trading rules on the past, and practise buying and selling with "
      "virtual money. Nothing here is real money or investment advice."),
    E("tabs", USING, "What are the tabs?",
      ["what are the tabs", "what is in each tab", "how is the app organised", "explain the tabs", "what does each tab do",
       "show me around", "how do i use this app", "how to use", "help me use the app"],
      "Overview: price chart, key signals and risk-and-return numbers. Market carpet: a colour map of industries and companies. Possible outcomes: simulated futures and a gauge. "
      "Strategy tests: trading rules replayed over 5 years. Paper trading: buy and sell with virtual money. "
      "Your Portfolio: build and track your own portfolio and see the leaderboard. Ask the bot: this assistant."),
    E("start_here", USING, "Where should I start?",
      ["where do i start", "what should i try first", "how do i begin", "getting started", "first steps", "what should i do first"],
      "The easiest way: use the 'New here? Three easy steps' box at the top of the page. 1) Pick a company (or press 'Show me a "
      "strong company'). 2) Read the coloured signal bars; if a finance term is new, switch on 'Plain words' at the top and every "
      "term turns into everyday words. 3) Try a practice trade in the Paper trading tab. If you just want to look around, use "
      "'Try a demo account' on the first screen: it opens with a ready-made practice portfolio."),
    E("real_money", USING, "Is this real money?",
      ["is this real money", "will i lose real money", "is it safe", "is anything real", "do i need to pay", "is it free",
       "is my money at risk", "is this a real trading app", "do i invest real money"],
      "No. Everything is virtual money for practice. Nothing connects to a broker or a bank, so you cannot gain or lose "
      "real money here."),
    E("advice", USING, "Is this investment advice? Should I buy something?",
      ["is this investment advice", "should i buy", "should i sell", "which stock should i buy", "best stock to buy",
       "what should i invest in", "will the price go up", "will it go up", "predict the price", "tell me what to buy",
       "is this a good stock", "is reliance a good buy", "recommend a stock", "give me a tip", "buy or sell",
       "can i make money", "is it a good time to invest", "stock tips", "which stock will rise", "is it going to double",
       "will it double", "will it crash", "will the market crash", "is it going up or down", "is it going to rise",
       "should i invest now", "is this a good investment"],
      "I cannot tell you what to buy or sell, and nobody can predict prices. This site is for learning. What I can do is "
      "help you read the numbers: for example, what an RSI of 28 means, or what the simulation does and does not show. "
      "For real decisions, please speak to a qualified, registered adviser."),
    E("who_made", USING, "Who made this?",
      ["who made this", "who built this app", "who created this", "who is the creator", "is this a school project", "who is behind this"],
      "It is an educational project made by a student for a school exhibition. To reach the admin, use the contact shown "
      "at the bottom of the error message, or ask the person running the stall."),
    E("data_source", USING, "Where does the data come from? Are prices live?",
      ["where does the data come from", "are the prices live", "is the data real time", "why are prices delayed", "data source",
       "is this live data", "how accurate are the prices", "where do prices come from", "yahoo finance"],
      "Share, ETF and bond-fund prices come from Yahoo Finance and can be a few minutes late. They update on their own "
      "while the market is open. Futures and options prices are calculated from the live share price, because free "
      "sources have no real NSE or BSE futures or options prices."),
    E("market_hours", USING, "When is the market open? Why are prices not changing?",
      ["when is the market open", "market hours", "trading hours", "why is the price not changing", "why does it say market closed",
       "why is the price not updating", "what time does the market open", "is the stock market open today", "why is nothing moving"],
      "The Indian market (NSE and BSE) trades Monday to Friday, 9:15 AM to 3:30 PM Indian time. Outside those hours, and on "
      "holidays, prices do not move, so the site shows the last closing price. During market hours the headline price, "
      "your portfolio value and the leaderboard refresh by themselves."),
    E("change_company", USING, "How do I change the company?",
      ["how do i change the company", "how do i search for a stock", "how do i pick another stock", "how do i find a company",
       "search for a company", "choose a different stock", "select a company", "look up a stock"],
      "Use the search box at the top of the page: start typing a company name (for example Reliance, Tata or Suzlon) and "
      "pick one from the suggestions. About 7,000 NSE and BSE companies are in it; the BSE listing is shown as (BSE: CODE). "
      "If a company is very new and not in the list, open 'Cannot find a company?' under the box. Everything on the page "
      "updates for the company you pick."),
    E("save_portfolio", USING, "Will my portfolio be saved? How do I come back later?",
      ["will my portfolio be saved", "how do i come back later", "how do i open my portfolio again", "returning user",
       "can i check my portfolio later", "is my portfolio saved", "how do i log in again", "i closed the page what now",
       "how do i see my portfolio at the end", "come back and check my portfolio"],
      "Yes. Your portfolio is saved under the name you chose. To come back, open the site, choose 'Returning user', pick "
      "your name and click 'Open my portfolio'. If you refresh the page, you stay signed in."),
    E("switch_user", USING, "How do I switch user or start a new account?",
      ["how do i switch user", "how do i log out", "how do i make a new account", "can another person use this",
       "how do i create a new user", "change user", "sign out", "different name"],
      "Click 'Switch user' near the top. You will return to the first screen, where you can create a new name or open a "
      "saved one."),
    E("reset_account", USING, "How do I start over or add more cash?",
      ["how do i start over", "reset my account", "how do i add more money", "add virtual cash", "can i change my starting capital",
       "i made a mistake and want to restart", "erase my trades", "change my capital", "get more cash"],
      "Go to Paper trading and open 'Account options' at the bottom. You can add virtual cash, or erase your trades and "
      "start again with a new amount."),
    E("error_help", USING, "Something went wrong. Who do I contact?",
      ["something went wrong", "i found an error", "the app is not working", "it crashed", "bug", "contact admin",
       "who do i contact", "the page is stuck", "i see an error message", "help it is broken", "not loading"],
      "Sorry about that. If you see an error message, it shows the admin's email address and a short reference code. "
      "Please send them both. If the page just seems stuck, try refreshing; you will stay signed in."),
    E("paper_trading", TRADING, "What is paper trading?",
      ["what is paper trading", "what does paper trading mean", "what is virtual trading", "practice trading", "what is simulated trading"],
      "Paper trading means practising with pretend money at real market prices. You can try buying and selling and see "
      "profit and loss, without any real risk. It is a safe way to learn how markets behave."),
    E("leaderboard", PORTFOLIO, "How does the leaderboard work?",
      ["how does the leaderboard work", "how is the leaderboard ranked", "who is winning", "what is the ranking based on",
       "how are people ranked", "what is the leaderboard", "why am i ranked lower"],
      "Everyone's portfolio is ranked by return: how much it has grown or shrunk compared with the money its owner "
      "started with. This means a small portfolio can beat a large one. It refreshes during market hours."),
    E("lookup", PORTFOLIO, "How can someone check a portfolio later?",
      ["how can i look up a portfolio", "can i check someone else's portfolio", "look up a portfolio", "see another user's portfolio",
       "how can the organiser check a portfolio", "find a portfolio by name"],
      "On the Your Portfolio tab, scroll to 'Look up a portfolio', choose a name, and you will see its current value, "
      "return and what it holds. Names have no password, so anyone can look up any name."),
    E("builder", PORTFOLIO, "How does the portfolio builder work?",
      ["how does the portfolio builder work", "how do i build a portfolio", "what do the sliders do", "how do i create my portfolio",
       "how do i invest my money", "how to use the builder", "what is allocation", "how do i split my money"],
      "In 'Build or add to my portfolio', first set how much of your cash goes into stocks, ETFs, bonds, futures and "
      "options. Then pick which ones. The money in each group is split equally between your picks, and the preview shows "
      "exactly what will be bought. Click 'Create my portfolio' to place the orders. Whatever cannot buy a whole unit "
      "stays as cash."),
    E("ring_chart", PORTFOLIO, "What does the ring chart show?",
      ["what does the ring chart show", "what is the donut chart", "what is the pie chart", "what are the colours in the ring",
       "where is my money", "what is the allocation chart"],
      "The ring shows where your money is: stocks, ETFs, bonds, futures, options and cash, as a share of your total "
      "portfolio value. Spreading money across different kinds of investments is called diversification."),
    E("return_pct", PORTFOLIO, "How is my profit or return worked out?",
      ["how is my profit calculated", "what is my return", "how is return calculated", "what does profit and loss mean",
       "how is portfolio value calculated", "what is portfolio value", "what is p and l"],
      "Portfolio value is your cash plus the current value of everything you hold. Profit or loss is that value minus the "
      "money you started with (plus any virtual cash you added), and the return is that as a percentage."),
    E("diversification", PORTFOLIO, "What is diversification?",
      ["what is diversification", "why spread my money", "should i put everything in one stock", "don't put all eggs in one basket",
       "why own different investments", "what does diversify mean"],
      "Diversification means spreading money across different kinds of investments so that one bad result does not hurt "
      "too much. It does not remove risk, but it usually makes the ride smoother."),
    # ------------------------------------------------------------------ charts and signals
    E("candlestick", SIGNALS, "What do the bars on the chart mean?",
      ["what is a candlestick", "what do the bars on the chart mean", "how do i read the chart", "what are the red and green bars",
       "what is a candle", "how to read candlesticks", "what does green and red mean on the chart", "explain the price chart"],
      "Each bar is one trading day. It shows where the price opened, its highest and lowest points that day, and where it "
      "closed. Green means the price closed higher than it opened; red means lower."),
    E("moving_average", SIGNALS, "What are the 50-day and 200-day averages?",
      ["what is a moving average", "what are the orange and navy lines", "what is the 50 day average", "what is the 200 day average",
       "what do the lines on the chart mean", "what is sma", "explain moving averages", "why 50 and 200 days"],
      "A moving average is the average closing price over the last 50 (or 200) days. It smooths out daily noise. The "
      "50-day line shows the recent mood and the 200-day line the long-term mood. When the price is above both, the trend "
      "is up; below both, it is down."),
    E("crossover", SIGNALS, "What is a golden cross or death cross?",
      ["what is a golden cross", "what is a death cross", "what is a crossover", "what is a moving average crossover",
       "what happens when the 50 day crosses the 200 day", "what is the crossover rule"],
      "A golden cross is when the 50-day average rises above the 200-day average, often read as a sign that momentum is "
      "turning up. A death cross is the opposite. The Moving-average crossover test holds the stock after a golden cross "
      "and sits in cash after a death cross."),
    E("bollinger", SIGNALS, "What are Bollinger Bands?",
      ["what are bollinger bands", "what is the grey band on the chart", "what is the usual price range", "explain bollinger bands",
       "what is the shaded area on the chart", "what is the grey area"],
      "The grey band is the price's usual range: a 20-day average with a band 2 standard deviations above and below it. "
      "It widens when the price is swinging a lot and narrows when it is calm. A price outside the band is unusual for "
      "that stock."),
    E("overbought", SIGNALS, "What do overbought and oversold mean?",
      ["what does overbought mean", "what does oversold mean", "what is overbought", "what is oversold", "overbought vs oversold",
       "is the stock overbought", "what is a stretched price"],
      "Overbought means the price has risen quickly and may be stretched, so a pause or dip is possible. Oversold means "
      "it has fallen quickly and may be due a bounce. Both are only hints: a stock can stay overbought or oversold for a "
      "long time. The RSI score is used to judge this."),
    E("last_close", SIGNALS, "What is the 'last close'?",
      ["what is last close", "what does last close mean", "what is closing price", "what is the previous close",
       "why does it say last close", "what is the closing price", "what is the day change"],
      "The closing price is the final price at the end of a trading day (3:30 PM). 'Last close' is the most recent one. "
      "The change shown beside it compares that price with the close before it."),
    E("trend_up_down", SIGNALS, "What does uptrend or downtrend mean?",
      ["what is an uptrend", "what is a downtrend", "what is a sideways trend", "what does trend direction mean",
       "difference between uptrend and downtrend"],
      "An uptrend means prices have been climbing over time; a downtrend means they have been sliding; sideways means "
      "no clear direction. On this site the trend is judged by where the price sits against its 50-day and 200-day "
      "averages."),
    # ------------------------------------------------------------------ risk and return (extras)
    E("risk_free", RISK, "What safe rate is used?",
      ["what is the risk free rate", "what safe rate is used", "why 6.5 percent", "what is the benchmark rate",
       "what interest rate do the ratios use", "what is risk free"],
      "Some ratios need the return of a very safe investment, like a government bond. This site assumes 6.5% a year. "
      "It is a simple assumption and the real figure changes over time."),
    E("nifty", RISK, "What is the Nifty 50?",
      ["what is nifty", "what is the nifty 50", "what is nifty 50", "what is the benchmark", "what is the market index",
       "why compare with nifty", "what is an index"],
      "The Nifty 50 is an index of 50 large Indian companies on the NSE, and the Sensex is the BSE's index of 30 large companies. Either is used as a stand-in for 'the market': NSE listings are compared with the Nifty 50 and BSE listings with the Sensex. "
      "Ratios like beta, alpha and correlation compare a stock with it."),
    E("risk_return", RISK, "What is the link between risk and return?",
      ["what is risk and return", "what is the relationship between risk and return", "higher risk higher return",
       "why do ratios matter", "what is risk adjusted return", "why not just look at return"],
      "Higher possible returns usually come with bigger swings. Looking only at return hides that. Ratios like Sharpe, "
      "Sortino and Calmar ask how much return you got for the risk or pain you took on."),
    # ------------------------------------------------------------------ simulations and strategy tests
    E("monte_carlo", SIMS, "What is a Monte Carlo simulation?",
      ["what is monte carlo", "what is a monte carlo simulation", "how does the simulation work", "what is the simulation",
       "how are the possible outcomes calculated", "explain monte carlo", "how does possible outcomes work",
       "what are the 2000 futures", "how does the simulation predict"],
      "We look at how the stock moved over the past year, its average direction and how much it bounces around daily. "
      "Then we create 2,000 imaginary futures by giving each future day a random move of that typical size. Lining up "
      "where all 2,000 end shows the range of what is possible. It is a way to see possibilities, not to know the future."),
    E("fan_chart", SIMS, "How do I read the fan chart?",
      ["how do i read the fan chart", "what is the shaded fan", "what do the shaded areas mean", "what is the dashed line",
       "what is the median line", "what is the fan", "explain the possible price chart"],
      "The blue line is the recent real price. The shaded fan shows where the simulated price paths go: the darkest area "
      "holds half of them, the next 70% and the lightest 90%. The dashed line is the middle outcome. A wider fan means "
      "more uncertainty."),
    E("gauge", SIMS, "What does the gauge mean?",
      ["what does the gauge mean", "how do i read the gauge", "what is chance of ending higher", "what is the needle",
       "what does the percentage on the gauge mean", "is the gauge a prediction", "what is the barometer"],
      "The gauge shows the share of the 2,000 simulated futures that ended higher than today's price. A stock that fell "
      "over the past year will lean towards 'lower'. It reflects the past year's behaviour; it is not a prediction."),
    E("not_prediction", SIMS, "Is the simulation a prediction?",
      ["is the simulation a prediction", "can i trust the simulation", "is the forecast accurate", "does the simulation predict the price",
       "how accurate is the simulation", "will the price end up in the range", "is this a forecast"],
      "No. It only shows how the price might move if the next weeks behaved like the past year. It cannot see news, "
      "company results or sudden shocks, so real prices can land outside the shaded range. Treat it as a way to think "
      "about uncertainty."),
    E("seventy_percent", SIMS, "What does 'a 70% chance between X and Y' mean?",
      ["what does 70 percent chance mean", "what is the 70 percent range", "explain the range sentence",
       "what does the chance between x and y mean", "how is the 70 percent range worked out"],
      "Of the 2,000 simulated futures, 70% ended between those two prices. We cut off the lowest 15% and the highest "
      "15% of results. It is a statement about the simulation, not a promise about the real price."),
    E("backtest", SIMS, "What is a backtest?",
      ["what is a backtest", "what are strategy tests", "how do strategy tests work", "what is backtesting",
       "what does the strategy test do", "how is the test done", "explain strategy tests"],
      "A backtest replays the past to see what a rule would have done. We start with Rs 1,00,000 five years ago, follow "
      "the rule day by day, subtract trading costs, and compare the result with simply buying and holding. A good past "
      "result does not mean a good future result."),
    E("buy_and_hold", SIMS, "What is buy and hold?",
      ["what is buy and hold", "what does buy and hold mean", "why compare with buy and hold", "what is the buy and hold line",
       "what is the grey line in the strategy test"],
      "Buy and hold means buying on the first day and never selling. It is the simplest strategy, so any rule has to "
      "beat it to be worth the effort. It is the grey line in the strategy charts."),
    E("trading_costs", SIMS, "What are trading costs in the tests?",
      ["what are trading costs", "why are there costs in the strategy test", "what is the trading cost box",
       "what does cost per switch mean", "do the tests include fees", "what is brokerage"],
      "Every time a rule switches between stock and cash, a small cost is charged (0.10% by default) to stand in for "
      "brokerage, taxes and the gap between buy and sell prices. You can change it on the Strategy tests tab. Without "
      "costs, rules that trade often look better than they really are."),
    E("next_day", SIMS, "Why are signals acted on the next day?",
      ["why next day", "what is look ahead bias", "is the backtest fair", "does the backtest cheat",
       "why do trades happen the day after the signal", "what is lookahead"],
      "A signal is only known at the end of a day, so a real trader could only act the next day. Acting on the same "
      "day's price would be cheating, because it uses information that was not available in time. The tests always wait "
      "one day."),
    E("rule_ma", SIMS, "How does the moving-average rule work?",
      ["how does the moving average rule work", "explain the moving average crossover strategy", "what is the crossover strategy",
       "how does the 50 200 rule work", "what is the moving average strategy"],
      "Hold the stock while its 50-day average price is above its 200-day average; otherwise stay in cash. It tries to "
      "catch long climbs and avoid long slides, but it is slow, so it can miss quick moves."),
    E("rule_rsi", SIMS, "How does the RSI rule work?",
      ["how does the rsi rule work", "explain the rsi strategy", "what is the rsi strategy", "when does the rsi rule buy"],
      "Buy after the stock has fallen hard (RSI below 30) and sell once it recovers (RSI above 55). It is a bounce-back "
      "idea: it can do well in choppy markets and badly when a stock keeps falling."),
    E("rule_macd", SIMS, "How does the MACD rule work?",
      ["how does the macd rule work", "explain the macd strategy", "what is the macd strategy", "when does the macd rule buy"],
      "Hold the stock while the MACD line is above its signal line, otherwise stay in cash. It reacts faster than the "
      "moving-average rule, so it trades more often and costs matter more."),
    E("rule_bollinger", SIMS, "How does the Bollinger Bands rule work?",
      ["how does the bollinger rule work", "explain the bollinger strategy", "what is the bollinger strategy",
       "when does the bollinger rule buy"],
      "Buy when the price drops below the lower band and sell when it returns to the middle (the 20-day average). It "
      "suits calm, range-bound stocks and struggles when a stock is in a real breakdown."),
    E("mc_test", SIMS, "What is the Monte Carlo test in Strategy tests?",
      ["what is the monte carlo test", "what does shuffle again do", "what is reshuffling history", "what is the strategy monte carlo",
       "why reshuffle the past", "what is a bootstrap", "how robust is the result"],
      "The real five years happened only once, so a good result could be partly luck. This test cuts those years into "
      "short chunks and shuffles them into 2,000 alternative histories. If the rule does well in most of them, its "
      "result is more believable."),
    E("past_future", SIMS, "Does a good past result mean a good future result?",
      ["does past performance predict the future", "will the strategy work in the future", "is a good backtest reliable",
       "can i trust the strategy tests", "what is overfitting", "will this rule make money"],
      "No. Past results describe the past. Markets change, and a rule that worked on one stock in one period may fail "
      "on another. The tests are for learning how rules behave, not for choosing real investments."),
    E("percentile", SIMS, "What does 'poor case (1 in 20)' mean?",
      ["what does 1 in 20 mean", "what is a percentile", "what is poor case", "what is good case", "what is the 5th percentile",
       "what does the 95th percentile mean"],
      "Line up all results from worst to best. The 'poor case' is the result that only 1 in 20 did worse than, and the "
      "'good case' is the one that only 1 in 20 did better than. They show a pessimistic and an optimistic but possible "
      "outcome."),
    # ------------------------------------------------------------------ trading basics
    E("stock", TRADING, "What is a stock (share)?",
      ["what is a stock", "what is a share", "what does owning a share mean", "what is equity", "what is a company stock"],
      "A share is a small piece of ownership in a company. If the company does well and others want its shares, the "
      "price may rise; if not, it may fall. Companies may also pay dividends, which this site does not model."),
    E("etf", TRADING, "What is an ETF?",
      ["what is an etf", "what does etf stand for", "what is an exchange traded fund", "what is niftybees", "what is an index fund",
       "how is an etf different from a stock", "what are gold etfs"],
      "An ETF is a fund that trades on the stock exchange like a share. It holds a basket, for example the Nifty 50 "
      "companies, or gold or silver. Buying one unit gives you a small share of the whole basket."),
    E("bond", TRADING, "What is a bond or bond fund?",
      ["what is a bond", "what is a bond etf", "what are bonds", "what is a government bond", "what is bharat bond",
       "what is a liquid etf", "what is gsec", "are bonds safer than stocks", "what is fixed income"],
      "A bond is a loan to a government or company that pays interest. Bond ETFs on this site hold such loans, for "
      "example Bharat Bond or government securities, and have live prices. Bonds are usually steadier than shares, but "
      "their prices still move, especially when interest rates change. Liquid ETFs behave like cash."),
    E("nse", TRADING, "What is the NSE?",
      ["what is nse", "what is the nse", "what is the national stock exchange", "what is nse india", "what is bse"],
      "The NSE (National Stock Exchange of India) is where most Indian shares are traded. The .NS you may see after a "
      "name, such as RELIANCE.NS, tells the data provider it is the NSE listing. The BSE (Bombay Stock Exchange) is India's "
      "older exchange; its listings end in .BO, such as RELIANCE.BO. Most large companies are listed on both, and in this site "
      "every feature works for both listings."),
    E("sell_rule", TRADING, "Why can't I sell something I don't own?",
      ["why can't i sell", "why is the sell button grey", "why is sell disabled", "can i short sell shares",
       "can i sell without buying", "why can i not sell"],
      "For normal share trading you must own a share before you can sell it, and this site follows that rule. The Sell "
      "button works once you own some. Futures are different: you can take a 'short' position to gain if the price falls."),
    E("avg_price", TRADING, "What is the average price?",
      ["what is average price", "what is avg price", "what does bought at mean", "how is the average buy price calculated",
       "what happens when i buy more of the same stock"],
      "If you buy the same share at different prices, the average price is the total you paid divided by the number of "
      "units. Profit or loss is measured against it. Selling part of your holding does not change the average of the rest."),
    # ------------------------------------------------------------------ futures and options
    E("future", DERIV, "What is a future?",
      ["what is a future", "what is a futures contract", "what are futures", "how do futures work", "explain futures",
       "what is a futures position"],
      "A future is an agreement to buy or sell something at a set price on a set date. You put down a margin (a "
      "deposit) instead of the full value, so gains and losses are bigger compared with the money you put in. Profit or "
      "loss is settled in cash when you close or when the contract expires."),
    E("option", DERIV, "What is an option? What are calls and puts?",
      ["what is an option", "what is a call option", "what is a put option", "what are calls and puts", "difference between call and put",
       "how do options work", "explain options", "what is a call", "what is a put"],
      "An option is the right, but not the obligation, to buy (a call) or sell (a put) at a set price on or before a "
      "date. You pay a price for that right, called the premium. A call gains if the price rises; a put gains if it falls. "
      "The most you can lose is the premium."),
    E("future_vs_option", DERIV, "What is the difference between a future and an option?",
      ["difference between a future and an option", "futures vs options", "future or option", "how are futures different from options",
       "options vs futures", "which is riskier futures or options"],
      "A future is an obligation: you gain or lose as the price moves, and losses can be large compared with the margin. "
      "An option is a right: you pay a premium up front and can lose at most that, but it can lose its whole value "
      "quickly, especially near expiry."),
    E("long_short", DERIV, "What does long and short mean?",
      ["what does long mean", "what does short mean", "what is a long position", "what is a short position",
       "what is going long", "what is shorting", "what is short selling"],
      "Going long means you profit if the price rises. Going short means you profit if it falls. On this site you can "
      "take either side in futures, but options can only be bought."),
    E("margin", DERIV, "What is margin?",
      ["what is margin", "what is a margin", "how much margin do i need", "what is the margin to block",
       "what does margin mean", "why is cash blocked"],
      "Margin is a deposit set aside to open a futures position, here 15% of the contract's value. It is returned (plus "
      "profit or minus loss) when you close. If losses use up the whole margin, the position is closed automatically."),
    E("lot", DERIV, "What is a lot?",
      ["what is a lot", "what is lot size", "what does one lot mean", "why do i have to buy in lots", "how many units in a lot"],
      "Futures and options trade in fixed bundles called lots. Here a lot is sized to be worth roughly Rs 2 lakh. Real "
      "lot sizes are set by the exchange and are larger, so the site uses a simpler version."),
    E("expiry", DERIV, "What is expiry?",
      ["what is expiry", "what does expire mean", "when do futures and options expire", "what is the expiry date",
       "what happens at expiry", "what happens when a contract expires", "what is settlement"],
      "Futures and options have an end date. Here contracts expire on the last Tuesday of the month at 3:30 PM. After "
      "that they are settled automatically at that day's closing price: a future pays its profit or loss, and an option "
      "is worth only its intrinsic value (zero if it has no value)."),
    E("strike", DERIV, "What is a strike price?",
      ["what is strike price", "what is a strike", "what does at the money mean", "what is atm", "which strike should i choose",
       "what is in the money"],
      "The strike is the fixed price in an option. A strike close to the current price is called 'at the money'. For a "
      "call, a strike below the price is 'in the money' (it already has value); the reverse is true for a put."),
    E("premium", DERIV, "What is the premium?",
      ["what is premium", "what is the option premium", "what does premium mean", "how is the premium calculated",
       "why is the premium so high", "why is the premium low", "what is break even"],
      "The premium is the price you pay for an option. It is higher when there is more time left, when the stock is more "
      "volatile, and when the strike is closer to the price. Break-even at expiry is the strike plus the premium for a "
      "call, or the strike minus the premium for a put."),
    E("calculated_prices", DERIV, "Why are futures and option prices 'calculated'?",
      ["why are futures prices calculated", "are option prices real", "how are option prices worked out", "are futures prices real",
       "what is black scholes", "what is cost of carry", "are derivative prices real", "why are the prices not real"],
      "Free data sources have no real NSE or BSE futures or options prices. So the site uses standard formulas on the live "
      "share price: a future's price is spot x e^(rate x time left), and an option's premium comes from the "
      "Black-Scholes formula with the stock's last-year volatility. They are fair-value estimates; real prices also "
      "reflect demand and traders' views."),
    E("leverage", DERIV, "Why are futures and options risky?",
      ["why are futures risky", "why are options risky", "what is leverage", "can i lose more than i invest", "are derivatives dangerous",
       "what is the risk in options"],
      "Leverage means a small deposit controls a large position, so small price moves create big gains or losses. "
      "Options can lose their entire premium; real futures can lose more than the margin. That is why they are best "
      "learned about with virtual money first."),
    E("buy_only_options", DERIV, "Why can I only buy options?",
      ["why can i only buy options", "can i sell options", "can i write options", "what is selling an option",
       "why can't i sell options", "what is option writing"],
      "Selling (writing) options can lose far more than you receive, sometimes without limit. To keep practice safe, "
      "the site allows only buying options, where the most you can lose is the premium you paid."),
    # ------------------------------------------------------------------ fusion analysis (CMT Level III, Chapter 8)
    E("fusion_what", FUSION, "What is fusion analysis?",
      ["what is fusion analysis", "explain fusion analysis", "what does fusion mean", "what is the fusion tab",
       "technical and fundamental together", "combining technical and fundamental analysis", "how does fusion analysis work",
       "what is cmt fusion", "what is the fusion method"],
      "Fusion analysis combines the different ways of studying a stock: its price trend (technical), its business results "
      "(fundamental), its price against its earnings (valuation) and the wider economy. The idea from the CMT Level III "
      "curriculum is that the price trend is the market's own opinion of all the rest, so a view on a company only pays "
      "off once the market agrees. The Fusion analysis tab rates each company this way."),
    E("fusion_formula", FUSION, "What does P = (F x V)^S mean?",
      ["what does p equals f times v to the s mean", "what is the p f v s formula", "explain the price formula",
       "what is the elegant formula", "what is sentiment in the formula", "p = (f * v)s", "what is f v and s",
       "how is a stock price built"],
      "A price (P) is built from fundamentals (F: growth, returns, leverage), valuation (V: what investors pay for them) and "
      "sentiment (S: how confident or fearful the crowd is). In bull markets S is above 1 and pushes the price up faster; in "
      "bear markets S is below 1. The market's price therefore reflects everything people know, and a lot they do not."),
    E("winners_circle", FUSION, "What is the Winner's Circle?",
      ["what is the winners circle", "what are the four groups", "explain groups 1 2 3 and 4", "what does group 1 mean",
       "what is the venn diagram", "what do the circles mean", "what is a group 4 stock", "what is a group 1 stock",
       "what is the fusion group", "how are companies grouped"],
      "Three circles: quality of fundamentals, valuation, and price trend and momentum. The trend circle is not negotiable. "
      "Group 1 = trending and outperforming with both fundamental quality and valuation. Group 2 = trending with at least "
      "one of them. Group 3 = trending with neither. Group 4 = not trending: a watchlist. Aim for many 1s, some 2s, few 3s, "
      "and avoid 4s."),
    E("why_trend_first", FUSION, "Why is the price trend 'non-negotiable'?",
      ["why is the trend not negotiable", "why must a stock be trending", "why not buy cheap stocks that are falling",
       "why does the trend matter", "why avoid group 4", "why listen to the market", "why not just trust fundamentals",
       "is the market the best analyst"],
      "No stock becomes a big winner without first getting back into an uptrend, and a view on fundamentals earns nothing "
      "until the market agrees with it. The chapter calls the market the best fundamental analyst on the planet, because "
      "the price already holds everything investors know. Buying cheap stocks that are still falling is the contrarian "
      "route, which the chapter warns about."),
    E("overlay", FUSION, "What does confirm, delay or reject mean?",
      ["what is the technical overlay", "what does confirm mean", "what does delay mean", "what does reject mean",
       "what is the overlay verdict", "how do technicals confirm fundamentals", "what is the verdict on the fusion tab"],
      "This is the technical overlay from Chapter 8.5. A view formed on fundamentals is checked against the price trend "
      "before acting. Confirm: the trend agrees. Delay: the fundamentals look good but the trend has not confirmed yet, so "
      "wait. Reject: neither supports it. The verdict is a way to organise thinking, not an instruction to trade."),
    E("divergence", FUSION, "What if the technicals and fundamentals disagree?",
      ["what if technicals and fundamentals disagree", "what is divergence", "what does divergence mean",
       "what to do when signals conflict", "why is there a divergence warning", "technicals and fundamentals diverge",
       "what is the divergence message"],
      "The chapter's advice is to pay more attention to risk: smaller positions, tighter stops, and a fresh look at the "
      "evidence. Disagreements usually appear near the end of a move, and eventually the two come back into line. The page "
      "shows a divergence warning when a company is trending without strong fundamentals, or has strong fundamentals but no trend."),
    E("trend_stages", FUSION, "What are the four trend stages?",
      ["what are the trend stages", "what is a clear uptrend", "what is a base of an uptrend", "what is a base of a downtrend",
       "what is a clear downtrend", "how is the trend stage decided", "what are the four stages"],
      "Three tests are counted: price above its 200-day average, the 50-day average above the 200-day, and the 200-day "
      "average rising. All three = clear uptrend. Two = base of an uptrend. One = base of a downtrend. None = clear "
      "downtrend. Only a clear uptrend can be inside the Winner's Circle."),
    E("fusion_scores", FUSION, "How are the 0-100 scores worked out?",
      ["how are the fusion scores calculated", "what is the quality score", "what is the valuation score",
       "how is quality of fundamentals measured", "how is valuation scored", "what are percentile scores", "what does 60 out of 100 mean",
       "what is the passing score", "how are companies ranked against each other"],
      "Each company is ranked 0 to 100 against the other companies in our list of 119. Quality averages growth (revenue and "
      "profit growth), returns (return on equity and margin) and low debt. Valuation averages low P/E and low price-to-book. "
      "50 or more passes a circle. These are open, simple versions; the chapter's own scores come from its authors' models, "
      "whose formulas are not published."),
    E("fusion_test", FUSION, "How does the fusion model-portfolio test work?",
      ["how does the fusion backtest work", "what is the model portfolio", "how is the fusion test done",
       "how was the fusion portfolio tested", "what does group 1 only mean", "what is the fusion portfolio",
       "does the fusion method beat the market", "how did group 1 perform"],
      "On the first trading day of each month the companies are rated using only information public by then, and an "
      "equal-weight portfolio of group 1 (or groups 1 and 2) is bought at the next day's close. It is compared with owning "
      "all the companies equally and with the Nifty 50, after trading costs. A company's yearly results are used only 75 days "
      "after the year ended."),
    E("fusion_window", FUSION, "Why is the fusion test only about 3 years?",
      ["why is the fusion test only 3 years", "why not 5 years for fusion", "how far back does fusion go",
       "why is the fusion window short", "where does the fundamental data come from", "why not use older fundamentals",
       "how much history does fusion use"],
      "Free yearly company results go back only about four years, and each year counts only once it was published. So the "
      "fundamental part can be tested from about mid-2023. The chapter itself does not require a particular test length: "
      "fusion analysis is a way to choose and rate stocks at a moment in time."),
    E("fusion_limits", FUSION, "How reliable is the fusion test?",
      ["is the fusion test reliable", "what are the limits of the fusion test", "what is survivorship bias",
       "can i trust the fusion results", "is the fusion backtest accurate", "what are the caveats of fusion",
       "does fusion guarantee returns"],
      "Treat it as an illustration. It covers about 3 years, tests only today's 119 listed companies (firms that "
      "disappeared are missing, called survivorship bias), uses results as Yahoo reports them now, and the period was "
      "mostly a rising market. It does not predict the future, and it is not investment advice."),
    E("trend_vs_swing", FUSION, "What is the difference between trend following and swing trading?",
      ["trend following vs swing trading", "what is trend following", "what is swing trading",
       "difference between trend following and swing trading", "which is better trend following or swing trading",
       "why do trend followers have bigger drawdowns", "what is a swing trader", "mean reversion vs trend following"],
      "Trend following is opportunity management: you accept bigger falls to stay in for the big winners, so the average win "
      "must be large. Swing trading is risk management: you keep losses small and take smaller gains, often with a higher "
      "win rate. Mixing the two (wanting huge gains with tiny stops) tends to fail because the trend has no room to breathe. "
      "In the Strategy tests, the moving-average and MACD rules are trend following; the RSI and Bollinger rules are swing-style."),
    E("expectancy_why", FUSION, "Why does expectancy matter?",
      ["why does expectancy matter", "what is the expectancy formula", "what does negative expectancy mean",
       "what is expectancy", "how do i know if a strategy works", "what is win rate times average win",
       "what is the most important number for a trader"],
      "Expectancy is (win rate x average win) minus (loss rate x average loss): what a typical trade earns. If it is "
      "negative, the process loses money over time and should be fixed before anything else, by changing the win rate, the "
      "average win or the average loss. The Strategy tests show it for every rule."),
    E("fifty_fifty", FUSION, "Should fundamentals and technicals each get 50%?",
      ["should it be 50 50 technical and fundamental", "how much weight for technical vs fundamental",
       "who wins when analysts disagree", "what is the tiebreak", "should fundamentals and technicals be equally weighted"],
      "The chapter says a strict 50-50 split never works. Each team weighs the two differently, disagreements will happen, "
      "and a tiebreaking process is needed that respects both views. In the Winner's Circle the price trend is the one "
      "condition that is not negotiable."),
    E("market_carpet_what", FUSION, "What is the market carpet?",
      ["what is a market carpet", "what is the market carpet tab", "what is a heat map of the market", "what is a treemap",
       "how do i read the market carpet", "what do the colours and sizes mean on the carpet", "what do the tiles mean",
       "what is the industry map", "how to find strong industries", "what is the market map"],
      "The market carpet is a map of the market. Each tile is an industry (or, once you open one, a company). The size "
      "shows how big it is by market value, and the colour shows performance: green is up, red is down. Look for the "
      "greenest industries first, then click one to see its companies and find the large, strong ones. It shows what "
      "has already happened, not what will happen."),
    E("top_down_steps", FUSION, "How do I use the carpet for top-down analysis?",
      ["what is top down analysis with the carpet", "how do i find strong industries and then companies",
       "what are the steps of top down investing", "what did davis suggest", "rank industry groups by strength",
       "which industry is strongest right now", "how do i pick stocks from an industry"],
      "Chapter 2 of CMT Level III gives three steps: 1) decide the trend of the whole market and trade with it, 2) rank "
      "industry groups by strength and focus on the strongest (the Market carpet tab does this), 3) inside a strong "
      "industry, open the individual charts, work out targets and decide where to act. The tab can show the strongest "
      "and weakest industry at the top, measured today or against the 50-day or 200-day average."),
    E("top_down", FUSION, "What is the top-down approach?",
      ["what is the top down approach", "what is top down analysis", "how do you find ideas top down",
       "what is a relative rotation graph", "what is sector rotation", "start with sectors then stocks"],
      "A top-down approach starts wide and narrows: first which asset classes and sectors the market is favouring, then "
      "the strongest companies inside the strongest sectors. The chapter uses relative rotation graphs for this. This site "
      "does not include those graphs; its fusion screen goes straight to the company level."),
]


def _glossary_entries():
    """One entry per financial term, built from the same text as the '?' bubbles."""
    category = {"rsi": SIGNALS, "macd": SIGNALS, "trend": SIGNALS, "volatility": SIGNALS,
                "fusion_group": FUSION, "market_carpet": SIGNALS, "trend_stage": FUSION, "outperformance": FUSION, "quality_score": FUSION,
                "valuation_score": FUSION, "overlay_verdict": FUSION, "expectancy": FUSION}
    asks = {
        "rsi": ["rsi", "relative strength index", "what does the rsi number mean", "what is the strength score"],
        "macd": ["macd", "moving average convergence divergence", "what is momentum", "what is the macd signal line"],
        "trend": ["trend direction", "what is the trend", "how is the trend decided"],
        "volatility": ["volatility", "what are price swings", "what is volatile", "how bumpy is the stock"],
        "ending_value": ["ending value", "what is the ending value of rs 1 lakh", "what did rs 1,00,000 become"],
        "total_return": ["total return", "what is the total return"],
        "cagr": ["cagr", "average yearly return", "annual return", "compound annual growth rate", "what is yearly return"],
        "max_drawdown": ["max drawdown", "maximum drawdown", "worst fall", "what is drawdown", "biggest fall"],
        "var95": ["var", "value at risk", "bad day loss", "what is var 95", "what is a bad day loss"],
        "sharpe": ["sharpe ratio", "sharpe", "what is sharpe", "explain the sharpe ratio in simple words", "how good is a sharpe ratio"],
        "sortino": ["sortino ratio", "sortino", "what is sortino"],
        "calmar": ["calmar ratio", "calmar", "what is calmar"],
        "treynor": ["treynor ratio", "treynor", "what is treynor"],
        "beta": ["beta", "what is beta", "what does beta mean", "how risky compared with the market"],
        "alpha": ["alpha", "jensen's alpha", "what is alpha", "what does alpha mean"],
        "information": ["information ratio", "what is the information ratio"],
        "correlation": ["correlation", "correlation with nifty", "what is correlation"],
        "chance_gain": ["chance of a gain", "what does chance of a gain mean"],
        "typical": ["typical result", "median", "what is the typical result", "what is the median"],
        "poor_case": ["poor case", "what is the poor case"],
        "good_case": ["good case", "what is the good case"],
        "beats_holding": ["beats holding", "what does beats holding mean", "how often does the rule beat holding"],
        "chance_loss": ["chance of a loss", "what does chance of a loss mean"],
        "win_rate": ["win rate", "what is win rate", "win rate per trade", "what is a good win rate"],
        "avg_win": ["average win", "what is the average win", "average winning trade"],
        "avg_loss": ["average loss", "what is the average loss", "average losing trade"],
        "expectancy": ["expectancy", "expectancy per trade", "what is the expectancy of a strategy"],
        "fusion_group": ["fusion group", "what is a fusion group", "which group is this company in"],
        "trend_stage": ["trend stage", "what is the trend stage"],
        "outperformance": ["outperformance", "6 month outperformance", "what does outperforming the market mean", "relative strength"],
        "quality_score": ["quality score", "fundamental quality", "what is fundamental quality"],
        "valuation_score": ["valuation score", "what is valuation", "what is the valuation circle"],
        "overlay_verdict": ["technical overlay verdict", "overlay verdict"],
    }
    entries = []
    for key, term in glossary.TERMS.items():
        title = term["title"]
        entries.append(E(
            f"term_{key}", category.get(key, RISK if key in {"ending_value", "total_return", "cagr", "max_drawdown", "var95",
                                                             "sharpe", "sortino", "calmar", "treynor", "beta", "alpha",
                                                             "information", "correlation"} else SIMS),
            f"What is {title}?",
            [f"what is {title.lower()}"] + asks.get(key, []) + [f"explain {title.lower()}", f"formula for {title.lower()}"],
            f"{term['use']} Formula: {term['formula']} How to read it: {term['read']}"))
    return entries


NOTES_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "bot_notes.json")
LEVELS = ("age_5", "age_10", "age_15", "adult")
SIMPLE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "bot_simple.json")
FAQ = "Common questions"


def _load_notes():
    """The bot's main notes (data/bot_notes.json): each term has three explanation levels (age 10, age 15, adult)
    plus what it means inside this app. Questions people ask are matched against the term, its keywords and the FAQ."""
    with open(NOTES_PATH, encoding="utf-8") as f:
        data = json.load(f)
    with open(SIMPLE_PATH, encoding="utf-8") as f:
        simple = json.load(f)         # age 5 and under: an everyday story with no finance in it, then the link back
    entries = []
    for n in data["entries"]:
        e = E("n_" + n["id"], n["category"], n["term"],
              n["keywords"] + [f"what is {n['term'].split(' (')[0].lower()}", f"explain {n['term'].split(' (')[0].lower()}"],
              n["age_15"] + " " + n["in_this_app"])
        e["levels"] = {lv: n[lv] for lv in LEVELS if lv != "age_5"}
        e["simple"] = simple.get(n["id"])
        e["levels"]["age_5"] = (e["simple"]["story"] + " " + e["simple"]["link"]) if e["simple"] else n["age_10"]
        e["in_app"] = n["in_this_app"]
        e["related_ids"] = ["n_" + r for r in n.get("related", [])]
        entries.append(e)
    for q in data["faq"]:
        entries.append(E("n_faq_" + q["id"], FAQ, q["question"], q["keywords"] + [q["question"]], q["answer"]))
    return entries, data["meta"], data["fallback"]


NOTES, NOTES_META, FALLBACK = _load_notes()
# the main notes come first, so on an equal match they win over the older hand-written entries
ENTRIES = NOTES + MANUAL + _glossary_entries()
BY_ID = {e["id"]: e for e in ENTRIES}
for _c in dict.fromkeys(e["category"] for e in ENTRIES):
    if _c not in CATEGORY_ORDER:
        CATEGORY_ORDER.append(_c)
