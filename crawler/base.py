"""
Base crawler with rotating proxies and user agents.
Anti-block protection built in.
"""
import random
import time
import logging
import requests
from typing import Optional, Dict, Any
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
]

ACCEPT_LANGUAGES = [
    'en-US,en;q=0.9',
    'en-GB,en;q=0.8,en-US;q=0.7',
    'en-US,en;q=0.8',
]


class BaseCrawler:
    """
    Base scraper with anti-block protection:
    - Rotating user agents
    - Random delays between requests
    - Optional proxy rotation
    - Retry logic with exponential backoff
    """

    def __init__(
        self,
        proxies: Optional[list] = None,
        min_delay: float = 1.5,
        max_delay: float = 4.0,
        max_retries: int = 3,
        timeout: int = 15,
    ):
        self.proxies = proxies or []
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
        self.timeout = timeout
        self._session = requests.Session()

    def _get_headers(self) -> Dict[str, str]:
        return {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': random.choice(ACCEPT_LANGUAGES),
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }

    def _get_proxy(self) -> Optional[Dict]:
        if not self.proxies:
            return None
        proxy_url = random.choice(self.proxies)
        return {'http': proxy_url, 'https': proxy_url}

    def _sleep(self):
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)

    def fetch(self, url: str, params: Optional[Dict] = None) -> Optional[str]:
        """Fetch URL with retry logic and anti-block measures."""
        for attempt in range(self.max_retries):
            try:
                if attempt > 0:
                    # Exponential backoff
                    time.sleep(2 ** attempt + random.uniform(0, 1))

                response = self._session.get(
                    url,
                    params=params,
                    headers=self._get_headers(),
                    proxies=self._get_proxy(),
                    timeout=self.timeout,
                    allow_redirects=True,
                )

                if response.status_code == 429:
                    # Rate limited - wait longer
                    logger.warning(f"Rate limited on {url}, waiting...")
                    time.sleep(30 + random.uniform(0, 15))
                    continue

                if response.status_code == 403:
                    logger.warning(f"403 Forbidden on {url}")
                    return None

                response.raise_for_status()

                # Random delay after successful request
                self._sleep()
                return response.text

            except requests.RequestException as e:
                logger.warning(f"Fetch attempt {attempt + 1} failed for {url}: {e}")
                if attempt == self.max_retries - 1:
                    logger.error(f"All retries failed for {url}")
                    return None

        return None

    def fetch_json(self, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Fetch URL and parse JSON response."""
        for attempt in range(self.max_retries):
            try:
                if attempt > 0:
                    time.sleep(2 ** attempt + random.uniform(0, 1))

                response = self._session.get(
                    url,
                    params=params,
                    headers={**self._get_headers(), 'Accept': 'application/json'},
                    proxies=self._get_proxy(),
                    timeout=self.timeout,
                )

                if response.status_code == 429:
                    time.sleep(30)
                    continue

                response.raise_for_status()
                self._sleep()
                return response.json()

            except (requests.RequestException, ValueError) as e:
                logger.warning(f"JSON fetch attempt {attempt + 1} failed for {url}: {e}")
                if attempt == self.max_retries - 1:
                    return None

        return None
