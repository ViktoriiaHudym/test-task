from src.coin_market_cap_watchlist import CoinMarketCapHTMLScraper, CoinMarketCapAPIScraper


def run_and_print_scraper(scraper_class, label, **kwargs):
    print(f'\n[{label}]')
    try:
        scraper = scraper_class(**kwargs)
        requests, elapsed = scraper.run_scraper()
        throughput = requests / elapsed if elapsed > 0 else 0
        print(f'Requests: {requests}')
        print(f'Time: {elapsed:.2f}s')
        print(f'Throughput: {throughput:.2f} req/s')
    except Exception as e:
        print(f'{label} scraper failed: {e}')


def main():
    print('--- CoinMarketCap Scraper Comparison ---')
    run_and_print_scraper(CoinMarketCapHTMLScraper, 'HTML Version', max_pages=5, measure_performance=True)
    run_and_print_scraper(CoinMarketCapAPIScraper, 'JSON/API Version', max_pages=5, measure_performance=True)


if __name__ == '__main__':
    main()
