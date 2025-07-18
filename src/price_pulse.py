import time
import signal
import threading
import logging

from datetime import datetime
from typing import List

from src.utils import get_response_data


user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
shutdown_event = threading.Event()


def shutdown_with_message(signum, frame):
    print("Shutting down...", flush=True)
    shutdown_event.set()


def fetch_latest_bitcoin_price() -> tuple:
    """
    Fetches the latest Bitcoin price in USD and its last updated timestamp.
    :return: Bitcoin price in USD and timestamp as a tuple (price, timestamp) or (None, None) if an error occurs.
    """

    url = 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_last_updated_at=true'
    bitcoin_data = get_response_data(url, headers={'User-Agent': user_agent}, shutdown_event=shutdown_event)
    if bitcoin_data:

        bitcoin_data = bitcoin_data.json()
        usd_price = bitcoin_data.get('bitcoin', {}).get('usd')
        last_updated_at = bitcoin_data.get('bitcoin', {}).get('last_updated_at')
        timestamp = datetime.utcfromtimestamp(last_updated_at).isoformat()

        return usd_price, timestamp
    else:
        return None, None


def compute_simple_moving_average(ticks: List[float], period: int = 10) -> float | None:
    if len(ticks) >= period:
        return sum(ticks[-period:]) / period
    return None


def poll_bitcoin_price(interval: int = 1, amount_to_poll: int = 10, sma_period: int = 10) -> List:
    """
    Polls the Bitcoin price every `interval` seconds and prints the price with timestamp.

    :param amount_to_poll: Amount of Bitcoin prices to poll.
    :param interval: Time in seconds between each poll.
    :param sma_period: Period for the simple moving average.
    :return: List of polled Bitcoin prices.
    """

    bitcoin_price_ticks = []
    while len(bitcoin_price_ticks) < amount_to_poll:

        bitcoin_price, price_datetime = fetch_latest_bitcoin_price()
        if bitcoin_price:
            bitcoin_price_ticks.append(bitcoin_price)

            current_sma = compute_simple_moving_average(bitcoin_price_ticks, period=sma_period)
            current_sma_formatted = f"{current_sma:,.2f}" if current_sma is not None else "N/A"
            print(
                f"[{price_datetime}] BTC → USD: ${bitcoin_price:,.2f} "
                f"SMA({sma_period}): ${current_sma_formatted}"
            )

        if shutdown_event.is_set():
            break

        time.sleep(interval)

    return bitcoin_price_ticks


def run(args):
    """
    Entry point for CLI integration.
    """
    logging.basicConfig(level=args.logging_level.upper())
    signal.signal(signal.SIGINT, shutdown_with_message)
    poll_bitcoin_price(
        interval=args.poll_interval,
        amount_to_poll=args.poll_amount,
        sma_period=args.sma_period
    )


def main():
    signal.signal(signal.SIGINT, shutdown_with_message)
    poll_bitcoin_price(interval=1, amount_to_poll=10, sma_period=10)


if __name__ == "__main__":
    main()
