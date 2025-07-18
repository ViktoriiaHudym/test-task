import time
import logging
import requests


def get_response_data(url, headers=None, method='GET', max_attempts=5, shutdown_event=None,
                      request_counter=None) -> requests.Response | None:
    time_to_wait = 1
    attempts = 0
    while True:
        try:
            response = requests.request(method=method, url=url, headers=headers, timeout=10)
            response.raise_for_status()

            if request_counter is not None:
                if hasattr(request_counter, 'request_count'):
                    request_counter.request_count += 1

            return response
        except requests.exceptions.RequestException as e:
            logging.info(f"Error fetching data: {e}. Retrying in {time_to_wait} seconds...")
            time.sleep(time_to_wait)
            time_to_wait *= 2       # Exponential backoff

        if shutdown_event and shutdown_event.is_set():
            break

        attempts += 1
        if attempts == max_attempts:
            logging.error(f"Max attempts reached ({max_attempts})!")
            break

    return None
