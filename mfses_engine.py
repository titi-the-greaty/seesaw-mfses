#!/usr/bin/env python3
"""
SEESAW MFSES v5.0 - Stock Analysis Engine
Moat, Fundamentals, Sentiment, Expectations, Safety scoring system
"""

import json
import os
import requests
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

# Configuration
POLYGON_API_KEY = os.environ.get("POLYGON_API_KEY", "oorbpfh9vHYkpK2M4CFjx9f8z3OMfhBD")
BASE_URL = "https://api.polygon.io"

# The 10 Tech Stocks
TICKERS = [
    "AAPL",   # Apple
    "MSFT",   # Microsoft
    "GOOGL",  # Alphabet
    "AMZN",   # Amazon
    "NVDA",   # Nvidia
    "META",   # Meta
    "TSLA",   # Tesla
    "AMD",    # AMD
    "INTC",   # Intel
    "CRM"     # Salesforce
]

# Sample data fallback (used when API fails)
SAMPLE_DATA = {
    "AAPL": {"name": "Apple Inc.", "price": 237.59, "change": 2.31, "volume": 48500000, "market_cap": 3.58e12, "sector": "Computer & Communications Equipment", "eps": 6.75, "eps_growth": 12.5, "debt_equity": 1.87, "dividend_yield": 0.44},
    "MSFT": {"name": "Microsoft Corporation", "price": 442.57, "change": -1.23, "volume": 21000000, "market_cap": 3.29e12, "sector": "Software Publishers", "eps": 12.41, "eps_growth": 18.2, "debt_equity": 0.35, "dividend_yield": 0.72},
    "GOOGL": {"name": "Alphabet Inc.", "price": 198.41, "change": 1.87, "volume": 25600000, "market_cap": 2.42e12, "sector": "Software Publishers", "eps": 7.52, "eps_growth": 32.1, "debt_equity": 0.11, "dividend_yield": 0.45},
    "AMZN": {"name": "Amazon.com Inc.", "price": 229.15, "change": 0.95, "volume": 38200000, "market_cap": 2.42e12, "sector": "General Warehousing and Storage", "eps": 5.22, "eps_growth": 85.4, "debt_equity": 0.58, "dividend_yield": 0.0},
    "NVDA": {"name": "NVIDIA Corporation", "price": 118.42, "change": -2.87, "volume": 312000000, "market_cap": 2.89e12, "sector": "Semiconductor Manufacturing", "eps": 2.94, "eps_growth": 152.3, "debt_equity": 0.41, "dividend_yield": 0.03},
    "META": {"name": "Meta Platforms Inc.", "price": 676.45, "change": 5.21, "volume": 14800000, "market_cap": 1.71e12, "sector": "Software Publishers", "eps": 22.13, "eps_growth": 68.5, "debt_equity": 0.28, "dividend_yield": 0.30},
    "TSLA": {"name": "Tesla Inc.", "price": 398.09, "change": -8.45, "volume": 89500000, "market_cap": 1.28e12, "sector": "Motor Vehicle Manufacturing", "eps": 3.12, "eps_growth": -15.2, "debt_equity": 0.19, "dividend_yield": 0.0},
    "AMD": {"name": "Advanced Micro Devices Inc.", "price": 119.42, "change": -1.58, "volume": 42300000, "market_cap": 193.5e9, "sector": "Semiconductor Manufacturing", "eps": 3.28, "eps_growth": 45.7, "debt_equity": 0.04, "dividend_yield": 0.0},
    "INTC": {"name": "Intel Corporation", "price": 20.87, "change": 0.32, "volume": 58700000, "market_cap": 89.2e9, "sector": "Semiconductor Manufacturing", "eps": -0.85, "eps_growth": -125.0, "debt_equity": 0.51, "dividend_yield": 2.39},
    "CRM": {"name": "Salesforce Inc.", "price": 331.24, "change": 3.87, "volume": 5200000, "market_cap": 317.8e9, "sector": "Software Publishers", "eps": 6.38, "eps_growth": 42.3, "debt_equity": 0.20, "dividend_yield": 0.48}
}

USE_SAMPLE_DATA = False  # Will be set to True if API fails

# ============================================================================
# SCORING FUNCTIONS
# ============================================================================

def calc_moat(market_cap: float) -> int:
    """Moat score based on market cap (competitive advantage)"""
    if market_cap >= 2e12: return 20      # $2T+
    elif market_cap >= 1e12: return 19    # $1T+
    elif market_cap >= 500e9: return 18   # $500B+
    elif market_cap >= 200e9: return 17   # $200B+
    elif market_cap >= 100e9: return 16   # $100B+
    elif market_cap >= 50e9: return 14    # $50B+
    elif market_cap >= 20e9: return 12    # $20B+
    elif market_cap >= 10e9: return 10    # $10B+
    elif market_cap >= 5e9: return 8      # $5B+
    elif market_cap >= 1e9: return 6      # $1B+
    else: return 4


def calc_growth(eps_growth: float) -> int:
    """Growth score based on EPS growth rate"""
    g = max(-50, min(100, eps_growth))

    if g >= 50: return 20
    elif g >= 35: return 18
    elif g >= 25: return 16
    elif g >= 15: return 14
    elif g >= 10: return 12
    elif g >= 5: return 10
    elif g >= 0: return 8
    elif g >= -10: return 6
    elif g >= -25: return 4
    else: return 2


def calc_balance(debt_equity: Optional[float]) -> int:
    """Balance score based on debt/equity ratio"""
    if debt_equity is None or debt_equity < 0:
        return 10  # Unknown

    if debt_equity < 0.1: return 20
    elif debt_equity < 0.3: return 18
    elif debt_equity < 0.5: return 16
    elif debt_equity < 0.7: return 14
    elif debt_equity < 1.0: return 12
    elif debt_equity < 1.5: return 10
    elif debt_equity < 2.0: return 8
    elif debt_equity < 3.0: return 6
    else: return 4


def calc_valuation(eps: float, price: float, eps_growth: float) -> int:
    """Valuation score using Graham formula"""
    if eps <= 0 or price <= 0:
        return 10  # Can't calculate

    # Graham formula: V = EPS * (8.5 + 2g)
    # Cap growth at 15% for conservative Graham value
    g = min(15, max(0, eps_growth))
    graham_value = eps * (8.5 + 2 * g)

    # Calculate upside percentage
    upside = ((graham_value - price) / price) * 100

    if upside >= 100: return 20
    elif upside >= 60: return 18
    elif upside >= 40: return 16
    elif upside >= 20: return 14
    elif upside >= 10: return 12
    elif upside >= 0: return 10
    elif upside >= -20: return 8
    elif upside >= -40: return 6
    else: return 4


def calc_sentiment(div_yield: float, sector: str, eps_growth: float) -> int:
    """Sentiment score based on dividends + sector + momentum"""
    score = 8  # Start at middle

    # Dividend component (+0 to +5)
    if div_yield >= 4: score += 5
    elif div_yield >= 3: score += 4
    elif div_yield >= 2: score += 3
    elif div_yield >= 1: score += 2
    elif div_yield > 0: score += 1

    # Tech sector bonus (+2)
    tech_keywords = ["COMPUTER", "SOFTWARE", "SEMICONDUCTOR", "ELECTRONIC", "TECH"]
    if any(kw in sector.upper() for kw in tech_keywords):
        score += 2

    # Growth momentum (+0 to +3)
    if eps_growth >= 25: score += 3
    elif eps_growth >= 15: score += 2
    elif eps_growth >= 5: score += 1

    return min(20, max(1, score))


def calc_mfses_scores(moat: int, growth: int, balance: int, valuation: int, sentiment: int) -> tuple:
    """Calculate Short, Mid, Long term MFSES scores"""

    # Short-term (0-6 months): Growth & Momentum focused
    short = (
        growth * 0.30 +      # 30% - Growth matters most short-term
        sentiment * 0.25 +   # 25% - Market sentiment
        valuation * 0.20 +   # 20% - Current value
        moat * 0.15 +        # 15% - Some stability
        balance * 0.10       # 10% - Less critical short-term
    )

    # Mid-term (1-3 years): Balanced approach
    mid = (
        moat * 0.25 +        # 25% - Quality matters
        valuation * 0.25 +   # 25% - Value realization
        growth * 0.20 +      # 20% - Continued growth
        balance * 0.15 +     # 15% - Financial health
        sentiment * 0.15     # 15% - Market perception
    )

    # Long-term (5+ years): Quality & Safety focused
    long = (
        moat * 0.30 +        # 30% - Competitive advantage key
        balance * 0.25 +     # 25% - Financial stability
        valuation * 0.20 +   # 20% - Entry price matters
        growth * 0.15 +      # 15% - Sustainable growth
        sentiment * 0.10     # 10% - Less noise long-term
    )

    return round(short, 1), round(mid, 1), round(long, 1)


def calc_markov_state(volume: float, avg_volume: float, change_pct: float) -> str:
    """Determine stock activity state"""
    activity = 0

    # Volume component
    if avg_volume > 0:
        vol_ratio = volume / avg_volume
        if vol_ratio > 2.5: activity += 3
        elif vol_ratio > 1.5: activity += 2
        elif vol_ratio > 1.0: activity += 1
        elif vol_ratio < 0.5: activity -= 1

    # Price movement component
    abs_change = abs(change_pct)
    if abs_change > 5: activity += 3
    elif abs_change > 3: activity += 2
    elif abs_change > 1.5: activity += 1

    if activity >= 5: return "HOT"
    elif activity >= 3: return "WARM"
    elif activity >= 1: return "COLD"
    else: return "FROZEN"


def calc_graham_value(eps: float, eps_growth: float) -> float:
    """Calculate Graham intrinsic value"""
    if eps <= 0:
        return 0
    g = min(15, max(0, eps_growth))
    return eps * (8.5 + 2 * g)


# ============================================================================
# API FUNCTIONS
# ============================================================================

def api_request(endpoint: str, params: Dict = None) -> Optional[Dict]:
    """Make a request to Polygon API"""
    if params is None:
        params = {}
    params["apiKey"] = POLYGON_API_KEY

    url = f"{BASE_URL}{endpoint}"
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"  API Error for {endpoint}: {e}")
        return None


def get_price_data(ticker: str) -> Dict:
    """Fetch price data from previous day aggregates"""
    data = api_request(f"/v2/aggs/ticker/{ticker}/prev")

    if data and data.get("results"):
        result = data["results"][0]
        close = result.get("c", 0)
        open_price = result.get("o", 0)
        change = close - open_price
        change_pct = (change / open_price * 100) if open_price else 0

        return {
            "price": close,
            "open": open_price,
            "high": result.get("h", 0),
            "low": result.get("l", 0),
            "volume": result.get("v", 0),
            "change": change,
            "change_pct": change_pct
        }

    return {"price": 0, "open": 0, "high": 0, "low": 0, "volume": 0, "change": 0, "change_pct": 0}


def get_ticker_details(ticker: str) -> Dict:
    """Fetch company details"""
    data = api_request(f"/v3/reference/tickers/{ticker}")

    if data and data.get("results"):
        result = data["results"]
        return {
            "name": result.get("name", ticker),
            "market_cap": result.get("market_cap", 0) or 0,
            "sector": result.get("sic_description", "Unknown"),
            "shares_outstanding": result.get("share_class_shares_outstanding", 0) or result.get("weighted_shares_outstanding", 0) or 0,
            "logo_url": result.get("branding", {}).get("icon_url", ""),
            "homepage": result.get("homepage_url", "")
        }

    return {"name": ticker, "market_cap": 0, "sector": "Unknown", "shares_outstanding": 0, "logo_url": "", "homepage": ""}


def get_financials(ticker: str, shares_outstanding: int) -> Dict:
    """Fetch financial data and calculate metrics"""
    DEBUG_TICKERS = ["META", "AAPL", "INTC"]  # Tickers to debug

    data = api_request(f"/vX/reference/financials", {
        "ticker": ticker,
        "limit": 5,
        "timeframe": "quarterly",
        "sort": "filing_date",
        "order": "desc"
    })

    result = {
        "eps": 0,
        "eps_growth": 0,
        "debt_equity": None,
        "total_debt": 0,
        "total_equity": 0,
        "net_income": 0,
        "revenue": 0,
        "debug_info": {}
    }

    if not data or not data.get("results"):
        if ticker in DEBUG_TICKERS:
            print(f"  DEBUG {ticker}: No financial data returned from API")
        return result

    financials = data["results"]

    # Debug: Show all filing periods
    if ticker in DEBUG_TICKERS:
        print(f"  DEBUG {ticker}: Found {len(financials)} quarterly filings")
        for i, f in enumerate(financials):
            period = f.get("fiscal_period", "?")
            year = f.get("fiscal_year", "?")
            filing_date = f.get("filing_date", "?")
            print(f"    [{i}] {period} {year} (filed: {filing_date})")

    # Get most recent quarter data
    if financials:
        latest = financials[0].get("financials", {})

        # Income statement
        income = latest.get("income_statement", {})
        net_income = income.get("net_income_loss", {}).get("value", 0) or 0
        revenue = income.get("revenues", {}).get("value", 0) or 0

        # Calculate EPS
        eps = 0
        if shares_outstanding > 0 and net_income != 0:
            # Annualize quarterly net income (multiply by 4)
            eps = (net_income * 4) / shares_outstanding

        # Balance sheet for debt/equity
        balance = latest.get("balance_sheet", {})

        # Get individual components for debugging
        liabilities = balance.get("liabilities", {}).get("value", 0) or 0
        long_term_debt = balance.get("long_term_debt", {}).get("value", 0) or 0
        current_debt = balance.get("current_debt", {}).get("value", 0) or 0
        noncurrent_liabilities = balance.get("noncurrent_liabilities", {}).get("value", 0) or 0
        current_liabilities = balance.get("current_liabilities", {}).get("value", 0) or 0

        # Use FINANCIAL DEBT for D/E ratio (not total liabilities)
        # Financial debt = long-term debt + current portion of debt
        total_debt = long_term_debt + current_debt
        if total_debt == 0:
            # Fallback: try to estimate financial debt from noncurrent liabilities
            # (which often includes long-term debt as a major component)
            # But cap at 50% of total liabilities to avoid including operating liabilities
            total_debt = min(noncurrent_liabilities, liabilities * 0.5) if noncurrent_liabilities > 0 else 0

        total_equity = balance.get("equity", {}).get("value", 0) or 0
        if total_equity == 0:
            total_equity = balance.get("stockholders_equity", {}).get("value", 0) or 0

        debt_equity = None
        if total_equity > 0:
            debt_equity = total_debt / total_equity

        # Debug balance sheet for AAPL
        if ticker in DEBUG_TICKERS:
            print(f"  DEBUG {ticker} Balance Sheet:")
            print(f"    liabilities (total): ${liabilities/1e9:.2f}B")
            print(f"    long_term_debt: ${long_term_debt/1e9:.2f}B")
            print(f"    current_debt: ${current_debt/1e9:.2f}B")
            print(f"    noncurrent_liabilities: ${noncurrent_liabilities/1e9:.2f}B")
            print(f"    current_liabilities: ${current_liabilities/1e9:.2f}B")
            print(f"    equity: ${total_equity/1e9:.2f}B")
            print(f"    D/E ratio: {debt_equity:.2f}" if debt_equity else "    D/E ratio: N/A")

        result.update({
            "eps": eps,
            "debt_equity": debt_equity,
            "total_debt": total_debt,
            "total_equity": total_equity,
            "net_income": net_income,
            "revenue": revenue
        })

    # Calculate EPS growth (compare to SAME quarter from year ago)
    current_period = financials[0].get("fiscal_period", "")
    current_year = int(financials[0].get("fiscal_year", 0))
    target_year = current_year - 1

    # Find the same quarter from last year
    year_ago_filing = None
    for f in financials:
        f_year = int(f.get("fiscal_year", 0))
        if f.get("fiscal_period") == current_period and f_year == target_year:
            year_ago_filing = f
            break

    if ticker in DEBUG_TICKERS:
        print(f"  DEBUG {ticker} EPS Growth Calculation:")
        print(f"    Current quarter: {current_period} {current_year}")
        print(f"    Looking for: {current_period} {target_year}")
        print(f"    Found year-ago filing: {'Yes' if year_ago_filing else 'No'}")

    if year_ago_filing:
        year_ago = year_ago_filing.get("financials", {})
        year_ago_income = year_ago.get("income_statement", {})
        year_ago_net_income = year_ago_income.get("net_income_loss", {}).get("value", 0) or 0

        if ticker in DEBUG_TICKERS:
            print(f"    Current net income: ${net_income/1e9:.2f}B")
            print(f"    Year-ago net income: ${year_ago_net_income/1e9:.2f}B")
            print(f"    Shares outstanding: {shares_outstanding/1e9:.2f}B")

        if shares_outstanding > 0 and year_ago_net_income != 0:
            year_ago_eps = (year_ago_net_income * 4) / shares_outstanding
            current_eps = result["eps"]

            if year_ago_eps != 0:
                result["eps_growth"] = ((current_eps - year_ago_eps) / abs(year_ago_eps)) * 100

            if ticker in DEBUG_TICKERS:
                print(f"    Current EPS (annualized): ${current_eps:.2f}")
                print(f"    Year-ago EPS (annualized): ${year_ago_eps:.2f}")
                print(f"    EPS Growth: {result['eps_growth']:.1f}%")
        else:
            if ticker in DEBUG_TICKERS:
                print(f"    WARNING: Cannot calculate (shares={shares_outstanding}, year_ago_income={year_ago_net_income})")
    else:
        if ticker in DEBUG_TICKERS:
            print(f"    WARNING: No matching year-ago quarter found in API data")
            print(f"    Available filings: {[(f.get('fiscal_period'), f.get('fiscal_year')) for f in financials]}")

    return result


def get_dividends(ticker: str, price: float) -> Dict:
    """Fetch dividend data"""
    data = api_request(f"/v3/reference/dividends", {
        "ticker": ticker,
        "limit": 4,
        "order": "desc"
    })

    result = {
        "annual_dividend": 0,
        "dividend_yield": 0
    }

    if data and data.get("results"):
        dividends = data["results"]
        annual_dividend = sum(d.get("cash_amount", 0) for d in dividends)

        result["annual_dividend"] = annual_dividend
        if price > 0:
            result["dividend_yield"] = (annual_dividend / price) * 100

    return result


def get_avg_volume(ticker: str) -> float:
    """Get 30-day average volume"""
    data = api_request(f"/v2/aggs/ticker/{ticker}/range/1/day/2024-01-01/2025-12-31", {
        "limit": 30,
        "sort": "desc"
    })

    if data and data.get("results"):
        volumes = [r.get("v", 0) for r in data["results"]]
        if volumes:
            return sum(volumes) / len(volumes)

    return 0


# ============================================================================
# MAIN PROCESSING
# ============================================================================

def validate_stock(stock: Dict) -> bool:
    """Ensure we have real data, not placeholders"""
    issues = []

    if stock["market_cap"] == 0:
        issues.append("Missing market cap")
    if stock["price"] == 0:
        issues.append("Missing price")

    if issues:
        print(f"  WARNING {stock['ticker']}: {', '.join(issues)}")
        return False
    return True


def create_stock_from_sample(ticker: str) -> Optional[Dict]:
    """Create stock data from sample data"""
    if ticker not in SAMPLE_DATA:
        return None

    sample = SAMPLE_DATA[ticker]
    price = sample["price"]
    change = sample["change"]
    change_pct = (change / (price - change) * 100) if price != change else 0
    volume = sample["volume"]
    market_cap = sample["market_cap"]
    sector = sample["sector"]
    eps = sample["eps"]
    eps_growth = sample["eps_growth"]
    debt_equity = sample["debt_equity"]
    dividend_yield = sample["dividend_yield"]

    # Calculate scores
    moat = calc_moat(market_cap)
    growth = calc_growth(eps_growth)
    balance = calc_balance(debt_equity)
    valuation = calc_valuation(eps, price, eps_growth)
    sentiment = calc_sentiment(dividend_yield, sector, eps_growth)

    # Calculate MFSES composite scores
    short_score, mid_score, long_score = calc_mfses_scores(moat, growth, balance, valuation, sentiment)

    # Calculate Markov state
    avg_volume = volume * 0.9  # Approximate
    state = calc_markov_state(volume, avg_volume, change_pct)

    # Calculate Graham value
    graham_value = calc_graham_value(eps, eps_growth)
    upside = ((graham_value - price) / price * 100) if price > 0 else 0

    # Simple audit for sample data
    audit = {
        "moat": {"input": f"Market Cap: ${market_cap/1e9:.1f}B", "bracket": "Sample", "formula": "Market cap brackets", "score": moat},
        "growth": {"input": f"EPS Growth: {eps_growth:.1f}%", "bracket": "Sample", "formula": "EPS growth brackets", "score": growth},
        "balance": {"input": f"D/E Ratio: {debt_equity:.2f}", "raw_debt": 0, "raw_equity": 0, "bracket": "Sample", "formula": "D/E brackets", "score": balance},
        "valuation": {"input": f"EPS: ${eps:.2f}, Price: ${price:.2f}", "graham_formula": "Sample", "graham_value": round(graham_value, 2), "upside_pct": round(upside, 1), "bracket": "Sample", "score": valuation},
        "sentiment": {"input": "Sample data", "breakdown": "Sample", "score": sentiment},
        "warnings": ["Using sample data - API unavailable"]
    }

    return {
        "ticker": ticker,
        "name": sample["name"],
        "price": round(price, 2),
        "change": round(change, 2),
        "change_pct": round(change_pct, 2),
        "volume": int(volume),
        "avg_volume": int(avg_volume),
        "market_cap": market_cap,
        "sector": sector,
        "logo_url": "",
        "homepage": "",
        "eps": round(eps, 2),
        "eps_growth": round(eps_growth, 1),
        "debt_equity": round(debt_equity, 2) if debt_equity is not None else None,
        "dividend_yield": round(dividend_yield, 2),
        "annual_dividend": round(dividend_yield * price / 100, 2),
        "total_debt": 0,
        "total_equity": 0,
        "graham_value": round(graham_value, 2),
        "upside": round(upside, 1),
        "moat": moat,
        "growth": growth,
        "balance": balance,
        "valuation": valuation,
        "sentiment": sentiment,
        "short_score": short_score,
        "mid_score": mid_score,
        "long_score": long_score,
        "state": state,
        "audit": audit
    }


def process_ticker(ticker: str) -> Optional[Dict]:
    """Process a single ticker and return all data"""
    print(f"Processing {ticker}...")

    # Fetch all data
    price_data = get_price_data(ticker)
    details = get_ticker_details(ticker)
    financials = get_financials(ticker, details["shares_outstanding"])
    dividends = get_dividends(ticker, price_data["price"])
    avg_volume = get_avg_volume(ticker)

    # Calculate scores
    moat = calc_moat(details["market_cap"])
    growth = calc_growth(financials["eps_growth"])
    balance = calc_balance(financials["debt_equity"])
    valuation = calc_valuation(financials["eps"], price_data["price"], financials["eps_growth"])
    sentiment = calc_sentiment(dividends["dividend_yield"], details["sector"], financials["eps_growth"])

    # Calculate MFSES composite scores
    short_score, mid_score, long_score = calc_mfses_scores(moat, growth, balance, valuation, sentiment)

    # Calculate Markov state
    state = calc_markov_state(price_data["volume"], avg_volume, price_data["change_pct"])

    # Calculate Graham value
    graham_value = calc_graham_value(financials["eps"], financials["eps_growth"])
    upside = ((graham_value - price_data["price"]) / price_data["price"] * 100) if price_data["price"] > 0 else 0

    # Build audit/fact-check data
    warnings = []
    debt_equity_val = financials["debt_equity"]

    # Validation warnings
    if debt_equity_val is None or debt_equity_val == 0:
        warnings.append("D/E ratio is 0 or missing - data may be incomplete")
    if financials["eps"] == 0 and details["market_cap"] > 50e9:
        warnings.append("EPS is 0 for large-cap stock - verify data")
    if details["market_cap"] == 0:
        warnings.append("Market cap is 0 - data missing")
    if financials["total_debt"] == 0 and financials["total_equity"] > 0:
        warnings.append("Total debt is 0 - may only have equity data")

    # Expected market cap ranges for known tickers
    expected_caps = {
        "AAPL": (2e12, 4e12), "MSFT": (2e12, 4e12), "GOOGL": (1.5e12, 3e12),
        "AMZN": (1.5e12, 3e12), "NVDA": (1e12, 5e12), "META": (800e9, 2e12),
        "TSLA": (500e9, 2e12), "AMD": (100e9, 400e9), "INTC": (50e9, 250e9),
        "CRM": (200e9, 400e9)
    }
    if ticker in expected_caps:
        low, high = expected_caps[ticker]
        if details["market_cap"] < low * 0.5 or details["market_cap"] > high * 2:
            warnings.append(f"Market cap ${details['market_cap']/1e9:.0f}B outside expected range ${low/1e9:.0f}B-${high/1e9:.0f}B")

    # Moat audit
    def get_moat_bracket(mc):
        if mc >= 2e12: return "$2T+", 20
        elif mc >= 1e12: return "$1T+", 19
        elif mc >= 500e9: return "$500B+", 18
        elif mc >= 200e9: return "$200B+", 17
        elif mc >= 100e9: return "$100B+", 16
        elif mc >= 50e9: return "$50B+", 14
        elif mc >= 20e9: return "$20B+", 12
        elif mc >= 10e9: return "$10B+", 10
        elif mc >= 5e9: return "$5B+", 8
        elif mc >= 1e9: return "$1B+", 6
        else: return "<$1B", 4

    moat_bracket, _ = get_moat_bracket(details["market_cap"])

    # Growth audit
    def get_growth_bracket(g):
        g = max(-50, min(100, g))
        if g >= 50: return "≥50%", 20
        elif g >= 35: return "35-50%", 18
        elif g >= 25: return "25-35%", 16
        elif g >= 15: return "15-25%", 14
        elif g >= 10: return "10-15%", 12
        elif g >= 5: return "5-10%", 10
        elif g >= 0: return "0-5%", 8
        elif g >= -10: return "-10-0%", 6
        elif g >= -25: return "-25--10%", 4
        else: return "<-25%", 2

    growth_bracket, _ = get_growth_bracket(financials["eps_growth"])

    # Balance audit
    def get_balance_bracket(de):
        if de is None or de < 0: return "Unknown", 10
        if de < 0.1: return "<0.1", 20
        elif de < 0.3: return "0.1-0.3", 18
        elif de < 0.5: return "0.3-0.5", 16
        elif de < 0.7: return "0.5-0.7", 14
        elif de < 1.0: return "0.7-1.0", 12
        elif de < 1.5: return "1.0-1.5", 10
        elif de < 2.0: return "1.5-2.0", 8
        elif de < 3.0: return "2.0-3.0", 6
        else: return "≥3.0", 4

    balance_bracket, _ = get_balance_bracket(debt_equity_val)

    # Valuation audit
    g_capped = min(15, max(0, financials["eps_growth"]))
    graham_calc = financials["eps"] * (8.5 + 2 * g_capped) if financials["eps"] > 0 else 0

    def get_valuation_bracket(up):
        if up >= 100: return "≥100% upside", 20
        elif up >= 60: return "60-100% upside", 18
        elif up >= 40: return "40-60% upside", 16
        elif up >= 20: return "20-40% upside", 14
        elif up >= 10: return "10-20% upside", 12
        elif up >= 0: return "0-10% upside", 10
        elif up >= -20: return "-20-0% upside", 8
        elif up >= -40: return "-40--20% upside", 6
        else: return "<-40% upside", 4

    valuation_bracket, _ = get_valuation_bracket(upside)

    # Sentiment audit
    sent_base = 8
    sent_div = 5 if dividends["dividend_yield"] >= 4 else (4 if dividends["dividend_yield"] >= 3 else (3 if dividends["dividend_yield"] >= 2 else (2 if dividends["dividend_yield"] >= 1 else (1 if dividends["dividend_yield"] > 0 else 0))))
    tech_keywords = ["COMPUTER", "SOFTWARE", "SEMICONDUCTOR", "ELECTRONIC", "TECH"]
    sent_tech = 2 if any(kw in details["sector"].upper() for kw in tech_keywords) else 0
    sent_growth = 3 if financials["eps_growth"] >= 25 else (2 if financials["eps_growth"] >= 15 else (1 if financials["eps_growth"] >= 5 else 0))

    audit = {
        "moat": {
            "input": f"Market Cap: ${details['market_cap']/1e9:.1f}B",
            "bracket": moat_bracket,
            "formula": "Market cap size brackets",
            "score": moat
        },
        "growth": {
            "input": f"EPS Growth: {financials['eps_growth']:.1f}%",
            "bracket": growth_bracket,
            "formula": "EPS growth rate brackets",
            "score": growth
        },
        "balance": {
            "input": f"D/E Ratio: {debt_equity_val:.2f}" if debt_equity_val is not None else "D/E Ratio: N/A",
            "raw_debt": financials["total_debt"],
            "raw_equity": financials["total_equity"],
            "bracket": balance_bracket,
            "formula": "Debt/Equity ratio brackets",
            "score": balance
        },
        "valuation": {
            "input": f"EPS: ${financials['eps']:.2f}, Price: ${price_data['price']:.2f}",
            "graham_formula": f"EPS × (8.5 + 2 × min(15, {financials['eps_growth']:.1f}%))",
            "graham_value": round(graham_calc, 2),
            "upside_pct": round(upside, 1),
            "bracket": valuation_bracket,
            "score": valuation
        },
        "sentiment": {
            "input": f"Div Yield: {dividends['dividend_yield']:.2f}%, Sector: {details['sector']}, Growth: {financials['eps_growth']:.1f}%",
            "breakdown": f"Base(8) + Div(+{sent_div}) + Tech(+{sent_tech}) + Growth(+{sent_growth}) = {sent_base + sent_div + sent_tech + sent_growth}",
            "score": sentiment
        },
        "warnings": warnings
    }

    stock = {
        "ticker": ticker,
        "name": details["name"],
        "price": round(price_data["price"], 2),
        "change": round(price_data["change"], 2),
        "change_pct": round(price_data["change_pct"], 2),
        "volume": int(price_data["volume"]),
        "avg_volume": int(avg_volume),
        "market_cap": details["market_cap"],
        "sector": details["sector"],
        "logo_url": details["logo_url"],
        "homepage": details["homepage"],

        # Financials
        "eps": round(financials["eps"], 2),
        "eps_growth": round(financials["eps_growth"], 1),
        "debt_equity": round(financials["debt_equity"], 2) if financials["debt_equity"] is not None else None,
        "dividend_yield": round(dividends["dividend_yield"], 2),
        "annual_dividend": round(dividends["annual_dividend"], 2),
        "total_debt": financials["total_debt"],
        "total_equity": financials["total_equity"],

        # Graham valuation
        "graham_value": round(graham_value, 2),
        "upside": round(upside, 1),

        # Factor scores (0-20)
        "moat": moat,
        "growth": growth,
        "balance": balance,
        "valuation": valuation,
        "sentiment": sentiment,

        # MFSES composite scores
        "short_score": short_score,
        "mid_score": mid_score,
        "long_score": long_score,

        # Markov state
        "state": state,

        # Audit data
        "audit": audit
    }

    # Validate - fall back to sample data if API failed
    if not validate_stock(stock):
        print(f"  Data validation failed for {ticker}, using sample data")
        sample_stock = create_stock_from_sample(ticker)
        if sample_stock:
            return sample_stock

    return stock


def generate_html(stocks: List[Dict], timestamp: str) -> str:
    """Generate the dashboard HTML"""

    def score_color(score: int) -> str:
        if score >= 16: return "#22c55e"
        elif score >= 12: return "#84cc16"
        elif score >= 8: return "#eab308"
        elif score >= 4: return "#f97316"
        else: return "#ef4444"

    def format_market_cap(cap: float) -> str:
        if cap >= 1e12:
            return f"${cap/1e12:.2f}T"
        elif cap >= 1e9:
            return f"${cap/1e9:.1f}B"
        elif cap >= 1e6:
            return f"${cap/1e6:.1f}M"
        return f"${cap:.0f}"

    def format_volume(vol: float) -> str:
        if vol >= 1e9:
            return f"{vol/1e9:.1f}B"
        elif vol >= 1e6:
            return f"{vol/1e6:.1f}M"
        elif vol >= 1e3:
            return f"{vol/1e3:.1f}K"
        return str(int(vol))

    def state_color(state: str) -> str:
        colors = {
            "HOT": "#ef4444",
            "WARM": "#f97316",
            "COLD": "#3b82f6",
            "FROZEN": "#6b7280"
        }
        return colors.get(state, "#6b7280")

    # Generate table rows
    rows = []
    for stock in stocks:
        logo_html = f'<img src="{stock["logo_url"]}?apiKey={POLYGON_API_KEY}" alt="{stock["ticker"]}" class="stock-logo" onerror="this.style.display=\'none\'">' if stock["logo_url"] else ''

        change_class = "positive" if stock["change"] >= 0 else "negative"
        change_sign = "+" if stock["change"] >= 0 else ""
        debt_equity_str = f'{stock["debt_equity"]:.2f}' if stock["debt_equity"] is not None else 'N/A'
        upside_class = "positive" if stock["upside"] >= 0 else "negative"
        upside_sign = "+" if stock["upside"] >= 0 else ""
        eps_growth_sign = "+" if stock["eps_growth"] >= 0 else ""

        # Extract audit data safely
        audit = stock.get("audit", {})
        audit_warnings = audit.get("warnings", [])
        audit_warnings_html = "".join([f'<div class="audit-warning">&#9888;&#65039; {w}</div>' for w in audit_warnings])

        audit_moat = audit.get("moat", {})
        audit_growth = audit.get("growth", {})
        audit_balance = audit.get("balance", {})
        audit_valuation = audit.get("valuation", {})
        audit_sentiment = audit.get("sentiment", {})

        row = f'''
        <tr class="stock-row" data-ticker="{stock["ticker"]}">
            <td class="logo-cell">{logo_html}</td>
            <td class="ticker-cell"><strong>{stock["ticker"]}</strong></td>
            <td class="name-cell">{stock["name"][:20]}</td>
            <td class="price-cell">${stock["price"]:.2f}</td>
            <td class="change-cell {change_class}">{change_sign}{stock["change"]:.2f}</td>
            <td class="pct-cell {change_class}">{change_sign}{stock["change_pct"]:.2f}%</td>
            <td class="volume-cell">{format_volume(stock["volume"])}</td>
            <td class="cap-cell">{format_market_cap(stock["market_cap"])}</td>
            <td class="score-cell" style="background-color: {score_color(stock["moat"])}">{stock["moat"]}</td>
            <td class="score-cell" style="background-color: {score_color(stock["growth"])}">{stock["growth"]}</td>
            <td class="score-cell" style="background-color: {score_color(stock["balance"])}">{stock["balance"]}</td>
            <td class="score-cell" style="background-color: {score_color(stock["valuation"])}">{stock["valuation"]}</td>
            <td class="score-cell" style="background-color: {score_color(stock["sentiment"])}">{stock["sentiment"]}</td>
            <td class="state-cell" style="color: {state_color(stock["state"])}">{stock["state"]}</td>
            <td class="menu-cell">
                <button class="audit-btn" onclick="toggleAudit('{stock["ticker"]}')" title="Fact Check">&#128269;</button>
                <button class="menu-btn" onclick="toggleDetails('{stock["ticker"]}')">&#8942;</button>
            </td>
        </tr>
        <tr class="details-row" id="details-{stock["ticker"]}" style="display: none;">
            <td colspan="16">
                <div class="details-content">
                    <div class="mfses-scores">
                        <div class="score-bar">
                            <span class="score-label">Short-term:</span>
                            <div class="bar-container">
                                <div class="bar" style="width: {stock["short_score"]*5}%; background: {score_color(int(stock["short_score"]))}"></div>
                            </div>
                            <span class="score-value">{stock["short_score"]}</span>
                        </div>
                        <div class="score-bar">
                            <span class="score-label">Mid-term:</span>
                            <div class="bar-container">
                                <div class="bar" style="width: {stock["mid_score"]*5}%; background: {score_color(int(stock["mid_score"]))}"></div>
                            </div>
                            <span class="score-value">{stock["mid_score"]}</span>
                        </div>
                        <div class="score-bar">
                            <span class="score-label">Long-term:</span>
                            <div class="bar-container">
                                <div class="bar" style="width: {stock["long_score"]*5}%; background: {score_color(int(stock["long_score"]))}"></div>
                            </div>
                            <span class="score-value">{stock["long_score"]}</span>
                        </div>
                    </div>
                    <div class="metrics-grid">
                        <div class="metric">
                            <span class="metric-label">Graham Value</span>
                            <span class="metric-value">${stock["graham_value"]:.2f}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Upside</span>
                            <span class="metric-value {upside_class}">{upside_sign}{stock["upside"]:.1f}%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">EPS</span>
                            <span class="metric-value">${stock["eps"]:.2f}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">EPS Growth</span>
                            <span class="metric-value">{eps_growth_sign}{stock["eps_growth"]:.1f}%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Debt/Equity</span>
                            <span class="metric-value">{debt_equity_str}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Div Yield</span>
                            <span class="metric-value">{stock["dividend_yield"]:.2f}%</span>
                        </div>
                    </div>
                    <div class="links">
                        <a href="https://finance.yahoo.com/quote/{stock["ticker"]}" target="_blank" class="link-btn">Yahoo Finance</a>
                        <a href="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={stock["ticker"]}&type=10-&dateb=&owner=include&count=40" target="_blank" class="link-btn">SEC Filings</a>
                    </div>
                </div>
            </td>
        </tr>
        <tr class="audit-row" id="audit-{stock["ticker"]}" style="display: none;">
            <td colspan="16">
                <div class="audit-panel">
                    <h3>&#128269; Fact Check: {stock["ticker"]}</h3>
                    {audit_warnings_html}
                    <div class="audit-grid">
                        <div class="audit-card">
                            <div class="audit-header" style="background: {score_color(stock["moat"])}">M = {stock["moat"]}</div>
                            <div class="audit-body">
                                <div><strong>Input:</strong> {audit_moat.get("input", "N/A")}</div>
                                <div><strong>Bracket:</strong> {audit_moat.get("bracket", "N/A")}</div>
                                <div><strong>Formula:</strong> {audit_moat.get("formula", "N/A")}</div>
                            </div>
                        </div>
                        <div class="audit-card">
                            <div class="audit-header" style="background: {score_color(stock["growth"])}">G = {stock["growth"]}</div>
                            <div class="audit-body">
                                <div><strong>Input:</strong> {audit_growth.get("input", "N/A")}</div>
                                <div><strong>Bracket:</strong> {audit_growth.get("bracket", "N/A")}</div>
                                <div><strong>Formula:</strong> {audit_growth.get("formula", "N/A")}</div>
                            </div>
                        </div>
                        <div class="audit-card">
                            <div class="audit-header" style="background: {score_color(stock["balance"])}">B = {stock["balance"]}</div>
                            <div class="audit-body">
                                <div><strong>Input:</strong> {audit_balance.get("input", "N/A")}</div>
                                <div><strong>Raw Debt:</strong> ${stock.get("total_debt", 0)/1e9:.2f}B</div>
                                <div><strong>Raw Equity:</strong> ${stock.get("total_equity", 0)/1e9:.2f}B</div>
                                <div><strong>Bracket:</strong> {audit_balance.get("bracket", "N/A")}</div>
                            </div>
                        </div>
                        <div class="audit-card">
                            <div class="audit-header" style="background: {score_color(stock["valuation"])}">V = {stock["valuation"]}</div>
                            <div class="audit-body">
                                <div><strong>Input:</strong> {audit_valuation.get("input", "N/A")}</div>
                                <div><strong>Graham:</strong> ${audit_valuation.get("graham_value", 0):.2f}</div>
                                <div><strong>Upside:</strong> {audit_valuation.get("upside_pct", 0):.1f}%</div>
                                <div><strong>Bracket:</strong> {audit_valuation.get("bracket", "N/A")}</div>
                            </div>
                        </div>
                        <div class="audit-card">
                            <div class="audit-header" style="background: {score_color(stock["sentiment"])}">S = {stock["sentiment"]}</div>
                            <div class="audit-body">
                                <div><strong>Breakdown:</strong> {audit_sentiment.get("breakdown", "N/A")}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </td>
        </tr>'''
        rows.append(row)

    table_rows = "\n".join(rows)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SEESAW MFSES - Financial Freedom</title>
    <style>
        :root {{
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-tertiary: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --border-color: #475569;
            --pink: #DB1478;
            --blue: #2A84C7;
        }}

        [data-theme="light"] {{
            --bg-primary: #f8fafc;
            --bg-secondary: #e2e8f0;
            --bg-tertiary: #cbd5e1;
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --border-color: #94a3b8;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
        }}

        .header {{
            background: var(--bg-secondary);
            padding: 1rem 2rem;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .logo {{
            font-size: 2rem;
            font-weight: bold;
        }}

        .logo .see {{
            color: var(--pink);
        }}

        .logo .saw {{
            color: var(--blue);
        }}

        .tagline {{
            color: var(--text-secondary);
            font-size: 0.875rem;
        }}

        .header-right {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}

        .updated {{
            color: var(--text-secondary);
            font-size: 0.75rem;
        }}

        .theme-toggle {{
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            cursor: pointer;
        }}

        .filter-bar {{
            background: var(--bg-secondary);
            padding: 0.75rem 2rem;
            border-bottom: 1px solid var(--border-color);
            position: sticky;
            top: 0;
            z-index: 100;
            display: flex;
            gap: 1rem;
            align-items: center;
        }}

        .filter-bar input {{
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            width: 200px;
        }}

        .filter-bar select {{
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
        }}

        .table-container {{
            overflow-x: auto;
            padding: 1rem;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.875rem;
        }}

        thead {{
            position: sticky;
            top: 52px;
            z-index: 99;
        }}

        th {{
            background: var(--bg-tertiary);
            padding: 0.75rem 0.5rem;
            text-align: left;
            font-weight: 600;
            color: var(--text-secondary);
            border-bottom: 2px solid var(--border-color);
            white-space: nowrap;
        }}

        td {{
            padding: 0.75rem 0.5rem;
            border-bottom: 1px solid var(--border-color);
        }}

        .stock-row:hover {{
            background: var(--bg-secondary);
        }}

        .stock-logo {{
            width: 24px;
            height: 24px;
            border-radius: 4px;
        }}

        .logo-cell {{
            width: 40px;
        }}

        .ticker-cell {{
            font-weight: 600;
            color: var(--blue);
        }}

        .name-cell {{
            color: var(--text-secondary);
            max-width: 150px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}

        .positive {{
            color: #22c55e;
        }}

        .negative {{
            color: #ef4444;
        }}

        .score-cell {{
            text-align: center;
            font-weight: 600;
            color: #000;
            border-radius: 4px;
            width: 36px;
        }}

        .state-cell {{
            font-weight: 600;
            font-size: 0.75rem;
        }}

        .menu-btn {{
            background: none;
            border: none;
            color: var(--text-secondary);
            cursor: pointer;
            font-size: 1.25rem;
            padding: 0.25rem;
        }}

        .menu-btn:hover {{
            color: var(--text-primary);
        }}

        .audit-btn {{
            background: none;
            border: none;
            color: var(--text-secondary);
            cursor: pointer;
            font-size: 1rem;
            padding: 0.25rem;
            margin-right: 0.25rem;
        }}

        .audit-btn:hover {{
            color: #3b82f6;
        }}

        .audit-row td {{
            background: var(--bg-tertiary);
            padding: 1rem;
        }}

        .audit-panel {{
            padding: 1rem;
        }}

        .audit-panel h3 {{
            margin-bottom: 1rem;
            color: var(--text-primary);
        }}

        .audit-warning {{
            background: #fef3c7;
            color: #92400e;
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            margin-bottom: 0.5rem;
            font-size: 0.875rem;
        }}

        [data-theme="dark"] .audit-warning {{
            background: #78350f;
            color: #fef3c7;
        }}

        .audit-grid {{
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 1rem;
            margin-top: 1rem;
        }}

        .audit-card {{
            background: var(--bg-secondary);
            border-radius: 0.5rem;
            overflow: hidden;
        }}

        .audit-header {{
            padding: 0.5rem;
            text-align: center;
            font-weight: bold;
            color: #000;
        }}

        .audit-body {{
            padding: 0.75rem;
            font-size: 0.75rem;
            color: var(--text-secondary);
        }}

        .audit-body div {{
            margin-bottom: 0.25rem;
        }}

        .audit-body strong {{
            color: var(--text-primary);
        }}

        @media (max-width: 1400px) {{
            .audit-grid {{
                grid-template-columns: repeat(3, 1fr);
            }}
        }}

        @media (max-width: 900px) {{
            .audit-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}

        .details-row td {{
            background: var(--bg-secondary);
            padding: 1rem;
        }}

        .details-content {{
            display: grid;
            grid-template-columns: 1fr 2fr 1fr;
            gap: 2rem;
            align-items: start;
        }}

        .mfses-scores {{
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }}

        .score-bar {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .score-label {{
            width: 80px;
            font-size: 0.75rem;
            color: var(--text-secondary);
        }}

        .bar-container {{
            flex: 1;
            height: 12px;
            background: var(--bg-tertiary);
            border-radius: 6px;
            overflow: hidden;
        }}

        .bar {{
            height: 100%;
            border-radius: 6px;
            transition: width 0.3s ease;
        }}

        .score-value {{
            width: 30px;
            text-align: right;
            font-weight: 600;
        }}

        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
        }}

        .metric {{
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }}

        .metric-label {{
            font-size: 0.75rem;
            color: var(--text-secondary);
        }}

        .metric-value {{
            font-weight: 600;
        }}

        .links {{
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }}

        .link-btn {{
            background: var(--bg-tertiary);
            color: var(--text-primary);
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            text-decoration: none;
            text-align: center;
            font-size: 0.75rem;
        }}

        .link-btn:hover {{
            background: var(--border-color);
        }}

        @media (max-width: 1200px) {{
            .details-content {{
                grid-template-columns: 1fr;
            }}

            .metrics-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
    </style>
</head>
<body>
    <header class="header">
        <div>
            <div class="logo"><span class="see">SEE</span><span class="saw">SAW!!</span></div>
            <div class="tagline">Financial Freedom</div>
        </div>
        <div class="header-right">
            <span class="updated">Updated: {timestamp}</span>
            <button class="theme-toggle" onclick="toggleTheme()">Toggle Theme</button>
        </div>
    </header>

    <div class="filter-bar">
        <input type="text" id="search" placeholder="Search ticker..." onkeyup="filterTable()">
        <select id="sort" onchange="sortTable()">
            <option value="">Sort by...</option>
            <option value="ticker">Ticker</option>
            <option value="price">Price</option>
            <option value="change_pct">% Change</option>
            <option value="market_cap">Market Cap</option>
            <option value="short_score">Short Score</option>
            <option value="mid_score">Mid Score</option>
            <option value="long_score">Long Score</option>
        </select>
        <select id="state-filter" onchange="filterTable()">
            <option value="">All States</option>
            <option value="HOT">HOT</option>
            <option value="WARM">WARM</option>
            <option value="COLD">COLD</option>
            <option value="FROZEN">FROZEN</option>
        </select>
    </div>

    <div class="table-container">
        <table id="stocks-table">
            <thead>
                <tr>
                    <th></th>
                    <th>Ticker</th>
                    <th>Company</th>
                    <th>Price</th>
                    <th>Change</th>
                    <th>%</th>
                    <th>Volume</th>
                    <th>Mkt Cap</th>
                    <th title="Moat Score">M</th>
                    <th title="Growth Score">G</th>
                    <th title="Balance Score">B</th>
                    <th title="Valuation Score">V</th>
                    <th title="Sentiment Score">S</th>
                    <th>State</th>
                    <th></th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
    </div>

    <script>
        const stockData = {json.dumps(stocks)};

        function toggleTheme() {{
            const body = document.body;
            const currentTheme = body.getAttribute('data-theme');
            body.setAttribute('data-theme', currentTheme === 'light' ? 'dark' : 'light');
            localStorage.setItem('theme', body.getAttribute('data-theme'));
        }}

        // Load saved theme
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {{
            document.body.setAttribute('data-theme', savedTheme);
        }}

        function toggleDetails(ticker) {{
            const row = document.getElementById('details-' + ticker);
            row.style.display = row.style.display === 'none' ? 'table-row' : 'none';
            // Hide audit when showing details
            document.getElementById('audit-' + ticker).style.display = 'none';
        }}

        function toggleAudit(ticker) {{
            const row = document.getElementById('audit-' + ticker);
            row.style.display = row.style.display === 'none' ? 'table-row' : 'none';
            // Hide details when showing audit
            document.getElementById('details-' + ticker).style.display = 'none';
        }}

        function filterTable() {{
            const search = document.getElementById('search').value.toUpperCase();
            const stateFilter = document.getElementById('state-filter').value;
            const rows = document.querySelectorAll('.stock-row');

            rows.forEach(row => {{
                const ticker = row.getAttribute('data-ticker');
                const stock = stockData.find(s => s.ticker === ticker);
                const matchesSearch = ticker.includes(search) || stock.name.toUpperCase().includes(search);
                const matchesState = !stateFilter || stock.state === stateFilter;

                row.style.display = matchesSearch && matchesState ? '' : 'none';
                document.getElementById('details-' + ticker).style.display = 'none';
                document.getElementById('audit-' + ticker).style.display = 'none';
            }});
        }}

        function sortTable() {{
            const sortBy = document.getElementById('sort').value;
            if (!sortBy) return;

            const tbody = document.querySelector('#stocks-table tbody');
            const rows = Array.from(tbody.querySelectorAll('.stock-row'));

            rows.sort((a, b) => {{
                const tickerA = a.getAttribute('data-ticker');
                const tickerB = b.getAttribute('data-ticker');
                const stockA = stockData.find(s => s.ticker === tickerA);
                const stockB = stockData.find(s => s.ticker === tickerB);

                if (sortBy === 'ticker') return tickerA.localeCompare(tickerB);
                return (stockB[sortBy] || 0) - (stockA[sortBy] || 0);
            }});

            rows.forEach(row => {{
                const ticker = row.getAttribute('data-ticker');
                const detailsRow = document.getElementById('details-' + ticker);
                const auditRow = document.getElementById('audit-' + ticker);
                tbody.appendChild(row);
                tbody.appendChild(detailsRow);
                tbody.appendChild(auditRow);
            }});
        }}
    </script>
</body>
</html>'''

    return html


def main():
    """Main execution"""
    print("=" * 60)
    print("SEESAW MFSES v5.0 - Stock Analysis Engine")
    print("=" * 60)

    stocks = []

    for ticker in TICKERS:
        stock = process_ticker(ticker)
        if stock:
            stocks.append(stock)
            print(f"  {ticker}: Price=${stock['price']}, M={stock['moat']}, G={stock['growth']}, B={stock['balance']}, V={stock['valuation']}, S={stock['sentiment']}")

    # Sort by mid-term score (default)
    stocks.sort(key=lambda x: x["mid_score"], reverse=True)

    # Generate timestamp
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Save data
    os.makedirs("docs", exist_ok=True)

    # Save JSON
    with open("docs/data.json", "w") as f:
        json.dump({
            "updated": timestamp,
            "stocks": stocks
        }, f, indent=2)
    print(f"\nSaved data.json")

    # Save HTML
    html = generate_html(stocks, timestamp)
    with open("docs/index.html", "w") as f:
        f.write(html)
    print(f"Saved index.html")

    print("\n" + "=" * 60)
    print("Processing complete!")
    print(f"Processed {len(stocks)} stocks")
    print("=" * 60)


if __name__ == "__main__":
    main()
