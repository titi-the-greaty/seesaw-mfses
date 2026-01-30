#!/usr/bin/env python3
"""
SEESAW MFSES v5.1 - Stock Analysis Engine
Moat, Fundamentals, Sentiment, Expectations, Safety scoring system
500 tickers across all sectors, prioritized by market cap.
"""

import json
import os
import sys
import requests
from datetime import datetime, timezone
from typing import Dict, List, Optional

POLYGON_API_KEY = os.environ.get("POLYGON_API_KEY", "")
BASE_URL = "https://api.polygon.io"

# ---------------------------------------------------------------------------
# 500 TICKERS BY SECTOR  (ordered roughly by market cap within each sector)
# ---------------------------------------------------------------------------
SECTORS: Dict[str, List[str]] = {
    "Technology": [
        "AAPL","MSFT","GOOGL","AMZN","NVDA","META","TSLA","AMD","INTC","CRM",
        "ORCL","ADBE","CSCO","AVGO","QCOM","TXN","IBM","NOW","INTU","AMAT",
        "MU","LRCX","KLAC","SNPS","CDNS","MRVL","FTNT","PANW","CRWD","ZS",
        "NET","DDOG","SNOW","MDB","PLTR","UBER","ABNB","SQ","PYPL","SHOP",
        "WDAY","TEAM","HUBS","DOCU","ZM","OKTA","BILL","MNDY","ESTC","TTD",
        "DASH","PINS","SNAP","ROKU","U","FIVN","TWLO","CFLT","PATH","S",
        "SMCI","ARM","DELL","HPQ","HPE","WDC","STX","KEYS","ANSS","PTC",
        "FICO","GDDY","GEN","AKAM","JNPR","FFIV","NTAP","ON","SWKS","MCHP",
        "NXPI","ADI","MPWR","TER","ENTG","WOLF","ALGM","RMBS","CRUS","SYNA",
        "MTSI","AMBA","ACLS","OLED","LSCC","SITM","POWI","DIOD","INDI","FORM",
    ],
    "Healthcare": [
        "JNJ","UNH","LLY","PFE","MRK","ABBV","TMO","ABT","DHR","BMY",
        "AMGN","GILD","CVS","CI","VRTX","REGN","ISRG","MDT","SYK","BDX",
        "ZTS","BSX","EW","DXCM","IDXX","IQV","A","BAX","MTD","WAT",
        "HOLX","ALGN","PODD","ILMN","NTRA","TFX","HSIC","XRAY","OGN","VTRS",
        "CNC","HCA","MOH","HUM","ELV","GEHC","RMD","COO","TFX","TECH",
    ],
    "Financial": [
        "JPM","V","MA","BAC","WFC","GS","MS","AXP","BLK","SCHW",
        "C","USB","PNC","TFC","COF","SPGI","MCO","ICE","CME","AON",
        "MMC","CB","MET","AIG","PRU","AFL","TRV","ALL","PGR","CINF",
        "RE","WRB","RJF","NTRS","STT","BK","FITB","HBAN","RF","KEY",
        "CFG","ZION","FHN","CMA","SIVB","ALLY","DFS","SYF","NDAQ","CBOE",
    ],
    "Consumer Discretionary": [
        "HD","MCD","NKE","SBUX","TGT","LOW","TJX","ROST","ORLY","AZO",
        "CMG","DRI","MAR","HLT","YUM","DPZ","BKNG","EXPE","LVS","WYNN",
        "MGM","RCL","CCL","NCLH","F","GM","APTV","BWA","LEA","RL",
        "PVH","TPR","CPRI","HAS","MAT","POOL","WSM","RH","DECK","LULU",
        "GRMN","BBY","KMX","AN","SAH","GPC","AAP","DG","DLTR","FIVE",
    ],
    "Consumer Staples": [
        "PG","KO","PEP","COST","WMT","PM","MO","MDLZ","CL","KMB",
        "GIS","K","CAG","HSY","SJM","MKC","HRL","TSN","CPB","POST",
        "MNST","STZ","BF.B","TAP","SAM","KDP","EL","CHD","CLX","SPC",
        "COTY","WBA","KR","SYY","ADM","BG","INGR","DAR","USFD","PFGC",
    ],
    "Industrials": [
        "CAT","DE","UNP","UPS","FDX","HON","GE","BA","RTX","LMT",
        "NOC","GD","MMM","EMR","ITW","PH","ROK","ETN","IR","AME",
        "SWK","DOV","FAST","NDSN","XYL","IEX","GNRC","TT","CARR","OTIS",
        "WAB","CSX","NSC","JBHT","CHRW","EXPD","ODFL","SAIA","XPO","LSTR",
        "DAL","UAL","LUV","ALK","JBLU","AAL","SAVE","HA","WM","RSG",
    ],
    "Energy": [
        "XOM","CVX","COP","EOG","SLB","OXY","PSX","VLO","MPC","PXD",
        "DVN","HAL","HES","FANG","OVV","APA","CTRA","MRO","EQT","AR",
        "RRC","SWN","TRGP","WMB","KMI","OKE","LNG","DTM","DINO","PARR",
    ],
    "Utilities": [
        "NEE","DUK","SO","D","AEP","EXC","SRE","XEL","WEC","ED",
        "ES","AWK","DTE","CMS","CNP","NI","PPL","FE","EVRG","ATO",
        "NRG","VST","CEG","PNW","OGE","AES","LNT","POR","BKH","AVA",
    ],
    "Real Estate": [
        "PLD","AMT","CCI","EQIX","SPG","O","WELL","AVB","EQR","DLR",
        "PSA","VICI","SBAC","WY","ARE","MAA","UDR","CPT","REG","KIM",
        "HST","SUI","ELS","PEAK","VTR","OHI","NNN","STAG","CUBE","EXR",
    ],
    "Materials": [
        "LIN","APD","SHW","ECL","FCX","NEM","NUE","STLD","VMC","MLM",
        "CF","MOS","FMC","ALB","CE","EMN","PPG","RPM","AXTA","AVNT",
        "BALL","PKG","IP","WRK","SEE","SON","ATR","OLN","HUN","CC",
    ],
}

# Flatten to ticker -> sector lookup
TICKER_SECTOR = {}
ALL_TICKERS: List[str] = []
for sector, tickers in SECTORS.items():
    for t in tickers:
        TICKER_SECTOR[t] = sector
        ALL_TICKERS.append(t)

# ============================================================================
# SCORING FUNCTIONS  (unchanged from v5.0)
# ============================================================================

def calc_moat(market_cap: float) -> int:
    if market_cap >= 2e12: return 20
    elif market_cap >= 1e12: return 19
    elif market_cap >= 500e9: return 18
    elif market_cap >= 200e9: return 17
    elif market_cap >= 100e9: return 16
    elif market_cap >= 50e9: return 14
    elif market_cap >= 20e9: return 12
    elif market_cap >= 10e9: return 10
    elif market_cap >= 5e9: return 8
    elif market_cap >= 1e9: return 6
    else: return 4


def calc_growth(eps_growth: float) -> int:
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
    if debt_equity is None or debt_equity < 0:
        return 10
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
    if eps <= 0 or price <= 0:
        return 10
    g = min(15, max(0, eps_growth))
    graham_value = eps * (8.5 + 2 * g)
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
    score = 8
    if div_yield >= 4: score += 5
    elif div_yield >= 3: score += 4
    elif div_yield >= 2: score += 3
    elif div_yield >= 1: score += 2
    elif div_yield > 0: score += 1
    tech_kw = ["COMPUTER","SOFTWARE","SEMICONDUCTOR","ELECTRONIC","TECH"]
    if any(kw in sector.upper() for kw in tech_kw):
        score += 2
    if eps_growth >= 25: score += 3
    elif eps_growth >= 15: score += 2
    elif eps_growth >= 5: score += 1
    return min(20, max(1, score))


def calc_mfses(m, g, b, v, s):
    short = g*0.30 + s*0.25 + v*0.20 + m*0.15 + b*0.10
    mid   = m*0.25 + v*0.25 + g*0.20 + b*0.15 + s*0.15
    lng   = m*0.30 + b*0.25 + v*0.20 + g*0.15 + s*0.10
    return round(short, 1), round(mid, 1), round(lng, 1)


def graham_value(eps, eps_growth):
    if eps <= 0: return 0
    g = min(15, max(0, eps_growth))
    return eps * (8.5 + 2 * g)


# ============================================================================
# API
# ============================================================================

_request_count = 0

def api_get(endpoint, params=None):
    global _request_count
    if not POLYGON_API_KEY:
        return None
    if params is None:
        params = {}
    params["apiKey"] = POLYGON_API_KEY
    try:
        r = requests.get(f"{BASE_URL}{endpoint}", params=params, timeout=30)
        _request_count += 1
        if r.status_code == 429:
            print(f"  Rate limited at request #{_request_count}")
            return None
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        return None


def fetch_price(ticker):
    d = api_get(f"/v2/aggs/ticker/{ticker}/prev")
    if d and d.get("results"):
        r = d["results"][0]
        c = r.get("c", 0)
        o = r.get("o", 0)
        ch = c - o
        pct = (ch / o * 100) if o else 0
        return {"price": c, "change": ch, "change_pct": pct, "volume": r.get("v", 0)}
    return {"price": 0, "change": 0, "change_pct": 0, "volume": 0}


def fetch_details(ticker):
    d = api_get(f"/v3/reference/tickers/{ticker}")
    if d and d.get("results"):
        r = d["results"]
        return {
            "name": r.get("name", ticker),
            "market_cap": r.get("market_cap", 0) or 0,
            "sic_desc": r.get("sic_description", "Unknown"),
            "shares": r.get("share_class_shares_outstanding", 0)
                      or r.get("weighted_shares_outstanding", 0) or 0,
            "logo": r.get("branding", {}).get("icon_url", ""),
        }
    return {"name": ticker, "market_cap": 0, "sic_desc": "Unknown", "shares": 0, "logo": ""}


def fetch_financials(ticker, shares):
    d = api_get("/vX/reference/financials", {
        "ticker": ticker, "limit": 5,
        "timeframe": "quarterly", "sort": "filing_date", "order": "desc"
    })
    out = {"eps": 0, "eps_growth": 0, "debt_equity": None,
           "total_debt": 0, "total_equity": 0, "net_income": 0}
    if not d or not d.get("results"):
        return out
    fins = d["results"]
    latest = fins[0].get("financials", {})
    inc = latest.get("income_statement", {})
    ni = inc.get("net_income_loss", {}).get("value", 0) or 0
    eps = 0
    if shares > 0 and ni != 0:
        eps = (ni * 4) / shares

    bs = latest.get("balance_sheet", {})
    lt_debt = bs.get("long_term_debt", {}).get("value", 0) or 0
    ct_debt = bs.get("current_debt", {}).get("value", 0) or 0
    nc_liab = bs.get("noncurrent_liabilities", {}).get("value", 0) or 0
    liab_total = bs.get("liabilities", {}).get("value", 0) or 0
    total_debt = lt_debt + ct_debt
    if total_debt == 0 and nc_liab > 0:
        total_debt = min(nc_liab, liab_total * 0.5)
    equity = bs.get("equity", {}).get("value", 0) or 0
    if equity == 0:
        equity = bs.get("stockholders_equity", {}).get("value", 0) or 0
    de = (total_debt / equity) if equity > 0 else None

    out.update({"eps": eps, "debt_equity": de, "total_debt": total_debt,
                "total_equity": equity, "net_income": ni})

    # EPS growth – match same fiscal period year-over-year
    cur_period = fins[0].get("fiscal_period", "")
    cur_year = int(fins[0].get("fiscal_year", 0) or 0)
    yag = None
    for f in fins:
        if f.get("fiscal_period") == cur_period and int(f.get("fiscal_year", 0) or 0) == cur_year - 1:
            yag = f
            break
    if yag:
        yag_ni = yag.get("financials", {}).get("income_statement", {}).get(
            "net_income_loss", {}).get("value", 0) or 0
        if shares > 0 and yag_ni != 0:
            yag_eps = (yag_ni * 4) / shares
            if yag_eps != 0:
                out["eps_growth"] = ((eps - yag_eps) / abs(yag_eps)) * 100
    return out


def fetch_dividends(ticker, price):
    d = api_get("/v3/reference/dividends", {"ticker": ticker, "limit": 4, "order": "desc"})
    ann = 0
    if d and d.get("results"):
        ann = sum(x.get("cash_amount", 0) for x in d["results"])
    yld = (ann / price * 100) if price > 0 else 0
    return {"annual_div": ann, "div_yield": yld}


# ============================================================================
# BUILD AUDIT
# ============================================================================

def build_audit(ticker, market_cap, eps_growth, de, eps, price, div_yield, sic, scores):
    m, g, b, v, s = scores
    warnings = []
    if de is not None and de == 0:
        warnings.append("D/E is exactly 0 - data may be missing")
    if de is None:
        warnings.append("D/E ratio unavailable")
    if eps == 0 and market_cap > 50e9:
        warnings.append("EPS is 0 for large-cap stock")
    if market_cap == 0:
        warnings.append("Market cap missing")

    # Sentiment breakdown
    sd = 5 if div_yield>=4 else (4 if div_yield>=3 else (3 if div_yield>=2 else (2 if div_yield>=1 else (1 if div_yield>0 else 0))))
    tk = ["COMPUTER","SOFTWARE","SEMICONDUCTOR","ELECTRONIC","TECH"]
    st = 2 if any(k in sic.upper() for k in tk) else 0
    sg = 3 if eps_growth>=25 else (2 if eps_growth>=15 else (1 if eps_growth>=5 else 0))

    g_capped = min(15, max(0, eps_growth))
    gv = eps * (8.5 + 2 * g_capped) if eps > 0 else 0
    up = ((gv - price) / price * 100) if price > 0 and gv > 0 else 0

    return {
        "moat": {"input": f"${market_cap/1e9:.1f}B", "score": m},
        "growth": {"input": f"{eps_growth:.1f}%", "score": g},
        "balance": {"input": f"{de:.2f}" if de is not None else "N/A", "score": b},
        "valuation": {"graham": round(gv, 2), "upside": round(up, 1), "score": v},
        "sentiment": {"breakdown": f"8+{sd}+{st}+{sg}={8+sd+st+sg}", "score": s},
        "warnings": warnings,
    }


# ============================================================================
# PROCESS ONE TICKER
# ============================================================================

def process(ticker):
    pr = fetch_price(ticker)
    det = fetch_details(ticker)
    fin = fetch_financials(ticker, det["shares"])
    div = fetch_dividends(ticker, pr["price"])

    sector = TICKER_SECTOR.get(ticker, "Unknown")
    mc = det["market_cap"]
    eg = fin["eps_growth"]
    de = fin["debt_equity"]
    ep = fin["eps"]
    dy = div["div_yield"]
    sic = det["sic_desc"]

    m = calc_moat(mc)
    g = calc_growth(eg)
    b = calc_balance(de)
    v = calc_valuation(ep, pr["price"], eg)
    s = calc_sentiment(dy, sic, eg)
    sh, mi, lo = calc_mfses(m, g, b, v, s)
    gv = graham_value(ep, eg)
    up = ((gv - pr["price"]) / pr["price"] * 100) if pr["price"] > 0 else 0

    audit = build_audit(ticker, mc, eg, de, ep, pr["price"], dy, sic, (m, g, b, v, s))

    return {
        "ticker": ticker,
        "name": det["name"],
        "sector": sector,
        "sic_desc": sic,
        "price": round(pr["price"], 2),
        "change": round(pr["change"], 2),
        "change_pct": round(pr["change_pct"], 2),
        "volume": int(pr["volume"]),
        "market_cap": mc,
        "logo": det["logo"],
        "eps": round(ep, 2),
        "eps_growth": round(eg, 1),
        "debt_equity": round(de, 2) if de is not None else None,
        "dividend_yield": round(dy, 2),
        "total_debt": fin["total_debt"],
        "total_equity": fin["total_equity"],
        "graham_value": round(gv, 2),
        "upside": round(up, 1),
        "moat": m, "growth": g, "balance": b, "valuation": v, "sentiment": s,
        "short_score": sh, "mid_score": mi, "long_score": lo,
        "audit": audit,
    }


# ============================================================================
# HTML GENERATION  (complete rewrite for v5.1)
# ============================================================================

def gen_html(stocks, timestamp):
    stocks_json = json.dumps(stocks)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SEESAW MFSES</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Sora:ital,wght@1,800&display=swap" rel="stylesheet">
<style>
:root {{
  --bg:#0f172a; --bg2:#1e293b; --bg3:#334155; --card:#1e293b;
  --text:#f8fafc; --text2:#94a3b8; --border:#475569;
  --pos:#22c55e; --neg:#ef4444; --pink:#DB1478; --blue:#2A84C7;
}}
[data-theme="light"] {{
  --bg:#f8fafc; --bg2:#e2e8f0; --bg3:#cbd5e1; --card:#ffffff;
  --text:#0f172a; --text2:#475569; --border:#94a3b8;
}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--text);font-size:13px}}

/* HEADER */
.header{{background:var(--bg2);padding:10px 20px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--border)}}
.logo-text{{font-family:'Sora',sans-serif;font-style:italic;font-size:24px;font-weight:800;letter-spacing:-1px}}
.logo-text .see{{color:var(--pink)}} .logo-text .saw{{color:var(--blue)}}
.tagline{{font-size:10px;color:var(--text2);margin-top:2px}}
.header-right{{display:flex;align-items:center;gap:12px}}
.updated{{font-size:10px;color:var(--text2)}}
.theme-btn{{background:var(--bg3);border:1px solid var(--border);color:var(--text);padding:5px 10px;border-radius:6px;cursor:pointer;font-size:11px}}

/* CONTROLS */
.controls{{position:sticky;top:0;z-index:100;background:var(--bg);padding:8px 20px;border-bottom:1px solid var(--border);display:flex;gap:8px;align-items:center;flex-wrap:wrap}}
.search-box input{{background:var(--bg3);border:1px solid var(--border);color:var(--text);padding:6px 12px;border-radius:6px;font-size:12px;width:180px}}
.dropdown{{position:relative;display:inline-block}}
.dropdown-btn{{background:var(--bg3);border:1px solid var(--border);color:var(--text);padding:6px 12px;border-radius:6px;cursor:pointer;font-size:12px;white-space:nowrap}}
.dropdown-content{{display:none;position:absolute;top:100%;left:0;background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:8px;min-width:180px;z-index:200;max-height:320px;overflow-y:auto;box-shadow:0 8px 24px rgba(0,0,0,.3)}}
.dropdown-content.show{{display:block}}
.dropdown-content label{{display:block;padding:4px 8px;font-size:12px;cursor:pointer;border-radius:4px;white-space:nowrap}}
.dropdown-content label:hover{{background:var(--bg3)}}
.dropdown-content label input{{margin-right:6px}}
.dropdown-actions{{display:flex;gap:6px;padding:6px 4px 2px;border-top:1px solid var(--border);margin-top:4px}}
.dropdown-actions button{{flex:1;padding:4px;font-size:11px;background:var(--bg3);border:1px solid var(--border);color:var(--text);border-radius:4px;cursor:pointer}}
.sort-btn{{display:block;width:100%;text-align:left;padding:6px 10px;font-size:12px;background:none;border:none;color:var(--text);cursor:pointer;border-radius:4px}}
.sort-btn:hover,.sort-btn.active{{background:var(--bg3)}}
.sort-btn.active{{color:var(--blue);font-weight:600}}

/* STATS BAR */
.stats-bar{{display:flex;gap:20px;margin-left:auto;font-size:11px;color:var(--text2)}}
.stat-val{{font-weight:700;color:var(--text);margin-right:3px}}

/* TABLE */
.table-wrap{{padding:0 10px 80px}}
table{{width:100%;border-collapse:collapse;font-size:12px;table-layout:fixed}}
thead{{position:sticky;top:42px;z-index:90}}
th{{background:var(--bg2);color:var(--text2);padding:6px 4px;text-align:left;font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.3px;border-bottom:2px solid var(--border);white-space:nowrap;overflow:hidden}}
td{{padding:6px 4px;border-bottom:1px solid var(--border);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.stock-row:hover{{background:var(--bg2)}}

/* column widths */
.col-logo{{width:28px}} .col-tick{{width:54px}} .col-name{{width:140px}}
.col-price{{width:65px}} .col-chg{{width:55px}} .col-pct{{width:55px}}
.col-vol{{width:60px}} .col-cap{{width:72px}}
.col-sc{{width:32px;text-align:center}} .col-up{{width:55px}} .col-act{{width:50px}}

/* elements */
.stock-logo{{width:20px;height:20px;border-radius:3px;vertical-align:middle}}
.ticker{{font-weight:700;color:var(--blue);font-size:12px}}
.name-cell{{color:var(--text2);font-size:11px}}
.pos{{color:var(--pos)}} .neg{{color:var(--neg)}}
.score-cell{{display:inline-block;padding:3px 0;border:1px solid var(--border);border-radius:5px;background:var(--card);font-weight:600;font-size:11px;text-align:center;width:28px}}
.upside-cell{{font-weight:600;font-size:12px}}
.act-btns{{display:flex;gap:2px}}
.act-btn{{background:none;border:none;color:var(--text2);cursor:pointer;font-size:13px;padding:2px 4px}}
.act-btn:hover{{color:var(--text)}}

/* detail / audit rows */
.detail-row td,.audit-row td{{background:var(--bg2);padding:12px 16px}}
.detail-content{{display:grid;grid-template-columns:1fr 2fr 1fr;gap:20px}}
.score-bar-wrap{{display:flex;flex-direction:column;gap:6px}}
.sb{{display:flex;align-items:center;gap:6px}}
.sb-label{{width:65px;font-size:11px;color:var(--text2)}}
.sb-track{{flex:1;height:10px;background:var(--bg3);border-radius:5px;overflow:hidden}}
.sb-fill{{height:100%;border-radius:5px}}
.sb-val{{width:28px;text-align:right;font-weight:600;font-size:11px}}
.metrics{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}}
.metric-label{{font-size:10px;color:var(--text2)}} .metric-val{{font-weight:600;font-size:12px}}
.links a{{display:inline-block;background:var(--bg3);color:var(--text);padding:5px 10px;border-radius:5px;text-decoration:none;font-size:11px;margin:2px}}

/* audit */
.audit-panel h3{{margin-bottom:10px;font-size:14px}}
.audit-warn{{background:#78350f;color:#fef3c7;padding:4px 10px;border-radius:5px;margin-bottom:4px;font-size:12px}}
[data-theme="light"] .audit-warn{{background:#fef3c7;color:#92400e}}
.audit-grid{{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin-top:8px}}
.audit-card{{background:var(--bg);border-radius:6px;overflow:hidden}}
.audit-hdr{{padding:4px 6px;text-align:center;font-weight:700;font-size:12px;color:#000;background:var(--bg3)}}
.audit-body{{padding:8px;font-size:11px;color:var(--text2)}}
.audit-body strong{{color:var(--text)}}

/* loading */
.loading-more{{text-align:center;padding:20px;color:var(--text2);font-size:12px}}

@media(max-width:1200px){{
  .col-name{{width:100px}}.col-vol{{display:none}}
  .detail-content{{grid-template-columns:1fr}}
  .audit-grid{{grid-template-columns:repeat(3,1fr)}}
}}
@media(max-width:800px){{
  .col-cap{{display:none}}.col-chg{{display:none}}
  .audit-grid{{grid-template-columns:repeat(2,1fr)}}
}}
</style>
</head>
<body>

<header class="header">
  <div>
    <div class="logo-text"><span class="see">SEE</span><span class="saw">SAW!!</span></div>
    <div class="tagline">Financial Freedom</div>
  </div>
  <div class="header-right">
    <span class="updated">Updated: {timestamp}</span>
    <button class="theme-btn" onclick="toggleTheme()">Theme</button>
  </div>
</header>

<div class="controls" id="controls">
  <div class="search-box"><input type="text" id="search" placeholder="Search ticker..." oninput="applyFilters()"></div>

  <div class="dropdown">
    <button class="dropdown-btn" onclick="togDd('sectorDd')">Sectors &#9660;</button>
    <div class="dropdown-content" id="sectorDd"></div>
  </div>

  <div class="dropdown">
    <button class="dropdown-btn" id="sortLabel" onclick="togDd('sortDd')">Sort: Mid &#9660;</button>
    <div class="dropdown-content" id="sortDd">
      <button class="sort-btn" onclick="doSort('short_score')">MFSES Short</button>
      <button class="sort-btn active" onclick="doSort('mid_score')">MFSES Mid</button>
      <button class="sort-btn" onclick="doSort('long_score')">MFSES Long</button>
      <hr style="border-color:var(--border);margin:4px 0">
      <button class="sort-btn" onclick="doSort('moat')">Moat</button>
      <button class="sort-btn" onclick="doSort('growth')">Growth</button>
      <button class="sort-btn" onclick="doSort('balance')">Balance</button>
      <button class="sort-btn" onclick="doSort('valuation')">Valuation</button>
      <button class="sort-btn" onclick="doSort('sentiment')">Sentiment</button>
      <hr style="border-color:var(--border);margin:4px 0">
      <button class="sort-btn" onclick="doSort('price')">Price</button>
      <button class="sort-btn" onclick="doSort('change_pct')">Change %</button>
      <button class="sort-btn" onclick="doSort('market_cap')">Market Cap</button>
      <button class="sort-btn" onclick="doSort('upside')">Upside %</button>
      <button class="sort-btn" onclick="doSort('ticker')">Ticker A-Z</button>
    </div>
  </div>

  <div class="stats-bar">
    <div><span class="stat-val" id="totalCount">0</span>Stocks</div>
    <div><span class="stat-val" id="showCount">0</span>Showing</div>
    <div><span class="stat-val" id="avgUpside">0%</span>Avg Upside</div>
  </div>
</div>

<div class="table-wrap">
  <table>
    <thead>
      <tr>
        <th class="col-logo"></th>
        <th class="col-tick">Ticker</th>
        <th class="col-name">Company</th>
        <th class="col-price">Price</th>
        <th class="col-chg">Chg</th>
        <th class="col-pct">%</th>
        <th class="col-vol">Volume</th>
        <th class="col-cap">Mkt Cap</th>
        <th class="col-sc" title="Moat">M</th>
        <th class="col-sc" title="Growth">G</th>
        <th class="col-sc" title="Balance">B</th>
        <th class="col-sc" title="Valuation">V</th>
        <th class="col-sc" title="Sentiment">S</th>
        <th class="col-up">Upside</th>
        <th class="col-act"></th>
      </tr>
    </thead>
    <tbody id="tbody"></tbody>
  </table>
  <div class="loading-more" id="loadingMore" style="display:none">Loading more...</div>
</div>

<script>
const ALL = {stocks_json};
const API_KEY = "{POLYGON_API_KEY}";
let filtered = [...ALL];
let displayed = 0;
const BATCH = 50;
let currentSort = "mid_score";
let sortAsc = false;
let openDetail = null;
let openAudit = null;

// --- INIT ---
function init() {{
  buildSectorDd();
  applyFilters();
  const t = localStorage.getItem('theme');
  if (t) document.body.setAttribute('data-theme', t);
}}

// --- THEME ---
function toggleTheme() {{
  const b = document.body;
  const nxt = b.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
  b.setAttribute('data-theme', nxt);
  localStorage.setItem('theme', nxt);
}}

// --- DROPDOWNS ---
function togDd(id) {{
  document.querySelectorAll('.dropdown-content').forEach(d => {{
    if (d.id !== id) d.classList.remove('show');
  }});
  document.getElementById(id).classList.toggle('show');
}}
document.addEventListener('click', e => {{
  if (!e.target.closest('.dropdown')) {{
    document.querySelectorAll('.dropdown-content').forEach(d => d.classList.remove('show'));
  }}
}});

// --- SECTOR DROPDOWN ---
const SECTORS = [...new Set(ALL.map(s => s.sector))].sort();
function buildSectorDd() {{
  const el = document.getElementById('sectorDd');
  let h = SECTORS.map(s => `<label><input type="checkbox" value="${{s}}" checked onchange="applyFilters()"> ${{s}}</label>`).join('');
  h += `<div class="dropdown-actions"><button onclick="chkAll(true)">All</button><button onclick="chkAll(false)">None</button></div>`;
  el.innerHTML = h;
}}
function chkAll(v) {{
  document.querySelectorAll('#sectorDd input').forEach(i => i.checked = v);
  applyFilters();
}}

// --- SORTING ---
function doSort(key) {{
  if (currentSort === key) sortAsc = !sortAsc;
  else {{ currentSort = key; sortAsc = key === 'ticker'; }}
  document.querySelectorAll('.sort-btn').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
  const labels = {{short_score:'Short',mid_score:'Mid',long_score:'Long',moat:'Moat',growth:'Growth',balance:'Balance',valuation:'Valuation',sentiment:'Sentiment',price:'Price',change_pct:'Chg%',market_cap:'Cap',upside:'Upside',ticker:'A-Z'}};
  document.getElementById('sortLabel').textContent = 'Sort: ' + (labels[key]||key) + ' \\u25BC';
  applyFilters();
}}

// --- FILTER + RENDER ---
function applyFilters() {{
  const q = document.getElementById('search').value.toUpperCase();
  const secs = new Set([...document.querySelectorAll('#sectorDd input:checked')].map(i => i.value));
  filtered = ALL.filter(s => {{
    if (q && !s.ticker.includes(q) && !s.name.toUpperCase().includes(q)) return false;
    if (!secs.has(s.sector)) return false;
    return true;
  }});
  // sort
  filtered.sort((a, b) => {{
    let va = a[currentSort], vb = b[currentSort];
    if (currentSort === 'ticker') return sortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
    va = va ?? -999; vb = vb ?? -999;
    return sortAsc ? va - vb : vb - va;
  }});
  displayed = 0;
  openDetail = null;
  openAudit = null;
  document.getElementById('tbody').innerHTML = '';
  loadMore();
  updateStats();
}}

function updateStats() {{
  document.getElementById('totalCount').textContent = filtered.length;
  document.getElementById('showCount').textContent = Math.min(displayed, filtered.length);
  const ups = filtered.filter(s => s.price > 0).map(s => s.upside);
  const avg = ups.length ? (ups.reduce((a,b)=>a+b,0)/ups.length) : 0;
  const el = document.getElementById('avgUpside');
  el.textContent = (avg >= 0 ? '+' : '') + avg.toFixed(1) + '%';
  el.className = 'stat-val ' + (avg >= 0 ? 'pos' : 'neg');
}}

function loadMore() {{
  const end = Math.min(displayed + BATCH, filtered.length);
  const tbody = document.getElementById('tbody');
  for (let i = displayed; i < end; i++) {{
    tbody.appendChild(buildRow(filtered[i]));
  }}
  displayed = end;
  document.getElementById('showCount').textContent = displayed;
  document.getElementById('loadingMore').style.display = displayed < filtered.length ? 'block' : 'none';
}}

// --- INFINITE SCROLL ---
window.addEventListener('scroll', () => {{
  if (displayed < filtered.length && window.innerHeight + window.scrollY >= document.body.offsetHeight - 400) {{
    loadMore();
  }}
}});

// --- BUILD ROW ---
function fmtVol(v) {{ if(v>=1e9)return(v/1e9).toFixed(1)+'B';if(v>=1e6)return(v/1e6).toFixed(1)+'M';if(v>=1e3)return(v/1e3).toFixed(0)+'K';return v; }}
function fmtCap(c) {{ if(c>=1e12)return'$'+(c/1e12).toFixed(2)+'T';if(c>=1e9)return'$'+(c/1e9).toFixed(1)+'B';if(c>=1e6)return'$'+(c/1e6).toFixed(0)+'M';return'$'+c; }}

function buildRow(s) {{
  const tr = document.createElement('tr');
  tr.className = 'stock-row';
  tr.dataset.ticker = s.ticker;
  const cc = s.change >= 0 ? 'pos' : 'neg';
  const sign = s.change >= 0 ? '+' : '';
  const ucc = s.upside >= 0 ? 'pos' : 'neg';
  const usign = s.upside >= 0 ? '+' : '';
  const logo = s.logo ? `<img class="stock-logo" src="${{s.logo}}?apiKey=${{API_KEY}}" onerror="this.style.display='none'" alt="">` : '';

  tr.innerHTML = `
    <td class="col-logo">${{logo}}</td>
    <td class="col-tick"><span class="ticker">${{s.ticker}}</span></td>
    <td class="col-name name-cell" title="${{s.name}}">${{s.name}}</td>
    <td class="col-price">${{s.price > 0 ? '$'+s.price.toFixed(2) : '-'}}</td>
    <td class="col-chg ${{cc}}">${{sign}}${{s.change.toFixed(2)}}</td>
    <td class="col-pct ${{cc}}">${{sign}}${{s.change_pct.toFixed(2)}}%</td>
    <td class="col-vol">${{fmtVol(s.volume)}}</td>
    <td class="col-cap">${{fmtCap(s.market_cap)}}</td>
    <td class="col-sc"><span class="score-cell">${{s.moat}}</span></td>
    <td class="col-sc"><span class="score-cell">${{s.growth}}</span></td>
    <td class="col-sc"><span class="score-cell">${{s.balance}}</span></td>
    <td class="col-sc"><span class="score-cell">${{s.valuation}}</span></td>
    <td class="col-sc"><span class="score-cell">${{s.sentiment}}</span></td>
    <td class="col-up upside-cell ${{ucc}}">${{usign}}${{s.upside.toFixed(1)}}%</td>
    <td class="col-act"><div class="act-btns">
      <button class="act-btn" title="Fact Check" onclick="togAudit('${{s.ticker}}',this)">&#128269;</button>
      <button class="act-btn" title="Details" onclick="togDetail('${{s.ticker}}',this)">&#8942;</button>
    </div></td>`;
  return tr;
}}

// --- DETAIL / AUDIT TOGGLE ---
function scColor(v) {{ if(v>=16)return'#22c55e';if(v>=12)return'#84cc16';if(v>=8)return'#eab308';if(v>=4)return'#f97316';return'#ef4444'; }}

function togDetail(tk, btn) {{
  const existing = document.getElementById('det-'+tk);
  if (existing) {{ existing.remove(); openDetail = null; return; }}
  // close any open
  if (openDetail) {{ const el = document.getElementById('det-'+openDetail); if(el) el.remove(); }}
  if (openAudit) {{ const el = document.getElementById('aud-'+openAudit); if(el) el.remove(); openAudit=null; }}
  openDetail = tk;
  const s = ALL.find(x => x.ticker === tk);
  if (!s) return;
  const row = btn.closest('tr');
  const tr = document.createElement('tr');
  tr.className = 'detail-row';
  tr.id = 'det-'+tk;
  const de = s.debt_equity !== null ? s.debt_equity.toFixed(2) : 'N/A';
  const upc = s.upside >= 0 ? 'pos' : 'neg';
  const ups = s.upside >= 0 ? '+' : '';
  const egc = s.eps_growth >= 0 ? '+' : '';
  tr.innerHTML = `<td colspan="15"><div class="detail-content">
    <div class="score-bar-wrap">
      ${{['Short','Mid','Long'].map((l,i) => {{
        const v = [s.short_score,s.mid_score,s.long_score][i];
        return `<div class="sb"><span class="sb-label">${{l}}:</span><div class="sb-track"><div class="sb-fill" style="width:${{v*5}}%;background:${{scColor(Math.round(v))}}"></div></div><span class="sb-val">${{v}}</span></div>`;
      }}).join('')}}
    </div>
    <div class="metrics">
      <div><div class="metric-label">Graham Value</div><div class="metric-val">${{s.graham_value > 0 ? '$'+s.graham_value.toFixed(2) : '-'}}</div></div>
      <div><div class="metric-label">Upside</div><div class="metric-val ${{upc}}">${{ups}}${{s.upside.toFixed(1)}}%</div></div>
      <div><div class="metric-label">EPS</div><div class="metric-val">${{s.eps !== 0 ? '$'+s.eps.toFixed(2) : '-'}}</div></div>
      <div><div class="metric-label">EPS Growth</div><div class="metric-val">${{egc}}${{s.eps_growth.toFixed(1)}}%</div></div>
      <div><div class="metric-label">Debt/Equity</div><div class="metric-val">${{de}}</div></div>
      <div><div class="metric-label">Div Yield</div><div class="metric-val">${{s.dividend_yield.toFixed(2)}}%</div></div>
    </div>
    <div>
      <a href="https://finance.yahoo.com/quote/${{s.ticker}}" target="_blank" class="links">Yahoo Finance</a>
      <a href="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=${{s.ticker}}&type=10-&dateb=&owner=include&count=40" target="_blank" class="links">SEC Filings</a>
    </div>
  </div></td>`;
  row.after(tr);
}}

function togAudit(tk, btn) {{
  const existing = document.getElementById('aud-'+tk);
  if (existing) {{ existing.remove(); openAudit = null; return; }}
  if (openAudit) {{ const el = document.getElementById('aud-'+openAudit); if(el) el.remove(); }}
  if (openDetail) {{ const el = document.getElementById('det-'+openDetail); if(el) el.remove(); openDetail=null; }}
  openAudit = tk;
  const s = ALL.find(x => x.ticker === tk);
  if (!s || !s.audit) return;
  const a = s.audit;
  const row = btn.closest('tr');
  const tr = document.createElement('tr');
  tr.className = 'audit-row';
  tr.id = 'aud-'+tk;
  const warns = (a.warnings||[]).map(w => `<div class="audit-warn">\\u26A0\\uFE0F ${{w}}</div>`).join('');
  const debt = s.total_debt ? '$'+(s.total_debt/1e9).toFixed(2)+'B' : '$0';
  const eq = s.total_equity ? '$'+(s.total_equity/1e9).toFixed(2)+'B' : '$0';
  tr.innerHTML = `<td colspan="15"><div class="audit-panel">
    <h3>&#128269; Fact Check: ${{s.ticker}}</h3>
    ${{warns}}
    <div class="audit-grid">
      <div class="audit-card"><div class="audit-hdr" style="background:${{scColor(s.moat)}}">M = ${{s.moat}}</div><div class="audit-body"><strong>Cap:</strong> ${{a.moat?.input||'-'}}</div></div>
      <div class="audit-card"><div class="audit-hdr" style="background:${{scColor(s.growth)}}">G = ${{s.growth}}</div><div class="audit-body"><strong>Growth:</strong> ${{a.growth?.input||'-'}}</div></div>
      <div class="audit-card"><div class="audit-hdr" style="background:${{scColor(s.balance)}}">B = ${{s.balance}}</div><div class="audit-body"><strong>D/E:</strong> ${{a.balance?.input||'-'}}<br><strong>Debt:</strong> ${{debt}}<br><strong>Equity:</strong> ${{eq}}</div></div>
      <div class="audit-card"><div class="audit-hdr" style="background:${{scColor(s.valuation)}}">V = ${{s.valuation}}</div><div class="audit-body"><strong>Graham:</strong> $${{a.valuation?.graham||0}}<br><strong>Upside:</strong> ${{a.valuation?.upside||0}}%</div></div>
      <div class="audit-card"><div class="audit-hdr" style="background:${{scColor(s.sentiment)}}">S = ${{s.sentiment}}</div><div class="audit-body"><strong>Calc:</strong> ${{a.sentiment?.breakdown||'-'}}</div></div>
    </div>
  </div></td>`;
  row.after(tr);
}}

init();
</script>
</body>
</html>'''


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 60)
    print("SEESAW MFSES v5.1 - 500 Stock Analysis Engine")
    print("=" * 60)

    stocks = []
    failed = 0
    total = len(ALL_TICKERS)

    for i, ticker in enumerate(ALL_TICKERS):
        pct_done = (i + 1) / total * 100
        if (i + 1) % 25 == 0 or i == 0:
            print(f"[{pct_done:.0f}%] Processing {ticker} ({i+1}/{total})...")

        try:
            s = process(ticker)
            if s and s["price"] > 0 and s["market_cap"] > 0:
                stocks.append(s)
            else:
                failed += 1
        except Exception as e:
            print(f"  ERROR {ticker}: {e}")
            failed += 1

        # If we hit too many failures in a row, the API may be down
        if failed > 50 and len(stocks) == 0:
            print("Too many failures, API may be down.")
            break

    print(f"\nProcessed: {len(stocks)} successful, {failed} failed")

    # Sort by mid-term score
    stocks.sort(key=lambda x: x["mid_score"], reverse=True)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    os.makedirs("docs", exist_ok=True)

    with open("docs/data.json", "w") as f:
        json.dump({"updated": ts, "count": len(stocks), "stocks": stocks}, f)
    print(f"Saved data.json ({len(stocks)} stocks)")

    html = gen_html(stocks, ts)
    with open("docs/index.html", "w") as f:
        f.write(html)
    print("Saved index.html")

    print(f"\nAPI requests made: {_request_count}")
    print("=" * 60)


if __name__ == "__main__":
    main()
