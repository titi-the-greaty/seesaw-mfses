# SEESAW MFSES v5.0

**Moat, Fundamentals, Sentiment, Expectations, Safety** - A stock analysis scoring system.

## Overview

SEESAW MFSES analyzes 10 tech stocks using 5 key factors:

- **M (Moat)** - Competitive advantage based on market cap
- **G (Growth)** - EPS growth rate
- **B (Balance)** - Financial health via debt/equity ratio
- **V (Valuation)** - Graham formula intrinsic value
- **S (Sentiment)** - Dividends, sector, and momentum

Each factor scores 1-20, combined into Short/Mid/Long term composite scores.

## Stocks Tracked

AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA, AMD, INTC, CRM

## Data Source

All data fetched from [Polygon.io](https://polygon.io) API.

## Setup

1. Clone the repository
2. Add `POLYGON_API_KEY` to GitHub Secrets
3. Enable GitHub Pages from `docs/` folder
4. Data updates automatically every 30 minutes during market hours

## Local Development

```bash
pip install requests
export POLYGON_API_KEY=your_key_here
python mfses_engine.py
```

## License

MIT
