import csv
import sqlite3
import time
import re
import logging
from typing import List
from abc import ABC, abstractmethod

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

from src.utils import get_response_data


class CoinMarketCapScraper(ABC):
    def __init__(self, max_pages: int = 5, save_csv: bool = False, save_sqlite: bool = False,
                 measure_performance: bool = False, logging_level: str = 'ERROR'):
        self.max_pages = int(max_pages)
        self.HEADERS = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'  # noqa
        }

        self.save_csv = save_csv
        self.save_sqlite = save_sqlite

        self.measure_performance = measure_performance
        self.request_count = 0  # For throughput measurement

        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        logging.basicConfig(level=logging_level.upper())

    @abstractmethod
    def get_listing_pages(self) -> list:
        pass

    @abstractmethod
    def scrape_listing_page(self, page: str) -> list:
        pass

    def run_scraper(self):
        self.request_count = 0
        start_time = time.time() if self.measure_performance else None

        logging.info("Starting CoinMarketCapWatchlist Scraper...")
        listing_pages = self.get_listing_pages()

        results = []
        for listing_page in listing_pages:
            listing_results = self.scrape_listing_page(listing_page)
            if not listing_results:
                continue

            results.extend(listing_results)

        if not results:
            logging.info("CoinMarketCapWatchlist Scraper returned no results.")
        else:
            logging.info(f"CoinMarketCapWatchlist Scraper found {len(results)} coins data.")

        if self.measure_performance:
            end_time = time.time()
            logging.info(
                f"Scraper completed. "
                f"Total requests made: {self.request_count}. "
                f"Time taken: {end_time - start_time:.2f} seconds."
            )
            return self.request_count, end_time - start_time

        if self.save_csv and results:
            try:
                self.save_results_to_csv(results)
            except Exception as e:
                logging.error(f"Failed to save results to CSV: {e}")
            logging.info(f"Results saved to watchlist.csv")

        if self.save_sqlite and results:
            try:
                self.save_results_to_sqlite(results)
            except Exception as e:
                logging.error(f"Failed to save results to SQLite: {e}")
            logging.info(f"Results saved to watchlist.db")

        logging.info("CoinMarketCapWatchlist Scraper finished successfully.")

    @staticmethod
    def save_results_to_csv(data: List[dict]):
        headers = data[0].keys()
        with open('watchlist.csv', 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)

    @staticmethod
    def save_results_to_sqlite(data: List[dict]):
        conn = sqlite3.connect('watchlist.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS watchlist (
                rank INTEGER,
                name TEXT,
                symbol TEXT,
                price REAL,
                change_24h REAL,
                market_cap REAL
            )
        ''')
        cursor.executemany(
            'INSERT INTO watchlist (rank, name, symbol, price, change_24h, market_cap) VALUES (?, ?, ?, ?, ?, ?)',  # noqa
            [(
                item.get('rank'),
                item.get('name'),
                item.get('symbol'),
                item.get('price'),
                item.get('change_24h'),
                item.get('market_cap')
            ) for item in data]
        )
        conn.commit()
        conn.close()


class CoinMarketCapHTMLScraper(CoinMarketCapScraper):
    BASE_URL = 'https://coinmarketcap.com'

    def get_listing_pages(self) -> List:
        return [self.BASE_URL]

    def scrape_listing_page(self, page_url: str) -> List[dict]:
        result = []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                page.goto(page_url, wait_until='networkidle')
                self.request_count += 1
                page.wait_for_selector('table.cmc-table')

                for page_num in range(self.max_pages):
                    last_height = page.evaluate('() => document.body.scrollHeight')
                    for _ in range(30):
                        page.mouse.wheel(0, 2000)
                        page.wait_for_timeout(1000)
                        new_height = page.evaluate('() => document.body.scrollHeight')
                        if new_height == last_height:
                            break
                        last_height = new_height

                    content = page.content()
                    result.extend(self.parse_coins_table(content))

                    if page_num < self.max_pages - 1:
                        next_button = page.query_selector('div.hide_for_narrow *> li.next > a')
                        if next_button:
                            next_button.click()
                            self.request_count += 1     # Count next page click as a request
                            page.wait_for_selector('table.cmc-table', state='attached')
                            page.wait_for_timeout(1000)
                        else:
                            logging.warning(f"Could not find or click next button on page {page_num+1}")
                            break
                browser.close()
        except Exception as e:
            logging.error(f"Error occurred during scraping the {page_url}: {e}")

        return result

    def parse_coins_table(self, html_content: str) -> list:
        result = []
        soup = BeautifulSoup(html_content, 'html.parser')

        top_coins_table = soup.select_one('table.cmc-table > tbody')
        if top_coins_table:

            for row in top_coins_table.find_all('tr'):
                coin_data = {}
                coin_data_selectors = {
                    'rank': "tr > td:nth-child(2)",
                    'name': "p[class*='coin-item-name']",
                    'symbol': "p[class*='coin-item-symbol']",
                    'price': "tr > td:nth-child(4) *> span",
                    'change_24h': "tr > td:nth-child(6)",
                    'market_cap': "tr > td:nth-child(8) *> span[data-nosnippet]"
                }
                for key, selector in coin_data_selectors.items():
                    element = row.select_one(selector)

                    if element:
                        element_text = element.text.strip()
                        if key in ['price', 'change_24h', 'market_cap']:
                            coin_data[key] = float(re.sub(r'[^\d.-]', '', element_text))
                        elif key == 'rank':
                            coin_data[key] = int(element_text)
                        else:
                            coin_data[key] = element_text
                    else:
                        coin_data[key] = None

                result.append(coin_data)
        return result


class CoinMarketCapAPIScraper(CoinMarketCapScraper):
    API_URL = "https://api.coinmarketcap.com/data-api/v3/cryptocurrency/listing?start={}&limit=100&sortBy=rank&sortType=desc&convert=USD,BTC,ETH&cryptoType=all&tagType=all&audited=false&aux=ath,atl,high24h,low24h,num_market_pairs,cmc_rank,date_added,max_supply,circulating_supply,total_supply,volume_7d,volume_30d,self_reported_circulating_supply,self_reported_market_cap"    # noqa

    def get_listing_pages(self) -> List[str]:
        return [self.API_URL.format(1 + 100 * i) for i in range(self.max_pages)]

    def scrape_listing_page(self, page_url: str) -> List[dict]:
        result = []
        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9',
            'origin': 'https://coinmarketcap.com',
            'referer': 'https://coinmarketcap.com/',
            'user-agent': self.HEADERS['User-Agent'],
        }
        try:
            response = get_response_data(page_url, headers=headers, request_counter=self)
            data = response.json()
        except Exception as e:
            logging.error(f"Cannot fetch JSON data from API response: {e}.")
            return result

        coins = data.get('data', {}).get('cryptoCurrencyList', [])
        for coin in coins:
            usd_quote = next((q for q in coin.get('quotes', []) if q.get('name') == 'USD'), None)
            if not usd_quote:
                continue

            result.append({
                'rank': coin.get('cmcRank'),
                'name': coin.get('name'),
                'symbol': coin.get('symbol'),
                'price': usd_quote.get('price'),
                'change_24h': usd_quote.get('percentChange24h'),
                'market_cap': usd_quote.get('marketCap'),
            })
        return result


if __name__ == "__main__":
    # Example usage
    html_scraper = CoinMarketCapHTMLScraper(max_pages=5, save_csv=True, save_sqlite=True, logging_level='info')
    html_scraper.run_scraper()

    # api_scraper = CoinMarketCapAPIScraper(max_pages=5, save_csv=True, save_sqlite=False, logging_level='info')
    # api_scraper.run_scraper()
