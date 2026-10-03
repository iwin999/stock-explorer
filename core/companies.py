"""A built-in list of ~100 popular NSE companies, plus the search over it.

Format of each row: (display name, NSE ticker, extra words people might type).
Yahoo Finance adds '.NS' to NSE tickers, e.g. Reliance -> RELIANCE.NS.
"""
import difflib

from core.search import yahoo_search

COMPANIES = [
    # ---- Large companies (Nifty 50 style) ----
    ("Reliance Industries", "RELIANCE.NS", "ril jio"),
    ("Tata Consultancy Services", "TCS.NS", "tcs"),
    ("HDFC Bank", "HDFCBANK.NS", "hdfc"),
    ("ICICI Bank", "ICICIBANK.NS", "icici"),
    ("Infosys", "INFY.NS", "infy"),
    ("Bharti Airtel", "BHARTIARTL.NS", "airtel"),
    ("State Bank of India", "SBIN.NS", "sbi"),
    ("ITC", "ITC.NS", "cigarettes"),
    ("Larsen & Toubro", "LT.NS", "l&t lnt"),
    ("Hindustan Unilever", "HINDUNILVR.NS", "hul"),
    ("Kotak Mahindra Bank", "KOTAKBANK.NS", "kotak"),
    ("Axis Bank", "AXISBANK.NS", "axis"),
    ("Bajaj Finance", "BAJFINANCE.NS", ""),
    ("Maruti Suzuki", "MARUTI.NS", "suzuki"),
    ("Sun Pharmaceutical", "SUNPHARMA.NS", "sun pharma"),
    ("Mahindra & Mahindra", "M&M.NS", "m and m mahindra"),
    ("HCL Technologies", "HCLTECH.NS", "hcl"),
    ("NTPC", "NTPC.NS", ""),
    ("Titan Company", "TITAN.NS", "tanishq watches"),
    ("UltraTech Cement", "ULTRACEMCO.NS", "ultratech"),
    ("Asian Paints", "ASIANPAINT.NS", ""),
    ("Power Grid Corporation", "POWERGRID.NS", ""),
    ("Oil & Natural Gas Corporation", "ONGC.NS", ""),
    ("Tata Steel", "TATASTEEL.NS", ""),
    ("Bajaj Finserv", "BAJAJFINSV.NS", ""),
    ("Nestle India", "NESTLEIND.NS", "maggi"),
    ("Wipro", "WIPRO.NS", ""),
    ("JSW Steel", "JSWSTEEL.NS", ""),
    ("Adani Enterprises", "ADANIENT.NS", "adani"),
    ("Adani Ports", "ADANIPORTS.NS", "adani"),
    ("Coal India", "COALINDIA.NS", ""),
    ("Grasim Industries", "GRASIM.NS", ""),
    ("Tech Mahindra", "TECHM.NS", ""),
    ("Hindalco Industries", "HINDALCO.NS", ""),
    ("Cipla", "CIPLA.NS", ""),
    ("Dr. Reddy's Laboratories", "DRREDDY.NS", "dr reddys"),
    ("Eicher Motors", "EICHERMOT.NS", "royal enfield"),
    ("Bharat Petroleum", "BPCL.NS", "bpcl"),
    ("Tata Consumer Products", "TATACONSUM.NS", "tata tea"),
    ("Apollo Hospitals", "APOLLOHOSP.NS", ""),
    ("SBI Life Insurance", "SBILIFE.NS", ""),
    ("HDFC Life Insurance", "HDFCLIFE.NS", ""),
    ("Britannia Industries", "BRITANNIA.NS", ""),
    ("Hero MotoCorp", "HEROMOTOCO.NS", "hero"),
    ("IndusInd Bank", "INDUSINDBK.NS", ""),
    ("Bajaj Auto", "BAJAJ-AUTO.NS", "bajaj"),
    ("Shriram Finance", "SHRIRAMFIN.NS", ""),
    ("Trent", "TRENT.NS", "westside"),
    ("Bharat Electronics", "BEL.NS", ""),
    ("Eternal (Zomato)", "ETERNAL.NS", "zomato blinkit"),
    ("Jio Financial Services", "JIOFIN.NS", "jio"),
    ("Tata Motors Passenger Vehicles", "TMPV.NS", "tata motors cars jaguar land rover jlr"),
    ("Tata Motors Commercial Vehicles", "TMCV.NS", "tata motors trucks"),
    # ---- More popular companies ----
    ("Avenue Supermarts (DMart)", "DMART.NS", "dmart"),
    ("Hindustan Aeronautics", "HAL.NS", ""),
    ("Vedanta", "VEDL.NS", ""),
    ("DLF", "DLF.NS", "real estate"),
    ("Godrej Consumer Products", "GODREJCP.NS", "godrej"),
    ("Pidilite Industries", "PIDILITIND.NS", "fevicol"),
    ("Siemens", "SIEMENS.NS", ""),
    ("ABB India", "ABB.NS", ""),
    ("Indian Oil Corporation", "IOC.NS", "ioc"),
    ("GAIL (India)", "GAIL.NS", ""),
    ("Punjab National Bank", "PNB.NS", ""),
    ("Bank of Baroda", "BANKBARODA.NS", ""),
    ("Canara Bank", "CANBK.NS", ""),
    ("Tata Power", "TATAPOWER.NS", ""),
    ("Macrotech Developers (Lodha)", "LODHA.NS", "lodha"),
    ("Ambuja Cements", "AMBUJACEM.NS", ""),
    ("Havells India", "HAVELLS.NS", ""),
    ("Dabur India", "DABUR.NS", ""),
    ("Marico", "MARICO.NS", "parachute"),
    ("Colgate-Palmolive India", "COLPAL.NS", "colgate"),
    ("Berger Paints", "BERGEPAINT.NS", ""),
    ("Muthoot Finance", "MUTHOOTFIN.NS", ""),
    ("Cholamandalam Investment", "CHOLAFIN.NS", "chola"),
    ("SRF", "SRF.NS", ""),
    ("TVS Motor Company", "TVSMOTOR.NS", "tvs"),
    ("LTM Limited (LTIMindtree)", "LTM.NS", "ltim lti mindtree"),
    ("Persistent Systems", "PERSISTENT.NS", ""),
    ("Mphasis", "MPHASIS.NS", ""),
    ("Info Edge (Naukri)", "NAUKRI.NS", "naukri"),
    ("IRCTC", "IRCTC.NS", "railway tickets"),
    ("Power Finance Corporation", "PFC.NS", ""),
    ("REC Limited", "RECLTD.NS", "rec"),
    ("InterGlobe Aviation (IndiGo)", "INDIGO.NS", "indigo airline"),
    ("Zydus Lifesciences", "ZYDUSLIFE.NS", "zydus"),
    ("Lupin", "LUPIN.NS", ""),
    ("Torrent Pharmaceuticals", "TORNTPHARM.NS", "torrent"),
    ("Aurobindo Pharma", "AUROPHARMA.NS", ""),
    ("Bosch", "BOSCHLTD.NS", ""),
    ("MRF", "MRF.NS", "tyres"),
    ("One 97 Communications (Paytm)", "PAYTM.NS", "paytm"),
    ("PB Fintech (Policybazaar)", "POLICYBZR.NS", "policybazaar"),
    ("FSN E-Commerce (Nykaa)", "NYKAA.NS", "nykaa"),
    ("IDFC First Bank", "IDFCFIRSTB.NS", ""),
    ("Yes Bank", "YESBANK.NS", ""),
    ("Bharat Heavy Electricals", "BHEL.NS", ""),
    ("Steel Authority of India", "SAIL.NS", ""),
    ("NMDC", "NMDC.NS", ""),
    ("Jindal Steel & Power", "JINDALSTEL.NS", ""),
    ("Adani Power", "ADANIPOWER.NS", "adani"),
    ("Adani Green Energy", "ADANIGREEN.NS", "adani"),
    ("ICICI Lombard", "ICICIGI.NS", ""),
    ("SBI Cards", "SBICARD.NS", ""),
    ("UPL", "UPL.NS", ""),
    ("Page Industries (Jockey)", "PAGEIND.NS", "jockey"),
    ("Jubilant FoodWorks (Domino's)", "JUBLFOOD.NS", "dominos pizza"),
    ("Voltas", "VOLTAS.NS", ""),
    ("Tata Elxsi", "TATAELXSI.NS", ""),
    ("Vodafone Idea", "IDEA.NS", "vi vodafone"),
    ("Hindustan Petroleum", "HINDPETRO.NS", "hpcl"),
    ("Petronet LNG", "PETRONET.NS", ""),
    ("Oberoi Realty", "OBEROIRLTY.NS", ""),
    ("Godrej Properties", "GODREJPROP.NS", "godrej"),
    ("Ashok Leyland", "ASHOKLEY.NS", ""),
    ("Bharat Forge", "BHARATFORG.NS", ""),
    ("Indian Hotels (Taj)", "INDHOTEL.NS", "taj"),
    ("Max Healthcare", "MAXHEALTH.NS", ""),
]

# The market index used as the yardstick for beta, alpha and the other market ratios
BENCHMARK = "^NSEI"   # Nifty 50

# Quick look-up: ticker -> display name
NAME_BY_SYMBOL = {symbol: name for name, symbol, _ in COMPANIES}


def label(symbol):
    """Text shown in the dropdown, e.g. 'Reliance Industries (RELIANCE)'."""
    return f"{NAME_BY_SYMBOL.get(symbol, symbol)} ({symbol.replace('.NS', '')})"


def search_local(query, limit=10):
    """Find companies in OUR list. Handles 'tata motors', 'RELIANCE', 'hdfc', typos.

    Scoring idea: every word the visitor typed must appear somewhere in the
    company's name/ticker/nicknames. If nothing matches, we try 'close
    spellings' with difflib (so 'relience' still finds Reliance).
    """
    words = query.lower().replace("&", " and ").split()
    if not words:
        return []

    matches = []
    for name, symbol, extra in COMPANIES:
        haystack = f"{name} {symbol} {extra}".lower().replace("&", " and ")
        if all(w in haystack for w in words):
            # Names that START with the query rank higher.
            starts = name.lower().startswith(words[0])
            matches.append((0 if starts else 1, name, symbol))
    matches.sort()
    results = [{"symbol": s, "name": n} for _, n, s in matches[:limit]]

    if not results:  # spelling mistakes: compare against each single word of every name
        best = {}
        for name, symbol, extra in COMPANIES:
            for word in (name + " " + extra).lower().split():
                score = difflib.SequenceMatcher(None, query.lower(), word).ratio()
                if score >= 0.75 and score > best.get(symbol, (0,))[0]:
                    best[symbol] = (score, name)
        for symbol, (score, name) in sorted(best.items(), key=lambda kv: -kv[1][0])[:limit]:
            results.append({"symbol": symbol, "name": name})
    return results


def search(query):
    """Our list first; the senior's Yahoo search only if our list finds nothing."""
    local = search_local(query)
    if local:
        return local, "our company list"
    return yahoo_search(query), "Yahoo Finance"
