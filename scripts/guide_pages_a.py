"""Pages 1 to 8 of the presenter's guide: the story, the basics, what can be traded, the screen map, and the chart tools."""
from guide_parts import (barometer_svg, candle_svg, chart_anatomy_svg, fib_svg, gauge, screen_map_svg, zigzag_svg)


def topic(title, simple, fin, screen=None, num=None, extra=""):
    n = f'<span class="num">{num}</span>' if num else ""
    scr = f'<div class="screen"><span class="chip a">On the screen</span>{screen}</div>' if screen else ""
    return (f'<div class="topic"><h3>{n}{title}</h3><div class="two">'
            f'<div class="simple"><span class="chip s">In simple words</span>{simple}</div>'
            f'<div class="fin"><span class="chip f">In finance words</span>{fin}</div></div>{extra}{scr}</div>')


CONTENTS = [("The story in one minute and the golden rules", "p2", "p2"), ("Part 1. The basics: companies, shares, exchanges", "p3", "p3"),
            ("Reading a price: volume, candles, trends, risk", "p4", "p4"), ("Your portfolio, practice trading, ETFs and bonds", "p5", "p5"),
            ("Futures and options", "p6", "p6"), ("Part 2. The screen, part by part", "p7", "p7"), ("The chart and its tools", "p8", "p8"),
            ("Part 3. The six indicators", "p9", "p10"), ("Part 4. The five strategies and the ML model", "p11", "p12"),
            ("The back-test, and why honesty matters", "p13", "p13"), ("Using the site, and a 3-minute demo", "p14", "p14"),
            ("Questions you will be asked, and a glossary", "p15", "p15")]


def page1():
    rows = "".join(f"<tr><td>{t}</td><td style='text-align:right;white-space:nowrap'><span class=\"pgn\" data-from=\"{f}\" data-to=\"{to}\"></span></td></tr>" for t, f, to in CONTENTS)
    return f"""
<div class="page" id="p1">
  <div style="margin-top:6mm"><div class="kicker">Presenter's guide</div>
  <div class="big">{{SITE}}</div>
  <p class="lead" style="margin-top:8px;font-size:14px;max-width:150mm">A practice stock market that explains itself. This guide explains <b>every part of the dashboard twice</b>:
  once in simple words with an everyday picture, and once in proper finance words.</p></div>
  <div class="cols" style="margin-top:9mm">
    <div class="topic" style="background:#f6f8fb"><h3>Who this is for</h3>
      <p>You are going to present {{SITE}} to visitors. You do <b>not</b> need to know anything about the stock market yet. This guide starts at the very
      beginning (what a share is) and builds up, one idea at a time. Each page uses words explained on the pages before it, so <b>read it in order</b>.</p>
      <p>Read it once through. Then keep it with you while you present, and use the contents list to jump to a page.</p></div>
    <div class="topic" style="background:#f6f8fb"><h3>How every topic is laid out</h3>
      <p><span class="chip s">In simple words</span> an everyday picture, for a friend who has never heard of the topic.</p>
      <p><span class="chip f">In finance words</span> the proper explanation, with the correct terms, as a finance professional would say it.</p>
      <p><span class="chip a">On the screen</span> exactly where you will see it in the app, and what it looks like.</p></div>
  </div>
  <h2 style="margin-top:8mm">Contents</h2>
  <table style="margin-top:3px"><tbody>{rows}</tbody></table>
  <h2 style="margin-top:9mm">The path through this guide</h2>
  <div class="cols" style="grid-template-columns:repeat(4,1fr);gap:7px;margin-top:4px">
    <div class="topic" style="background:#eef5ff"><div class="kicker" style="letter-spacing:.1em">Step 1</div><h3>The basics</h3><p class="small">Shares, prices, volume, candles, trends, risk, portfolios. [[Pgr:p3:p5]].</p></div>
    <div class="topic" style="background:#eef5ff"><div class="kicker" style="letter-spacing:.1em">Step 2</div><h3>What you can trade</h3><p class="small">ETFs, bonds, futures and options. [[Pgr:p5:p6]].</p></div>
    <div class="topic" style="background:#eef5ff"><div class="kicker" style="letter-spacing:.1em">Step 3</div><h3>The screen</h3><p class="small">A map of every box, and the chart tools. [[Pgr:p7:p8]].</p></div>
    <div class="topic" style="background:#eef5ff"><div class="kicker" style="letter-spacing:.1em">Step 4</div><h3>The readers</h3><p class="small">Six indicators, five strategies, the ML model and the back-test. [[Pgr:p9:p13]].</p></div>
  </div>
  <div class="note" style="margin-top:8mm"><b class="t">Important.</b> {{SITE}} is an <b>educational project</b>. All money in it is <b>virtual</b> and nothing on it is investment advice.
  The prices come from Yahoo Finance and can be a few minutes late. Say this at the start of every presentation.</div>
  <div class="foot"><span>{{SITE}}: Presenter's guide</span><span>Made by Freya Shah (P/2977), Mayo College Girls School</span><span>1</span></div>
</div>"""


def page2():
    return f"""
<div class="page" id="p2">
  <div class="head"><span class="part">Start here</span><span class="site">{{SITE}}</span></div>
  <h1>The story in one minute</h1>
  <p class="lead">Learn these lines first. Everything else in the guide helps you answer questions about them.</p>
  <div class="say"><i>Say it like this:</i><br>
  "This is {{SITE}}, a practice stock market. Real companies, real prices, but <b>pretend money</b>, so you can learn without losing anything.
  On the left is your practice portfolio. In the middle is the price chart of any company you search for. On the right are six <b>indicators</b>:
  small gauges that read the chart for you. Along the bottom are <b>five strategies</b> from a professional exam called the CMT, and each one gives its
  reading, a vote. The dial on the left combines the five votes. And in the corner there is a chat helper that explains any word you do not know."</div>
  <h2 style="margin-top:7mm">The three golden rules</h2>
  <div class="cols3">
    <div class="topic"><h3><span class="num">1</span>It is practice money</h3><p>Nothing here is real. You cannot win or lose actual rupees. Say "practice money" or "virtual money", never "invest your money".</p></div>
    <div class="topic"><h3><span class="num">2</span>It describes, it never advises</h3><p>The site shows what the charts are saying. It never says "buy this". If a visitor asks "should I buy?", the answer is: "That is not what it is for. It shows what the signals read; the decision is yours, and a real decision needs a real adviser."</p></div>
    <div class="topic"><h3><span class="num">3</span>Be honest about the limits</h3><p>In our own tests the strategies were right about <b>50 times out of 100</b>, which is the same as flipping a coin. We show that openly on purpose. It makes the site trustworthy.</p></div>
  </div>
  <h2 style="margin-top:6mm">Say this, not that</h2>
  <table><thead><tr><th style="width:50%">Instead of</th><th>Say</th></tr></thead><tbody>
    <tr><td>"The price <b>will</b> fall."</td><td>"The reading <b>leans down</b>." (a lean is not a promise)</td></tr>
    <tr><td>"You should buy this."</td><td>"The strategy says Up. Whether to act on it is up to you."</td></tr>
    <tr><td>"Invest Rs 10,000."</td><td>"Practise with Rs 10,000 of virtual money."</td></tr>
    <tr><td>"The ML model predicts tomorrow."</td><td>"The ML model gives a modelled chance. In tests it was about as good as a coin toss."</td></tr>
    <tr><td>"This stock is a winner."</td><td>"This company passes the trend test the strategy uses."</td></tr>
  </tbody></table>
  <h2 style="margin-top:6mm">How this guide is ordered</h2>
  <div class="cols">
    <div class="topic tight"><p><b>Part 1, the basics ([[pgr:p3:p6]]).</b> Companies, shares, prices, volume, candles, trends, risk, portfolios, ETFs, bonds, futures and options. You cannot understand an indicator without these.</p>
    <p><b>Part 2, the screen ([[pgr:p7:p8]]).</b> A map of every box on the dashboard, and the tools on the chart.</p></div>
    <div class="topic tight"><p><b>Part 3, the indicators ([[pgr:p9:p10]]).</b> The six gauges on the right.</p>
    <p><b>Part 4, the strategies ([[pgr:p11:p13]]).</b> The five strategies, the ML model, the dial and the back-test.</p>
    <p><b>The end ([[pgr:p14:p15]]).</b> A demo script, likely questions and a glossary.</p></div>
  </div>
  <div class="foot"><span>{{SITE}}: Presenter's guide</span><span>Educational project. Not investment advice.</span><span>2</span></div>
</div>"""


def page3():
    return f"""
<div class="page" id="p3">
  <div class="head"><span class="part">Part 1. The basics</span><span class="site">{{SITE}}</span></div>
  <h1>Companies, shares and the stock market</h1>
  <p class="lead">Start with these five ideas. Every later page leans on them.</p>
  {topic("A company, and a share (also called a stock)",
    "<p>Imagine a pizza shop. The shop is cut into a million tiny slices, and anyone can own a slice. A <b>share</b> is one slice of a company. If you own a slice, you own a tiny piece of the shop, and if the shop does well, your slice becomes more valuable.</p>",
    "<p>A <b>share</b> (or <b>stock</b>) is a unit of <b>ownership</b> in a company. Companies sell shares to raise money to grow. A shareholder owns part of the company and may get a share of the profit, called a <b>dividend</b>. A company whose shares anyone can buy is called <b>listed</b>.</p>",
    "<p>You search for a company by name (a small spelling slip is fine) and its price chart appears. You can buy and sell shares of it with practice money.</p>", 1)}
  {topic("Why does a share price go up and down?",
    "<p>Think of a popular toy at school. If everyone wants it and few have it, the price goes up. If nobody wants it, the price falls. A share price is simply what buyers and sellers agree on right now.</p>",
    "<p>Price is set by <b>supply and demand</b> in the market. More buyers than sellers pushes the price up. More sellers than buyers pushes it down. News, company profits, interest rates and the general mood of investors (<b>sentiment</b>) all change how many people want to buy or sell.</p>",
    "<p>The big number at the top of the chart is the latest price. Next to it is the change since yesterday's close, in rupees and in percent (green for up, red for down).</p>", 2)}
  {topic("The stock exchange: NSE and BSE",
    "<p>An exchange is like a big, well-organised market (a mela with strict rules) where all buying and selling of shares happens in one place, fairly and openly.</p>",
    "<p>A <b>stock exchange</b> is a regulated marketplace where listed shares are traded. India has two main ones: the <b>NSE</b> (National Stock Exchange) and the <b>BSE</b> (Bombay Stock Exchange). Many big companies are listed on both. The regulator that watches over them is <b>SEBI</b>.</p>",
    "<p>You can search both listings. A company's short code, called a <b>ticker symbol</b> (like RELIANCE or TCS), is shown next to its name. It is the company's nickname on the exchange.</p>", 3)}
  {topic("An index: Nifty 50 and Sensex",
    "<p>An index is a <b>class scoreboard</b>. Instead of looking at 50 students one by one, you look at their average marks. The Nifty 50 is the average of the 50 biggest companies on the NSE, so it tells you how 'the market' is doing overall.</p>",
    "<p>An <b>index</b> tracks a basket of shares. The <b>Nifty 50</b> covers 50 large NSE companies, weighted by size. The <b>Sensex</b> covers 30 large BSE companies. They are used as the <b>benchmark</b>: to say whether a company did better or worse than the market.</p>",
    "<p>The 'Relative strength' strategy compares a company with the Nifty 50 (or Sensex for a BSE listing).</p>", 4)}
  {topic("Market hours, and the 'last close'",
    "<p>The market is like a shop with opening hours. Outside them nothing is bought or sold, so the price stays where it stopped.</p>",
    "<p>The Indian market trades <b>9:15 am to 3:30 pm, Monday to Friday</b>, except holidays. The <b>last close</b> is the final price of the previous session. Outside hours the screen shows it, with a note that the market is closed.</p>",
    "<p>The line under the price says 'Market closed (opens Monday at 9:15 am), last close' or tells you the market is open. While it is open, parts of the screen refresh themselves every few seconds. Prices come from Yahoo Finance and can be a few minutes late.</p>", 5)}
  <div class="foot"><span>{{SITE}}: Presenter's guide</span><span>Part 1 of 4</span><span>3</span></div>
</div>"""


def page4():
    return f"""
<div class="page" id="p4">
  <div class="head"><span class="part">Part 1. The basics</span><span class="site">{{SITE}}</span></div>
  <h1>Reading a price: volume, candles, trends and risk</h1>
  <p class="lead">Now the language of the chart. Every indicator later is built from these.</p>
  {topic("Volume",
    "<p>Volume is how many shoppers walked into the mall today. A big crowd means lots of interest. A price move that many people joined is more believable than one a few people made.</p>",
    "<p><b>Volume</b> is the number of shares traded in a period. High volume on a move <b>confirms</b> it. Low volume suggests weak conviction. Volume is shown separately from price because it measures participation, not value.</p>",
    "<p>The bars under the chart. Green bars are days the price rose, red bars are days it fell.</p>", 1)}
  {topic("Open, High, Low, Close and the candle",
    "<p>Each day has a little story: where the price <b>started</b>, the <b>highest</b> and <b>lowest</b> it reached, and where it <b>finished</b>. A candle draws that story as one small shape. Green means the day ended higher than it began. Red means lower.</p>",
    "<p>The four daily prices are <b>OHLC</b>: open, high, low, close. A <b>candlestick</b> shows them: the thick <b>body</b> runs from open to close and the thin <b>wicks</b> reach the high and low. A green body means close above open.</p>",
    "<p>Every bar on the main chart is one candle: a day, a week or a month, depending on the Day, Week and Month buttons.</p>", 2,
    extra='<div style="max-width:105mm;margin:6px auto 2px auto">' + candle_svg() + '<p class="small" style="text-align:center">Left: a green candle (the price rose). Right: a red candle (the price fell).</p></div>')}
  {topic("Trend: up, down or sideways",
    "<p>A trend is the direction a price has been walking. Up like climbing stairs, down like descending them, or sideways like walking along a corridor.</p>",
    "<p>A <b>trend</b> is the general direction of price over time: an <b>uptrend</b> (rising highs and lows), a <b>downtrend</b>, or a <b>sideways</b> (range-bound) market. Trend-following aims to go with the trend, not against it.</p>",
    "<p>Most strategies and indicators are really different ways of asking: is there a trend, and how strong is it?</p>", 3)}
  <div class="cols">
  {topic("Risk and return",
    "<p>Return is what you might gain. Risk is how bumpy the road is on the way, and how much you could lose. A very bumpy road can lead somewhere great, or nowhere. Bigger possible gains come with bigger possible losses.</p>",
    "<p><b>Return</b> is the percentage gain or loss on money invested. <b>Risk</b> is the uncertainty of that return, often measured by <b>volatility</b> (how much the price swings). Higher expected return generally needs accepting higher risk. There is no free lunch.</p>", None, 4)}
  {topic("Diversification",
    "<p>Do not carry all your eggs in one basket. If you drop it, they all break. Putting eggs in different baskets means one accident does not ruin everything.</p>",
    "<p><b>Diversification</b> means spreading money across different companies, sectors and asset types, so one bad result hurts less. It lowers the risk specific to one company, but it does not remove the risk of the whole market falling.</p>",
    "<p>The ring on the left shows how your practice money is spread across stocks, ETFs, bonds, futures, options and cash.</p>", 5)}
  </div>
  <div class="foot"><span>{{SITE}}: Presenter's guide</span><span>Part 1 of 4</span><span>4</span></div>
</div>"""


def page5():
    return f"""
<div class="page" id="p5">
  <div class="head"><span class="part">Part 1. The basics</span><span class="site">{{SITE}}</span></div>
  <h1>Your portfolio, practice trading, ETFs and bonds</h1>
  <p class="lead">What you hold, how the site lets you practise, and two things to hold besides shares.</p>
  {topic("Portfolio, cash, profit and return",
    "<p>Your <b>portfolio</b> is your bag of things you own, plus the cash you have not spent. If you start with Rs 1,00,000 and your bag is worth Rs 1,05,000 a week later, you are up Rs 5,000. That is a <b>5% return</b>.</p>",
    "<p>A <b>portfolio</b> is the collection of all your holdings plus <b>cash</b>. Its value is cash plus the current market value of everything held. <b>Profit or loss (P&amp;L)</b> is value minus what you put in, and the <b>return</b> is that as a percentage. If you buy the same share at different prices, your <b>average buy price</b> is the total paid divided by the units.</p>",
    "<p>'Portfolio value' at the top shows the total and the percent change since you started. 'Bought: what you hold' lists each holding with its profit or loss. 'Sold: recent sales' lists your last six sales.</p>", 1)}
  {topic("Paper trading",
    "<p>Cricketers practise in the <b>nets</b> before a real match. Paper trading is the nets for the stock market: real prices, pretend money, nothing to lose, plenty to learn.</p>",
    "<p><b>Paper trading</b> (also called virtual or simulated trading) means placing trades with pretend money at real market prices, to learn how buying, selling, profit and loss work without financial risk. It is a standard way to practise a strategy before committing real capital.</p>",
    "<p>You pick your starting practice money (Rs 50,000, 1 lakh, 5 lakh, 10 lakh or your own amount). The Buy, Sell and Exit all buttons below the chart place practice trades. No brokerage or tax is charged here; real trading has both.</p>", 2)}
  {topic("ETF (exchange-traded fund)",
    "<p>An ETF is a <b>lunchbox with a bit of everything</b>. Instead of buying one food item, you buy one box that has many items inside. One ETF can hold a whole basket of companies, or gold, or silver.</p>",
    "<p>An <b>ETF</b> is a fund that holds a basket of assets (shares of an index, gold, silver or bonds) and is bought and sold on the exchange like a share. A <b>Nifty 50 ETF</b> simply copies the Nifty 50. ETFs give instant <b>diversification</b> with one purchase and usually low costs.</p>",
    "<p>In the Buy pop-up, the 'ETFs and bonds' tab lists Nifty 50, Bank, IT, Gold and Silver ETFs, among others.</p>", 3)}
  {topic("Bond",
    "<p>A bond is <b>lending money</b>. You lend to the government or a company, and they promise to give it back on a set date, plus a little extra (interest) for using it. It is like lending your friend Rs 100 and getting back Rs 106 next year.</p>",
    "<p>A <b>bond</b> is a loan to an issuer (a government or company) that pays regular <b>interest</b> (the <b>coupon</b>) and returns the <b>principal</b> at <b>maturity</b>. Bond prices move opposite to interest rates. Government bonds are generally lower-risk than company bonds, and bonds are usually calmer than shares.</p>",
    "<p>The same 'ETFs and bonds' tab includes bond ETFs such as the Bharat Bond ETF and government-security (G-Sec) ETFs, plus 'liquid' ETFs that behave like cash.</p>", 4)}
  <div class="note"><b class="t">Cannot sell what you do not own.</b> In the practice account you can only sell shares you hold, and you can only buy what your cash allows. If cash runs short, the Buy button says so.</div>
  <div class="foot"><span>{{SITE}}: Presenter's guide</span><span>Part 1 of 4</span><span>5</span></div>
</div>"""


def page6():
    return f"""
<div class="page" id="p6">
  <div class="head"><span class="part">Part 1. The basics</span><span class="site">{{SITE}}</span></div>
  <h1>Futures and options</h1>
  <p class="lead">These are called <b>derivatives</b>: their value comes from (is <i>derived</i> from) something else, such as a share. They are riskier, so go slowly.</p>
  {topic("Future",
    "<p>A farmer and a shopkeeper agree <b>today</b> that the shopkeeper will buy 100 kg of mangoes next month at Rs 80 a kilo, <b>whatever the price turns out to be</b>. Both are <b>bound</b> to the deal. If the price rises to Rs 100, the shopkeeper gained. If it falls to Rs 60, the farmer gained.</p>",
    "<p>A <b>futures contract</b> is an agreement to buy or sell an asset at a fixed price on a fixed date. It is an <b>obligation</b> for both sides. You put down only a small deposit, the <b>margin</b>, so gains and losses are large compared with what you put in: this is <b>leverage</b>.</p>")}
  <div class="cols">
  {topic("Long and short",
    "<p><b>Long</b> = you gain if the price goes <b>up</b>. <b>Short</b> = you gain if it goes <b>down</b>, like betting a ticket price will fall.</p>",
    "<p>Going <b>long</b> profits from a rise; going <b>short</b> profits from a fall. In this app you can go long or short in futures. Shares can only be bought, then sold.</p>")}
  {topic("Margin, lot and expiry",
    "<p><b>Margin</b> is a deposit, like the one you pay to rent a bike. A <b>lot</b> is a fixed pack size, like eggs sold by the dozen. <b>Expiry</b> is the date the deal ends, like a milk packet's date.</p>",
    "<p><b>Margin</b>: a deposit that backs the position (here 15% of the contract's value). A <b>lot</b>: the fixed quantity in one contract. <b>Expiry</b>: the contract's end date (here the last Tuesday of the month). If losses use up the margin, the position is closed automatically.</p>")}
  </div>
  {topic("Option: call and put",
    "<p>You pay a small fee to <b>reserve</b> a phone at today's price for a week. If the price jumps, you use your reservation and save money. If it drops, you just walk away and lose only the small fee. An option is a <b>right</b>, not a must.</p><p>A <b>call</b> = the right to <b>buy</b> (you hope the price goes up). A <b>put</b> = the right to <b>sell</b> (you hope it goes down).</p>",
    "<p>An <b>option</b> gives the buyer the <b>right but not the obligation</b> to buy (a <b>call</b>) or sell (a <b>put</b>) an asset at a fixed price, the <b>strike price</b>, on or before <b>expiry</b>. The price paid for that right is the <b>premium</b>. The most the buyer can lose is the premium, but it can lose all of its value quickly, especially near expiry.</p>")}
  <table><thead><tr><th></th><th>Future</th><th>Option (bought)</th></tr></thead><tbody>
    <tr><td><b>What you hold</b></td><td>An obligation</td><td>A right</td></tr>
    <tr><td><b>Up-front cost</b></td><td>Margin (a deposit)</td><td>Premium (a fee, gone if unused)</td></tr>
    <tr><td><b>Worst case</b></td><td>Large losses compared with the margin</td><td>Lose the whole premium</td></tr>
    <tr><td><b>Direction</b></td><td>Long or short</td><td>Call (up) or put (down)</td></tr>
  </tbody></table>
  <div class="note"><b class="t">How the app does it.</b> Real exchange prices for futures and options are not freely available, so the app <b>calculates</b> them from the live share price with standard formulas (futures price grows at a 6.5% safe rate until expiry; options use the Black-Scholes formula). Lot sizes and margin are <b>simplified for learning</b> (a lot is worth about Rs 2 lakh and margin is 15%). In this app, options can only be <b>bought</b>, not sold. Say that these are <b>estimates, not exchange quotes</b>.</div>
  <div class="screen" style="margin-top:0"><span class="chip a">On the screen</span><p>Click <b>Buy</b> and the pop-up has four tabs: Stocks, ETFs and bonds, Futures, Options. Choose what to trade, how many, and press the button. After an order the pop-up <b>stays open</b>, so you can place the next one, and the page behind updates when you close it.</p></div>
  <div class="foot"><span>{{SITE}}: Presenter's guide</span><span>Part 1 of 4</span><span>6</span></div>
</div>"""


def page7():
    return f"""
<div class="page" id="p7">
  <div class="head"><span class="part">Part 2. The screen</span><span class="site">{{SITE}}</span></div>
  <h1>The dashboard, part by part</h1>
  <p class="lead">One screen holds everything. Match the numbers on the map to the list below.</p>
  <div class="topic" style="padding:6px">{screen_map_svg()}</div>
  <table style="margin-top:6px"><thead><tr><th style="width:4%">#</th><th style="width:24%">What it is</th><th>What it does, in plain words</th></tr></thead><tbody>
  <tr><td>1</td><td>Site name and crest</td><td>The school crest and the name of the site.</td></tr>
  <tr><td>2</td><td>Portfolio value</td><td>Everything you own, in rupees, with the percent gained or lost since you started. Grey 0.00% means no change yet.</td></tr>
  <tr><td>3</td><td>Dark mode and Dashboard view</td><td>Dark mode changes the colours. Dashboard view switches between this wide screen and a simpler phone-style layout. The site picks one by itself: a computer, tablet or iPad opens this wide screen, a phone opens the phone-style layout.</td></tr>
  <tr><td>4</td><td>Demo and Tour</td><td><b>Demo</b> plays a short demo by itself: it searches a company, changes the chart, opens a strategy and makes a practice buy, with a big caption and a spoken voice, and you can change its speed like a video. Touch the screen to stop it. <b>Tour</b> is a guided walk through each part, one step at a time (11 steps).</td></tr>
  <tr><td>5</td><td>The i button</td><td>Opens the About box: what the project is, its limits, credits and the creator.</td></tr>
  <tr><td>6</td><td>Bought and Sold</td><td>What you hold with profit or loss on each, and your last six sales.</td></tr>
  <tr><td>7</td><td>Where your money is</td><td>A ring showing how your money splits between stocks, ETFs, bonds, futures, options and cash. With more than two kinds, the key under it scrolls.</td></tr>
  <tr><td>8</td><td>Leaderboard</td><td>Everyone ranked by <b>percent return</b>, so a small portfolio can beat a big one. Shows the top four and you.</td></tr>
  <tr><td>9</td><td>Combined strategy reading</td><td>A dial that combines the five strategies' votes ([[pgr:p11:p11]]).</td></tr>
  <tr><td>10</td><td>Search stock</td><td>Type a company name, even with a small spelling slip, and press Enter. Both NSE and BSE listings work.</td></tr>
  <tr><td>11</td><td>Chart controls</td><td>1, 2 or 4 charts; Day, Week or Month candles; 6M, 1Y, 2Y or 5Y of history; Fibonacci lines; and a Dark switch for just the chart.</td></tr>
  <tr><td>12</td><td>The chart</td><td>The price history with its tools (next page).</td></tr>
  <tr><td>13</td><td>Buy, Sell, Exit all</td><td>Buy opens the order pop-up. Sell works once you hold something. Exit all sells everything at once; your starting money is not reset.</td></tr>
  <tr><td>14</td><td>Indicators</td><td>Six gauges that read the chart ([[pgr:p9:p10]]). Hover over the small i beside a name for a description.</td></tr>
  <tr><td>15</td><td>The strategies table</td><td>Five CMT strategies and an ML model, each with its vote and its back-test. A Full view button opens a chart and a plain explanation.</td></tr>
  <tr><td>16</td><td>The round chat button</td><td>Stays in the corner while you scroll. It opens 'Ask me anything', a helper that explains words and how the app works. The small blue document button above it opens this guide.</td></tr>
  </tbody></table>
  <div class="foot"><span>{{SITE}}: Presenter's guide</span><span>Part 2 of 4</span><span>7</span></div>
</div>"""


def page8():
    return f"""
<div class="page" id="p8">
  <div class="head"><span class="part">Part 2. The screen</span><span class="site">{{SITE}}</span></div>
  <h1>The chart and its tools</h1>
  <p class="lead">What the lines, bands and bars on the chart mean. You met candles and volume on [[pgr:p4:p4]].</p>
  <div class="cols">
    <div class="topic"><h3>A chart with its tools</h3>{chart_anatomy_svg()}<p class="small">A made-up example to show the parts. A real chart has candles instead of one line.</p></div>
    <div>
    {topic("Moving average (50-day and 200-day)",
      "<p>A day's price jumps about. The <b>average of the last 50 days</b> smooths out the bumps, like finding your average marks over a term instead of one test. The 50-day line shows the recent mood and the 200-day line the long-term mood.</p>",
      "<p>A <b>simple moving average (SMA)</b> is the mean of the last N closes. It filters noise and shows direction. Price above both lines, with the 50-day above the 200-day, is a classic uptrend. A <b>golden cross</b> is the 50-day rising above the 200-day; a <b>death cross</b> is the reverse.</p>",
      "<p>The orange line is the 50-day average and the navy line the 200-day.</p>")}
    </div>
  </div>
  <div class="cols">
  {topic("The grey band (Bollinger Bands)",
    "<p>It is the price's <b>usual lane</b>, like the lane markings on a road. Most days the price stays inside it. When the price swings wildly the lane gets wider; when it is calm the lane narrows.</p>",
    "<p><b>Bollinger Bands</b> (John Bollinger) are a 20-day average with bands <b>2 standard deviations</b> above and below. They widen with volatility. A close outside the band is unusual for that stock, but in a strong trend it can stay there.</p>",
    "<p>The grey shaded area around the price line.</p>")}
  {topic("Fibonacci levels",
    "<p>Drop a ball down a staircase. It does not roll straight down: it pauses on certain steps. Fibonacci lines mark the steps where a price often <b>pauses</b> after a big rise or fall.</p>",
    "<p>After a swing, prices often <b>retrace</b> part of the move before continuing. <b>Fibonacci retracements</b> mark 23.6%, 38.2%, 50%, 61.8% and 78.6% of the swing; <b>extensions</b> (127.2%, 161.8%) mark possible targets beyond it. They are a guide for support and resistance, not a prediction.</p>",
    "<p>Switch on <b>Fibonacci</b> in the chart controls. The lines are drawn from the highest and lowest price in the period you are viewing.</p>")}
  </div>
  <div class="topic" style="margin-bottom:6px"><h3>Fibonacci levels, drawn</h3><div style="max-width:100mm">{fib_svg()}</div></div>
  <div class="cols">
  {topic("Support and resistance",
    "<p><b>Support</b> is a floor the price bounced off before. <b>Resistance</b> is a ceiling it could not get through. They are like the floor and ceiling of a room.</p>",
    "<p><b>Support</b> is a price zone where buying has repeatedly stopped declines; <b>resistance</b> is a zone where selling has stopped advances. A break through either is often read as a change in the balance of buyers and sellers.</p>")}
  {topic("1, 2 or 4 charts; Day, Week or Month",
    "<p>Like zooming a map: one chart for the big picture, or several side by side to compare views. Day, Week and Month decide whether each candle is one day, one week or one month.</p>",
    "<p>Looking at <b>multiple timeframes</b> is standard analysis: the higher timeframe shows the main trend, the lower one the timing. The 1, 2 and 4 buttons set how many charts you see, each in a timeframe of your choice.</p>")}
  </div>
  <div class="foot"><span>{{SITE}}: Presenter's guide</span><span>Part 2 of 4</span><span>8</span></div>
</div>"""
