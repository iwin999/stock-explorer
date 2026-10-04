"""One entry per financial term: what it tells you, its formula, and how to read it.

These feed the small "?" bubbles shown next to every term on the site. Each entry:
  title   - the full name
  use     - what it is used for, in plain words
  formula - how it is calculated
  read    - how to interpret the number
"""

TERMS = {
    "market_carpet": dict(
        title="Market carpet",
        use="A map of many companies at once, used to spot the strongest industries before looking at single companies.",
        formula="Tile size = market capitalisation (share price x number of shares). Tile colour = performance (today, or the gap from the 50-day or 200-day average). An industry's colour is the market-cap-weighted average of its companies.",
        read="Large green tiles are big companies or industries that are doing well; red means falling. Look for strong industries first, then strong companies inside them. It describes the past and does not predict."),
    # ---------------- key signals ----------------
    "rsi": dict(
        title="RSI (Relative Strength Index)",
        use="A 0-100 score of how fast the price has been rising or falling lately. Used to spot stocks that may have moved too far, too fast.",
        formula="RSI = 100 - 100 / (1 + average gain / average loss), using Wilder's smoothed averages over 14 days.",
        read="Above 70: may be overextended after a quick rise. Below 30: may be oversold after a quick fall. In between: balanced."),
    "macd": dict(
        title="MACD (Moving Average Convergence Divergence)",
        use="Shows whether price momentum is building up or fading by comparing a fast and a slow average.",
        formula="MACD line = 12-day exponential average - 26-day exponential average. Signal line = 9-day average of the MACD line.",
        read="MACD above its signal line: upward momentum. Below: downward momentum."),
    "trend": dict(
        title="Trend direction",
        use="Summarises where the price is heading using its 50-day and 200-day average prices.",
        formula="Uptrend if price > 50-day average > 200-day average. Downtrend if price < 50-day average < 200-day average. Otherwise sideways.",
        read="Uptrend: a steady climb. Downtrend: a steady slide. Sideways: no clear direction."),
    "volatility": dict(
        title="Volatility",
        use="Measures how much the price jumps around. Higher means a bumpier, riskier ride.",
        formula="Standard deviation of daily returns x square root of 252 (trading days in a year).",
        read="Under 20%: fairly calm. 20-35%: moderately active. Over 35%: highly active."),
    # ---------------- return and risk ----------------
    "ending_value": dict(
        title="Ending value",
        use="What the starting Rs 1,00,000 would have grown (or shrunk) to at the end of the test.",
        formula="Start value x (1 + daily result) compounded over every day of the test, after trading costs.",
        read="Compare the rule with buy-and-hold: the higher number made more money over this period."),
    "total_return": dict(
        title="Total return",
        use="The overall percentage gain or loss over the whole period.",
        formula="(Ending value / Starting value) - 1.",
        read="+20% means Rs 1,00,000 became Rs 1,20,000. It does not show how bumpy the journey was."),
    "cagr": dict(
        title="Average yearly return (CAGR)",
        use="The steady yearly growth rate that would give the same final result. Lets you compare periods of different lengths.",
        formula="CAGR = (Ending value / Starting value) ^ (1 / years) - 1.",
        read="Compare it with a safe option such as a bond (about 6.5%). A return below that did not reward the risk."),
    "max_drawdown": dict(
        title="Worst fall (maximum drawdown)",
        use="The biggest drop from a peak to the next low point: the worst loss someone holding through the period would have lived through.",
        formula="Lowest value of (current value / highest value so far - 1).",
        read="-30% means at one point the investment was 30% below its previous high. Smaller (closer to zero) is better."),
    "var95": dict(
        title="Value at Risk (VaR, 95%)",
        use="A 'bad day' measure: how much you could lose in one day on all but the worst 5% of days.",
        formula="The 5th percentile of daily returns, shown as a loss.",
        read="2% means that on 1 trading day in 20 the loss has been at least 2%."),
    # ---------------- reward for the risk taken ----------------
    "sharpe": dict(
        title="Sharpe ratio",
        use="Reward earned for each unit of risk taken. Lets you compare investments with different bumpiness.",
        formula="(Average return - safe rate) / volatility, scaled to a year: mean(daily excess return) x 252 / (daily std x sqrt(252)).",
        read="Below 0: earned less than a safe bond. 0-1: modest. Above 1: generally considered good. Above 2: excellent."),
    "sortino": dict(
        title="Sortino ratio",
        use="Like Sharpe, but only counts the falls as risk, because investors do not mind upward jumps.",
        formula="(Average return - safe rate) / downside deviation, where downside deviation uses only the days below the safe rate.",
        read="Higher is better. If it is much higher than Sharpe, most of the bumpiness was on the upside."),
    "calmar": dict(
        title="Calmar ratio",
        use="Reward compared with the worst pain endured.",
        formula="Average yearly return / absolute value of the maximum drawdown.",
        read="Above 1: the yearly return was bigger than the worst fall. Higher is better."),
    "treynor": dict(
        title="Treynor ratio",
        use="Reward earned per unit of market risk (beta). Useful for judging a holding as one part of a diversified portfolio.",
        formula="(Average yearly return - safe rate) / beta.",
        read="Higher is better. It is unreliable when beta is close to zero."),
    # ---------------- compared with the market ----------------
    "beta": dict(
        title="Beta",
        use="How strongly the stock moves compared with the market (the Nifty 50, or the Sensex for a BSE listing).",
        formula="Covariance of the stock's daily returns with the market index's, divided by the variance of the index's returns.",
        read="1: moves with the market. Above 1: swings more than the market. Below 1: swings less. Negative: tends to move opposite."),
    "alpha": dict(
        title="Alpha (Jensen's alpha)",
        use="The yearly return beyond what the stock's market risk alone would explain.",
        formula="(Stock return - safe rate) - beta x (index return - safe rate), annualised.",
        read="Positive: did better than its risk deserved. Negative: did worse."),
    "information": dict(
        title="Information ratio",
        use="How consistently the stock beat (or trailed) the market index, relative to how much it differed.",
        formula="Average daily return minus the index's, divided by the standard deviation of that difference, scaled to a year.",
        read="Above 0.5 is generally considered good. Negative means it tended to trail the market."),
    "correlation": dict(
        title="Correlation with the market index",
        use="How closely the stock moves in step with the market.",
        formula="Pearson correlation of daily returns, between -1 and 1.",
        read="Near 1: moves with the market. Near 0: unrelated. Below 0: moves the opposite way."),
    # ---------------- simulation results ----------------
    "chance_gain": dict(
        title="Chance of a gain",
        use="Of all the simulated futures, the share that ended with a profit.",
        formula="(Number of simulated paths with a return above 0) / 2,000.",
        read="50% is a coin toss. This is a share of imagined futures, not a promise."),
    "typical": dict(
        title="Typical result (median)",
        use="The middle result: half of the simulated futures did better, half did worse.",
        formula="The 50th percentile of the simulated returns.",
        read="A better 'typical' guide than the average, because a few extreme outcomes do not distort it."),
    "poor_case": dict(
        title="Poor case (1 in 20)",
        use="A pessimistic but possible result: only 1 simulated future in 20 did worse.",
        formula="The 5th percentile of the simulated returns.",
        read="Use it to ask: could I live with this outcome?"),
    "good_case": dict(
        title="Good case (1 in 20)",
        use="An optimistic but possible result: only 1 simulated future in 20 did better.",
        formula="The 95th percentile of the simulated returns.",
        read="Treat it as the upside of luck, not a target."),
    "beats_holding": dict(
        title="Beats holding",
        use="How often the rule did better than simply buying and holding the stock.",
        formula="(Number of paths where the rule's return > buy-and-hold's return) / total paths.",
        read="Above 50% means the rule was usually ahead. The size of the gap matters too, not just how often."),
    # ---------------- trade-by-trade results (CMT Level III, 8.1) ----------------
    "win_rate": dict(
        title="Win rate (per trade)",
        use="Of the completed trades, the share that made money.",
        formula="Winning trades / all trades. A trade is one stretch of holding the stock, from buying to selling.",
        read="A low win rate can still work if the wins are much bigger than the losses (typical of trend following). "
             "A high win rate can still lose money if the losses are large."),
    "avg_win": dict(
        title="Average win",
        use="The average gain on the trades that made money.",
        formula="Sum of the returns of winning trades / number of winning trades.",
        read="Compare it with the average loss. Trend followers need big winners to pay for many small losses."),
    "avg_loss": dict(
        title="Average loss",
        use="The average loss on the trades that lost money.",
        formula="Sum of the losses of losing trades / number of losing trades (shown as a positive number).",
        read="Smaller is better. Swing traders try to keep this small; trend followers accept bigger ones."),
    "expectancy": dict(
        title="Expectancy per trade",
        use="What a typical trade earns on average. The chapter calls it the most important test of any trading process.",
        formula="(win rate x average win) - (loss rate x average loss).",
        read="Positive: on average each trade added money. Zero or negative: the process loses money over time, so stop and "
             "fix the win rate, the average win or the average loss."),
    # ---------------- fusion analysis (CMT Level III, Chapter 8) ----------------
    "fusion_group": dict(
        title="Fusion group (1 to 4)",
        use="Sorts a company by how many of the Winner's Circle conditions it meets. Price trend and momentum are non-negotiable.",
        formula="1 = trending and outperforming with BOTH fundamental quality and valuation; 2 = with at least one; 3 = with neither; "
                "4 = not trending (watchlist).",
        read="Aim for many 1s, some 2s, few 3s, and avoid 4s. It is a way to organise ideas, not a buy or sell instruction."),
    "trend_stage": dict(
        title="Trend stage",
        use="Where the price is in its long-term cycle.",
        formula="Three tests: price above its 200-day average; 50-day average above the 200-day; 200-day average rising. "
                "All three = clear uptrend, two = base of an uptrend, one = base of a downtrend, none = clear downtrend.",
        read="Clear uptrend is the only stage inside the Winner's Circle."),
    "outperformance": dict(
        title="6-month outperformance",
        use="Shows whether the stock has beaten the market lately, which the chapter treats as part of the market's own opinion.",
        formula="The stock's 6-month return minus the Nifty 50's 6-month return.",
        read="Positive means the stock has led the market. It must be positive for the company to be inside the Winner's Circle."),
    "quality_score": dict(
        title="Fundamental quality score (0-100)",
        use="Ranks the company against the others in our list on growth, returns and leverage.",
        formula="Average of three parts, each a 0-100 rank: growth (revenue and profit growth), returns (return on equity "
                "and operating margin), and leverage (low debt to equity; skipped for banks).",
        read="50 or more passes the 'quality' circle. 100 would be the best in the list, 0 the worst."),
    "valuation_score": dict(
        title="Valuation score (0-100)",
        use="Ranks how cheaply the company is priced against the others in our list.",
        formula="Average of two 0-100 ranks: low price-to-earnings (P/E) and low price-to-book (P/B). Loss-making companies "
                "rank worst on P/E.",
        read="50 or more passes the 'valuation' circle. A high score means cheaper than most, not necessarily a bargain."),
    "overlay_verdict": dict(
        title="Technical overlay verdict",
        use="Chapter 8.5's idea: let the price trend confirm, delay or reject a fundamental view.",
        formula="Confirm when trend and momentum agree with the fundamentals; delay when the fundamentals look good but the "
                "trend has not confirmed; reject when neither supports it.",
        read="When the two disagree, give risk management more weight: smaller positions, tighter stops, and reassess."),
    "chance_loss": dict(
        title="Chance of a loss",
        use="Of the reshuffled histories, the share where the rule lost money.",
        formula="(Number of reshuffled histories with a negative total return) / 2,000.",
        read="A low number suggests the rule's success was not just luck of the order of days."),
}


def get(key):
    return TERMS[key]


def as_markdown(key):
    t = TERMS[key]
    return (f"**{t['title']}**\n\n**What it is used for.** {t['use']}\n\n"
            f"**Formula.** {t['formula']}\n\n**How to read it.** {t['read']}")
