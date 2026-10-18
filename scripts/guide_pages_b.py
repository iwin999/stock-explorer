"""Pages 9 to 15 of the presenter's guide: indicators, strategies, the back-test, the demo, questions and the glossary."""
from guide_pages_a import topic
from guide_parts import barometer_svg, gauge, zigzag_svg


def page9():
    return f"""
<div class="page" id="p9">
  <div class="head"><span class="part">Part 3. The six indicators</span><span class="site">{{SITE}}</span></div>
  <h1>Indicators, and how to read a gauge</h1>
  <p class="lead">An <b>indicator</b> is a number worked out from price (and sometimes volume) that answers one small question about a chart. The six gauges on the right of the screen each answer a different question.</p>
  <div class="topic"><h3>How to read any gauge on the screen</h3><div class="cols">
    <div><p>Every gauge is a coloured bar with a black pointer.</p>
    <ul><li><b class="down">Red on the left</b>: this indicator <b>leans down</b>.</li><li><b class="up">Green on the right</b>: it <b>leans up</b>.</li><li><b class="flat">Middle</b>: neutral.</li></ul>
    <p>The badge at the top right says <i>Leans up</i>, <i>Leans down</i> or <i>Neutral</i>, and the word under the bar says what the reading is, such as 'Balanced' or 'Stretched high'.</p></div>
    <div><p class="small">Example: a pointer near the right end</p>{gauge(78, "Falling", "Rising")}
    <p class="small" style="margin-top:6px">Example: a pointer in the middle</p>{gauge(50, "Selling", "Buying")}
    <p class="small" style="margin-top:6px">Some indicators measure a <b>stretch</b> (RSI, Z-score, the band). For these the bar is turned round: 'stretched high' sits at the red end, because a price that ran up too fast often cools off.</p></div>
  </div></div>
  <div class="note"><b class="t">One idea to repeat to visitors.</b> An indicator is a <b>clue, not an answer</b>. Six clues can disagree, and that is normal. Never treat one gauge as a promise.</div>
  {topic("RSI (speed)",
    "<p>RSI is the <b>speedometer</b> of a price. It runs from 0 to 100. Near 100 the price has been racing up very fast and may need a rest. Near 0 it has been falling fast and may bounce. But like a fast car, it can keep going.</p>",
    "<p><b>Relative Strength Index</b> (J. Welles Wilder): RSI = 100 - 100 / (1 + average gain / average loss), using Wilder's smoothing over <b>14 days</b>. Above <b>70</b> is conventionally <b>overbought</b>, below <b>30</b> <b>oversold</b>. In strong trends it can stay at an extreme for a long time, so it is a hint, not a signal on its own.</p>",
    "<p>'RSI (speed)'. 'Overbought (70)' is the red left end, 'Oversold (30)' the green right end. The word under it says Balanced, Overbought or Oversold.</p>", 1)}
  {topic("MACD (momentum)",
    "<p>Two friends run along a track, one quick and one steady. When the quick one pulls ahead, the pace is <b>picking up</b>. When the steady one catches up, the pace is <b>fading</b>. MACD compares a quick and a slow average of the price in the same way.</p>",
    "<p><b>Moving Average Convergence Divergence</b> (Gerald Appel): the MACD line is the <b>12-day</b> exponential average minus the <b>26-day</b> one. The <b>signal line</b> is the 9-day average of the MACD line, and the <b>histogram</b> is the gap between them. MACD above its signal line means rising momentum, below means fading.</p>",
    "<p>'MACD (momentum)'. The words are Rising, Slightly rising, Slightly falling or Falling, with the pointer to the right when momentum is rising.</p>", 2)}
  {topic("Trend strength (ADX)",
    "<p>ADX is the <b>wind speed</b>, not the wind direction. A weak wind means the price is just drifting about. A strong wind means the price is really heading somewhere. Two helper lines say whether the buyers or the sellers are pushing.</p>",
    "<p><b>Average Directional Index</b> (J. Welles Wilder): a 14-day smoothed measure of <b>trend strength</b>, either way. Below about <b>20</b> the market is range-bound; above 20 it is trending. Direction comes from <b>+DI</b> (upward pressure) against <b>-DI</b> (downward pressure).</p>",
    "<p>'Trend strength (ADX)'. The pointer shows who is in the lead: right with 'Buyers lead', left with 'Sellers lead'.</p>", 3)}
  <div class="foot"><span>{{SITE}}: Presenter's guide</span><span>Part 3 of 4</span><span>9</span></div>
</div>"""


def page10():
    return f"""
<div class="page" id="p10">
  <div class="head"><span class="part">Part 3. The six indicators</span><span class="site">{{SITE}}</span></div>
  <h1>Indicators, continued</h1>
  <p class="lead">Three more gauges, and a word on how they fit together.</p>
  {topic("Z-score",
    "<p>A Z-score is how far today's price is from its <b>usual</b> price, like your height compared with your class. Close to the class average means normal. Far taller or far shorter than everyone means unusual. A price very far above its usual level often drifts back down.</p>",
    "<p>z = (price - 20-day average) / standard deviation over the same 20 days. It measures the price in units of <b>standard deviations</b>. Beyond <b>+2</b> or <b>-2</b> is unusual (about 1 day in 20 if prices were bell-shaped), which mean-reversion traders watch. In strong trends extremes can persist.</p>",
    "<p>'Z-score'. The words are Stretched high (above +2), Normal, or Stretched low (below -2). It is turned round: stretched high is the red end.</p>", 1)}
  {topic("On-Balance Volume (OBV)",
    "<p>Count the shoppers who come into a shop. On days the price goes <b>up</b>, <b>add</b> the crowd to a score. On days it goes <b>down</b>, <b>take it away</b>. If the score keeps climbing, the crowd turns up more on the up days. It tells you whether the crowd is busier when the price rises or when it falls.</p>",
    "<p><b>On-Balance Volume</b> (Joseph Granville, 1963): a running total that adds a day's volume on an up-close and subtracts it on a down-close. A rising OBV suggests <b>accumulation</b> (buyers in control); a falling OBV suggests <b>distribution</b>. If price makes a new high but OBV does not, that <b>divergence</b> is a warning. The app uses the last 20 days' net flow, from -100% to +100%.</p>",
    "<p>'On-Balance Volume'. The words are 'Buyers backing it' (pointer right), 'Sellers backing it' (pointer left) or 'Balanced'. It is the one gauge that looks at <b>volume</b>, not just price.</p>", 2)}
  {topic("Bollinger band (where the price sits)",
    "<p>On [[pgr:p8:p8]] the grey band was the price's usual lane. This gauge tells you <b>where in the lane</b> the price is right now: near the top edge, near the bottom edge or in the middle.</p>",
    "<p>%B = (price - lower band) / (upper band - lower band). Near the <b>top</b> of the band the price is <b>stretched high</b>; near the <b>bottom</b> it is <b>stretched low</b>. Outside the band is an extreme. Band width shows volatility.</p>",
    "<p>'Bollinger band'. 'Top of range' is the red left end, 'Bottom of range' the green right end. The words say Stretched high, Inside range or Stretched low.</p>", 3)}
  <h2 style="margin-top:4px">Why do the six gauges often disagree?</h2>
  <div class="cols">
    <div class="topic tight"><p>They answer <b>different questions</b>. RSI asks 'how fast?', MACD 'is the pace picking up?', ADX 'is there a real trend?', the Z-score and the band ask 'how stretched?', and OBV asks 'is the crowd behind it?'.</p>
    <p>It is like asking six different doctors six different questions. Their answers do not have to match. The skill is in seeing the whole picture.</p></div>
    <div class="topic tight"><p><b>In finance words:</b> the indicators fall into families: <b>momentum</b> (RSI, MACD), <b>trend strength</b> (ADX), <b>volatility and stretch</b> (Z-score, Bollinger), and <b>volume</b> (OBV). Using one from each family is better than using several from the same family, because they add different information.</p>
    <p class="small">All six are <b>lagging</b>: they are calculated from past prices, so they describe, they do not foresee.</p></div>
  </div>
  <div class="topic"><h3>Hover for help</h3><p>Next to every indicator name is a small <b>i</b>. Hover over it (or the badge) for a one-paragraph description. The round chat button in the corner can also answer 'what is the Z-score?' in simple or adult language.</p></div>
  <div class="foot"><span>{{SITE}}: Presenter's guide</span><span>Part 3 of 4</span><span>10</span></div>
</div>"""


def page11():
    return f"""
<div class="page" id="p11">
  <div class="head"><span class="part">Part 4. The strategies</span><span class="site">{{SITE}}</span></div>
  <h1>Strategies, votes and the dial</h1>
  <p class="lead">Indicators are clues. A <b>strategy</b> is a set of rules that turns clues into a call. Five of them come from the <b>CMT</b> (Chartered Market Technician) curriculum, the professional exam in chart analysis.</p>
  <div class="cols">
    <div class="topic"><h3>The vote</h3><p>Each strategy looks at the chart and gives one of three answers, called a <b>vote</b>:</p>
    <ul><li><b class="up">▲ Up</b>: its rules say the reading leans up.</li><li><b class="down">▼ Down</b>: leans down.</li><li><b class="flat">– Neutral</b>: no clear reading. 'n/a' means not enough history to judge.</li></ul>
    <p class="small">A vote describes what the rules see today. It is not a promise about tomorrow.</p></div>
    <div class="topic"><h3>The dial (combined strategy reading)</h3><div style="display:flex;gap:10px;align-items:center"><div>{barometer_svg(-3)}</div>
    <div><p>The dial adds up the five votes (+1 for each Up, -1 for each Down).</p><p>It says <b>Strongly up</b>, <b>Leans up</b>, <b>Balanced</b>, <b>Leans down</b> or <b>Strongly down</b>, and below it: '3 of 5 strategies read down, 1 up, 1 neutral'. The ML model is <b>not</b> counted.</p></div></div></div>
  </div>
  <div class="note"><b class="t">Think of five friends voting on whether to take an umbrella.</b> Each looks at the sky in a different way. The dial just counts their votes. It does not know whether it will rain.</div>
  {topic("Fusion stage (the Winner's Circle trend test)",
    "<p>It asks one question: <b>is this company in a clear, steady climb and doing better than the market?</b> Imagine a runner who is both running uphill and overtaking the rest of the class. The strategy likes such runners. If instead the runner is sliding downhill, it votes Down.</p>",
    "<p>From <b>CMT Level III, Chapter 8</b> (fusion analysis). A company is in a <b>clear uptrend</b> when the price is above a rising 200-day average and the 50-day is above the 200-day, and it also <b>outperforms the Nifty over six months</b> (the trend and momentum test). That votes Up. A clear downtrend votes Down. Everything else is Neutral. The <b>four trend stages</b> are: clear uptrend, base of an uptrend, base of a downtrend, clear downtrend.</p>",
    "<p>First row of the table. <b>Full view</b> shows a scrollable guide to the four groups, with plain names: <b>Winner's Circle</b> (trend, quality and valuation all pass), <b>Strong contender</b> (trend plus one of the two), <b>Momentum only</b> (trend, but not quality or valuation) and <b>Watchlist</b> (the trend has not confirmed).</p>", 1)}
  {topic("Dow Theory",
    "<p>Climbing stairs: each step is higher than the last, and each rest stop is higher too. That is an <b>uptrend</b>. If the peaks and the dips both keep getting lower, it is like walking down the stairs: a <b>downtrend</b>.</p>",
    "<p>From <b>CMT Level I</b> (Charles Dow). An uptrend is a sequence of <b>higher highs and higher lows</b>; a downtrend is <b>lower highs and lower lows</b>. The trend is <b>confirmed</b> only when both agree. The app marks a swing point once five bars on each side confirm it, so it never looks ahead.</p>",
    "<p>Second row. Votes Up when the last two swing highs and swing lows are both rising, Down when both are falling, Neutral when they disagree.</p>", 2)}
  <div class="cols"><div class="topic" style="margin:0"><h3>Higher highs, higher lows</h3>{zigzag_svg(True)}</div><div class="topic" style="margin:0"><h3>Lower highs, lower lows</h3>{zigzag_svg(False)}</div></div>
  <div class="foot"><span>{{SITE}}: Presenter's guide</span><span>Part 4 of 4</span><span>11</span></div>
</div>"""


def page12():
    return f"""
<div class="page" id="p12">
  <div class="head"><span class="part">Part 4. The strategies</span><span class="site">{{SITE}}</span></div>
  <h1>Strategies, continued, and the ML model</h1>
  <p class="lead">Three more CMT strategies, and one machine-learning model that is not from the CMT.</p>
  {topic("Relative strength (against the market)",
    "<p>A race. If the whole class improves by 5 marks and you improve by 10, you did better than the class even though everyone improved. This strategy checks whether a company is <b>running faster than the Nifty 50</b>. Leaders tend to stay leaders for a while.</p>",
    "<p>A <b>CMT core topic</b>. It divides the stock's price by the index to get a <b>relative strength line</b>. It votes <b>Up</b> when that line is above its own 50-day average and has risen over three months, <b>Down</b> when it is below and has fallen, else Neutral. (Do not confuse it with the RSI indicator, which is different.)</p>",
    "<p>Third row. The 'What it sees' column says, for example, '-1.9% vs the market (3 months)'.</p>", 1)}
  {topic("Wyckoff: effort versus result",
    "<p>Push a heavy door. <b>Big effort and the door swings open</b>: a real move. <b>Big effort and it barely moves</b>: someone on the other side is pushing back. In markets, effort is volume and result is how far the price moved.</p>",
    "<p>From <b>CMT Level II</b> (Richard Wyckoff). <b>Effort</b> = volume at least 1.4 times its 20-day average. <b>Result</b> = the price move compared with a typical day's range (ATR). Big effort with a big result follows the move (Up or Down). Big effort with a small result is a <b>stall</b>: near the low of the recent range that is <b>absorption</b> (Up), near the high it is <b>distribution</b> (Down).</p>",
    "<p>Fourth row. 'What it sees' shows, for example, 'Volume 1.8x usual'.</p>", 2)}
  {topic("Fibonacci confluence",
    "<p>You saw the staircase on [[pgr:p8:p8]]. This strategy checks whether the price is <b>resting on one of the steps</b> right now. A price that dipped after a climb and is pausing on a step may be getting ready to climb again.</p>",
    "<p>From <b>CMT Levels I and II</b>. Over the last six months' swing it checks whether the price sits within 4% of the swing's size from the <b>38.2%, 50% or 61.8%</b> retracement. A pullback in an <b>uptrend</b> that holds there votes <b>Up</b> (support); a bounce in a <b>downtrend</b> that stalls there votes <b>Down</b> (resistance). 'Confluence' means several clues meeting at one level.</p>",
    "<p>Fifth row. 'Not at a key level' means Neutral.</p>", 3)}
  {topic("The ML model (machine learning)",
    "<p>We showed a computer thousands of days of old prices from 137 companies and let it learn <b>which clues usually came before a rise or a fall</b>, a bit like learning which clouds usually bring rain. It then says something like '52% chance of a higher close tomorrow'. But day-to-day moves are mostly luck, so it is only about as good as a <b>coin toss</b>.</p>",
    "<p>A <b>logistic regression</b> (a simple, explainable model, not deep learning) with <b>18 inputs</b>: the five strategy votes plus RSI, Stochastic RSI, Bollinger %B, Z-score, MACD, ADX lean, On-Balance Volume, recent returns, volume, volatility and distance from the 200-day average. It was <b>trained on the first 70%</b> of the dates and <b>tested on the last 30%</b>, data it had never seen. Out of sample it scored about <b>50 to 51%</b>, the same as always guessing the more common direction. It shows a lean only at 54% or more (Up) or 46% or less (Down).</p>",
    "<p>The sixth row, marked 'ML model'. <b>Full view</b> shows a bar chart of which inputs pushed today's number up or down. It is a <b>second opinion</b>, not counted in the dial.</p>", 4)}
  <div class="note"><b class="t">Key message for visitors.</b> The strategies and the model are <b>tools for understanding a chart</b>, from a real professional curriculum. We tested them honestly and they were about as good as a coin toss at predicting. We show that on purpose. That honesty is the point of the project.</div>
  <div class="foot"><span>{{SITE}}: Presenter's guide</span><span>Part 4 of 4</span><span>12</span></div>
</div>"""


def page13():
    return f"""
<div class="page" id="p13">
  <div class="head"><span class="part">Part 4. The strategies</span><span class="site">{{SITE}}</span></div>
  <h1>The back-test, and why honesty matters</h1>
  <p class="lead">The last column of the strategies table is the one visitors ask about most.</p>
  {topic("What is a back-test?",
    "<p>Before an exam you practise with <b>last year's question paper</b> to see how well your method works. A back-test does the same for a strategy: we <b>replay old prices</b> and see how often the strategy would have been right. Then we check it again on a part it had never seen.</p>",
    "<p>A <b>back-test</b> applies a rule set to <b>historical data</b> to measure how it would have performed. A fair back-test avoids <b>look-ahead bias</b> (using information that was not available at the time) and <b>overfitting</b> (tuning rules until they fit the past). Here the rules were fixed first and the results are reported on the dates held back.</p>")}
  {topic("How to read 'Back-test on this company'",
    "<p>For the company on screen, the column says <b>how often that strategy's Up or Down vote came true</b>. '49% next day' means: on the days it said Up or Down for this company, the price moved that way the very next day 49 times out of 100. '41% over 20 days' means the same, about a month later.</p>",
    "<p>Each row's figure is that company's own <b>hit rate</b>: the share of Up or Down votes followed by a move in that direction over the next day and the next 20 trading days, measured on that company's own history (roughly 900 to 1,100 calls for Fusion stage, Dow Theory and Relative strength, around 300 for Fibonacci and only about 150 for Wyckoff, which votes on far fewer days). Hover over a number to see how many past calls it rests on and the all-company average for comparison. If a strategy made fewer than 30 calls, the row says 'too few past calls to judge'. For the ML model the figure is from days it was not trained on.</p>",
    "<p>The header reads 'Back-test on this company: how often it matched the next move'. A company with no saved history shows the all-company average and the header says so.</p>")}
  <div class="cols">
  <div class="topic"><h3>The honest headline</h3>
    <p>The next-day numbers are almost all (about 9 in 10) between <b>45% and 55%</b>. The 20-day numbers spread wider, but their typical value is still close to 50%. A <b>coin toss is 50%</b>.</p>
    <table><thead><tr><th>If the figure is</th><th>It means</th></tr></thead><tbody>
    <tr><td>About 50%</td><td>No better than a coin toss</td></tr><tr><td>Above 50%</td><td>Slightly better, but small samples can fluctuate</td></tr>
    <tr><td>Below 50%</td><td>Slightly worse than a toss, for this company</td></tr></tbody></table>
    <p class="small" style="margin-top:4px">Do not read a 53% on one company and a 48% on another as 'one is better'. Per-company numbers wobble by a few points by luck alone.</p></div>
  <div class="topic"><h3>Why show numbers that are not impressive?</h3>
    <p><b>Because it is true.</b> Share prices from one day to the next are very hard to forecast. If a website claimed 80% accuracy you should be suspicious.</p>
    <p>This site's promise is different: it teaches how professionals <b>read</b> a chart, and it is honest about how far reading goes. That is why the screen says the strategies <b>describe, they do not recommend</b>.</p></div>
  </div>
  {topic("So what are the strategies good for?",
    "<p>A weather forecast cannot tell you if it will rain on your cricket match, but knowing how to read the clouds still helps you decide whether to carry a raincoat. The strategies help you <b>understand what the chart is doing and why</b>, and to ask better questions.</p>",
    "<p>In practice technical signals are used as <b>inputs to a process</b> that also includes <b>risk management</b> (position sizing, stop-losses) and the investor's time horizon, not as stand-alone predictors. The value is in discipline and understanding, not in a guaranteed edge. Past results do not guarantee future results.</p>")}
  <div class="screen" style="margin-top:0"><span class="chip a">On the screen</span><p>Click <b>Full view</b> on any row. A pop-up shows a chart of what that strategy is looking at, a key, and a plain explanation of what it is doing today for this company.</p></div>
  <div class="foot"><span>{{SITE}}: Presenter's guide</span><span>Part 4 of 4</span><span>13</span></div>
</div>"""


def page14():
    return f"""
<div class="page" id="p14">
  <div class="head"><span class="part">The presentation</span><span class="site">{{SITE}}</span></div>
  <h1>Using the site, and a 3-minute demo</h1>
  <div class="cols">
  <div class="topic"><h3>How a visitor uses it, step by step</h3>
    <ol style="margin:2px 0 4px 16px;padding:0">
      <li><b>Start.</b> Choose a name (a first name or nickname) and how much practice money. Returning visitors choose 'Returning user' and type the same name. Portfolios have no passwords, so anyone who knows a name can open it.</li>
      <li><b>Search.</b> Type a company, for example Reliance, and press Enter.</li>
      <li><b>Look.</b> Read the chart. Try Week, 5Y and Fibonacci.</li>
      <li><b>Read.</b> Look at the six gauges, the dial and the strategies table. Click one Full view.</li>
      <li><b>Practise.</b> Press Buy, choose how much, buy. The pop-up stays open for the next order.</li>
      <li><b>Watch.</b> Your holdings, ring and rank update. Check the leaderboard.</li>
      <li><b>Ask.</b> Use the round chat button for any word you do not know.</li>
    </ol></div>
  <div class="topic"><h3>Handy things to know</h3><ul>
    <li><b>Demo:</b> press the Demo button and the screen runs itself, with captions and a voice, and at the end it tries the chat helper by itself. The speed buttons on its card (0.75× to 2×) work like a video's playback speed. Use it when nobody is at the screen. Touch the screen to take over.</li>
    <li><b>This guide:</b> the small blue document button above the chat button opens this guide in a new tab.</li>
    <li><b>Tour:</b> the Tour button walks through every part of the screen in 11 steps, each with a fuller explanation. You press Next and Back at your own pace.</li>
    <li><b>Dark mode:</b> good for a dim room or a projector.</li>
    <li><b>Dashboard view:</b> off gives the simple phone-style layout.</li>
    <li><b>Leaderboard:</b> ranked by percent return since the start, so small portfolios can win.</li>
    <li><b>Slow or odd?</b> The site is on free hosting and may take a moment to wake. Prices may be a few minutes behind.</li>
    <li><b>An error message?</b> Stay calm. A grey note appears with a reference number to quote to the admin. It is not your fault.</li></ul></div>
  </div>
  <h2>A 3-minute demo script</h2>
  <table><thead><tr><th style="width:11%">Time</th><th style="width:34%">Do this</th><th>Say this</th></tr></thead><tbody>
  <tr><td>0:00</td><td>Show the whole screen.</td><td>"This is a practice stock market. Real prices, pretend money. Nothing here is advice."</td></tr>
  <tr><td>0:30</td><td>Search a company. Point at the price and the chart.</td><td>"Each bar is one day. Green means the price rose, red means it fell. The bars underneath are how many shares were traded."</td></tr>
  <tr><td>1:00</td><td>Switch on Fibonacci. Point at the orange and navy lines.</td><td>"The lines smooth out the bumps. The pale lines are places where a price often pauses."</td></tr>
  <tr><td>1:30</td><td>Point at the six gauges. Hover over one i.</td><td>"Each gauge asks a different question: how fast, how strong, how stretched, is the crowd behind it. Red leans down, green leans up."</td></tr>
  <tr><td>2:00</td><td>Point at the dial and the table. Click one Full view.</td><td>"Five strategies from a professional exam vote Up, Down or Neutral. The dial counts the votes. In our tests they were about as good as a coin toss, and we say so."</td></tr>
  <tr><td>2:30</td><td>Press Buy and place a small practice order. Close the pop-up.</td><td>"Now I practise. My holding and my ranking just updated. Questions? The round button explains any word."</td></tr>
  </tbody></table>
  <div class="cols" style="margin-top:6px">
  <div class="topic tight"><h3>Do</h3><ul><li>Say 'practice money' and 'the reading leans'.</li><li>Let visitors try it themselves.</li><li>Say 'I do not know, let us ask the helper' when unsure.</li></ul></div>
  <div class="topic tight"><h3>Do not</h3><ul><li>Say what a price will do, or give tips.</li><li>Call it investing advice or a money-making tool.</li><li>Hide the 50% honesty. It is your best point.</li></ul></div>
  </div>
  <div class="foot"><span>{{SITE}}: Presenter's guide</span><span>Presenting</span><span>14</span></div>
</div>"""


QA = [
    ("Is this real money?", "No. Everything is virtual. Prices are real, the money is pretend."),
    ("Can I make money with this?", "It is for learning, not earning. It teaches how to read charts. Real trading carries real risk and needs a real adviser."),
    ("Should I buy this share?", "The site does not tell you that. It shows what the signals read. The decision, and the responsibility, is yours."),
    ("Is the prediction accurate?", "There is no prediction. The strategies describe the chart, and in our tests they matched the next move about 50% of the time, like a coin toss."),
    ("Why does it say 'leans' instead of 'will'?", "Because nobody can know the future. 'Leans' means the clues point that way, not that it will happen."),
    ("Are the prices live?", "They come from Yahoo Finance and can be a few minutes late. When the market is closed it shows the last close."),
    ("Why are the futures and options prices 'calculated'?", "Real exchange prices for them are not freely available, so the app works them out from the share price with standard formulas. They are learning estimates."),
    ("What is the CMT?", "The Chartered Market Technician exam, a professional qualification in chart analysis. The strategies here come from its curriculum."),
    ("What does the ML model do?", "It learned from old prices which clues came before ups and downs, and gives a chance. In tests it was about as good as a coin toss, so it is a second opinion."),
    ("Who made it?", "Freya Shah, from Mayo College Girls School, using what she has learned, with an AI coding assistant to write the code."),
    ("Why is there no password?", "Names are not private. Use a first name or nickname and no personal details."),
    ("Which indicator is the best?", "None on its own. They answer different questions, so the skill is in using them together."),
]

GLOSSARY = [
    ("ADX", "Strength of a trend, either way."), ("Benchmark", "An index used to compare against, like the Nifty 50."),
    ("Bond", "A loan to a government or company that pays interest."), ("Bollinger Bands", "A band showing a price's usual range."),
    ("Call", "An option giving the right to buy."), ("Candlestick", "One bar showing open, high, low and close."),
    ("CMT", "Chartered Market Technician, a chart-analysis qualification."), ("Diversification", "Spreading money to reduce risk."),
    ("Dividend", "A share of a company's profit paid to shareholders."), ("ETF", "A fund bought like a share that holds a basket of assets."),
    ("Exchange", "A regulated market where shares trade (NSE, BSE)."), ("Expiry", "The date a future or option ends."),
    ("Fibonacci", "Levels (38.2%, 50%, 61.8%) where prices often pause."), ("Future", "An agreement to buy or sell at a fixed price on a fixed date."),
    ("Index", "A scoreboard of a basket of shares."), ("Leverage", "Controlling a big position with a small deposit."),
    ("Long / Short", "Profit from a rise / profit from a fall."), ("Lot", "The fixed quantity in one contract."),
    ("MACD", "A momentum gauge from two moving averages."), ("Margin", "A deposit that backs a futures position."),
    ("Moving average", "The average price over the last N days."), ("OBV", "A running total of volume on up days minus down days."),
    ("Option", "The right, not the obligation, to buy or sell."), ("Portfolio", "Everything you hold, plus cash."),
    ("Premium", "The price paid for an option."), ("Put", "An option giving the right to sell."),
    ("RSI", "A 0 to 100 speed gauge of recent moves."), ("Strike price", "The fixed price in an option contract."),
    ("Support / Resistance", "A price floor / a price ceiling."), ("Trend", "The general direction of a price."),
    ("Volatility", "How much a price swings."), ("Volume", "How many shares were traded."),
    ("Z-score", "How far a price is from its 20-day average, in standard deviations."),
]


def page15():
    qa = "".join(f'<div class="qa"><b>{q}</b><br>{a}</div>' for q, a in QA)
    gl = "".join(f"<div><b>{t}.</b> {d}</div>" for t, d in GLOSSARY)
    return f"""
<div class="page" id="p15">
  <div class="head"><span class="part">Questions and glossary</span><span class="site">{{SITE}}</span></div>
  <h1>Questions you will be asked</h1>
  <div class="cols" style="gap:14px"><div>{"".join(f'<div class="qa"><b>{q}</b><br>{a}</div>' for q, a in QA[:6])}</div><div>{"".join(f'<div class="qa"><b>{q}</b><br>{a}</div>' for q, a in QA[6:])}</div></div>
  <h2 style="margin-top:7px">Glossary: every word in one line</h2>
  <div class="gl">{gl}</div>
  <div class="foot"><span>{{SITE}}: Presenter's guide</span><span>Educational project. Not investment advice.</span><span>15</span></div>
</div>"""
