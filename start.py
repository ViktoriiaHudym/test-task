import argparse
import sys

from src import price_pulse, compare_scrapers
from src.coin_market_cap_watchlist import CoinMarketCapHTMLScraper, CoinMarketCapAPIScraper


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--phase', '-p', type=int, required=True, help='Phase of the script')
    parser.add_argument('--logging_level', '-l', type=str, default='ERROR', help='Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)')

    # Phase 1 arguments
    parser.add_argument('--poll_interval', '-poi', type=int, default=1, help='Polling interval in seconds')
    parser.add_argument('--poll_amount', '-poa', type=int, default=10, help='Polling amount')
    parser.add_argument('--sma_period', '-smap', type=int, default=10, help='SMA period')

    # Phase 2 arguments
    parser.add_argument('--mode', '-m', type=str, choices=['html', 'api', 'compare'], default='html', help='Phase 2: html, api, or compare (default: html)')
    parser.add_argument('--max_pages', type=int, default=5, help='Number of pages to scrape (default: 5)')
    parser.add_argument('--save_csv', action='store_true', help='Save results to CSV')
    parser.add_argument('--save_sqlite', action='store_true', help='Save results to SQLite DB')
    parser.add_argument('--measure_performance', action='store_true', help='Measure and print scraper performance (requests, time, throughput)')

    args = parser.parse_args()

    if args.phase == 1:
        price_pulse.run(args)

    elif args.phase == 2:
        if args.mode == 'compare':
            compare_scrapers.main()
        else:
            scraper_class = CoinMarketCapHTMLScraper if args.mode == 'html' else CoinMarketCapAPIScraper
            scraper = scraper_class(
                max_pages=args.max_pages,
                save_csv=args.save_csv,
                save_sqlite=args.save_sqlite,
                measure_performance=args.measure_performance,
                logging_level=args.logging_level
            )
            scraper.run_scraper()
    else:
        print(
            "Invalid phase specified. "
            "Use 1 for 'Phase 1 – Price Pulse' or 2 for 'Phase 2 – CoinMarketCap Watchlist'."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
