# Crypto Crawler Challenge

## Overview
This project is a two-phase solution for the Crypto Crawler Challenge:

- **Phase 1: Price Pulse**
  - Polls the live Bitcoin price from CoinGecko every second, prints the price and a N-tick Simple Moving Average (SMA), and handles errors robustly.
- **Phase 2: CoinMarketCap Watchlist**
  - Scrapes the top 100 coins from CoinMarketCap using both HTML scraping and the internal JSON API, saving results to CSV or SQLite, and compares performance.

---

## Installation

1. **Clone the repository** (or copy the lvix folder to your workspace).
2. **Install Python 3.10+**
3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Install Playwright browsers** (for HTML scraping):

```bash
python -m playwright install
```

---

## Usage

### Phase 1: Price Pulse

Poll the Bitcoin price every second, print price and SMA (default period 10):

```bash
python start.py --phase 1
```

With custom polling interval, polling amount, and SMA period:

```bash
python start.py --phase 1 --poll_interval 2 --poll_amount 20 --sma_period 5
```
#### Options Explained:
- `--poll_interval` (`-poi`): Polling interval in seconds (default: 1)
- `--poll_amount` (`-poa`): Number of price polls (default: 10)
- `--sma_period` (`-smap`): SMA period (default: 10)
- `--logging_level` (`-l`): Logging level (default: ERROR)

---

### Phase 2: CoinMarketCap Watchlist

#### HTML Scraper (default):
Uses Playwright and BeautifulSoup to extract data from rendered HTML tables.

```bash
python start.py --phase 2 --mode html --save_csv --max_pages 5
```

#### API Scraper:
Fetches structured data directly from CoinMarketCap's internal API.
Much faster and more reliable.

```bash
python start.py --phase 2 --mode api --save_sqlite --max_pages 3
```

#### Performance Comparison:

```bash
python start.py --phase 2 --mode compare --measure_performance
```

#### Options Explained:
- `--mode` (`-m`): `html`, `api`, or `compare` (default: html)
- `--max_pages`: Number of pages to scrape (default: 5)
- `--save_csv`: Save results to CSV file
- `--save_sqlite`: Save results to SQLite database
- `--measure_performance`: Print requests, time, and throughput
- `--logging_level` (`-l`): Logging level (default: ERROR)

---

## Performance Comparison: HTML vs JSON (API)

Here is the results of the performance comparison between HTML scraping and JSON API scraping:

| Metric | HTML Version | JSON/API Version |
| :--- | :--- | :--- |
| **Requests Made** | 5 | 5 |
| **Total Time** | 37.87s | 0.49s |
| **Throughput** | 0.13 req/s | 10.31 req/s |

**Conclusion:** The JSON/API method is overwhelmingly more efficient, proving to be over **77 times faster** than parsing HTML.

---

## File Structure
- `start.py` — Main entry point, CLI for phase selection
- `src/price_pulse.py` — Phase 1: Price polling logic
- `src/coin_market_cap_watchlist.py` — Phase 2: HTML & JSON scrapers
- `src/compare_scrapers.py` — Performance comparison script
- `src/utils.py` — Shared utilities

---

## Bonus features implemented
- Flexible Command-Line Interface (CLI)
- Customizable polling intervals and SMA periods
- Error handling and logging
- Users can set the logging level to DEBUG, INFO, WARNING, ERROR, or CRITICAL for more or less output as needed.
