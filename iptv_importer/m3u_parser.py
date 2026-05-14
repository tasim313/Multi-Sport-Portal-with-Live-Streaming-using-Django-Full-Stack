"""
M3U playlist parser for IPTV-org channels.
Parses #EXTINF lines to extract channel metadata and stream URLs.
"""
import re
import logging
import requests
from typing import Iterator, Dict, Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# iptv-org M3U sources by category
IPTV_ORG_PLAYLISTS = {
    'sports': 'https://iptv-org.github.io/iptv/categories/sports.m3u',
    'news': 'https://iptv-org.github.io/iptv/categories/news.m3u',
    'entertainment': 'https://iptv-org.github.io/iptv/categories/entertainment.m3u',
    'movies': 'https://iptv-org.github.io/iptv/categories/movies.m3u',
    'kids': 'https://iptv-org.github.io/iptv/categories/kids.m3u',
    'music': 'https://iptv-org.github.io/iptv/categories/music.m3u',
}

# Master playlist (all channels)
IPTV_ORG_MASTER = 'https://iptv-org.github.io/iptv/index.m3u'


def _extract_attr(extinf_line: str, attr_name: str) -> str:
    """Extract an attribute value from an #EXTINF line."""
    pattern = rf'{re.escape(attr_name)}="([^"]*)"'
    match = re.search(pattern, extinf_line)
    return match.group(1).strip() if match else ''


def parse_m3u_content(content: str) -> Iterator[Dict[str, Any]]:
    """
    Parse M3U content and yield channel dicts.
    Each dict has: name, stream_url, tvg_id, logo, group_title, country, language
    """
    lines = content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('#EXTINF:'):
            # Parse metadata from EXTINF line
            channel = {}
            channel['tvg_id'] = _extract_attr(line, 'tvg-id')
            channel['logo'] = _extract_attr(line, 'tvg-logo')
            channel['country'] = _extract_attr(line, 'tvg-country')
            channel['language'] = _extract_attr(line, 'tvg-language')
            channel['group_title'] = _extract_attr(line, 'group-title')

            # Channel name is after the last comma
            comma_idx = line.rfind(',')
            channel['name'] = line[comma_idx + 1:].strip() if comma_idx != -1 else 'Unknown'

            # Next non-empty line should be the stream URL
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1

            if j < len(lines):
                url_line = lines[j].strip()
                if url_line and not url_line.startswith('#'):
                    channel['stream_url'] = url_line
                    i = j + 1
                    yield channel
                    continue

        i += 1


def fetch_m3u_playlist(url: str, timeout: int = 30) -> str:
    """Fetch M3U playlist content from URL."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; SportPortalBot/1.0)',
        'Accept': '*/*',
    }
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logger.error(f"Failed to fetch M3U from {url}: {e}")
        return ''


def normalize_country_code(country_str: str) -> str:
    """Normalize country string to 2-letter uppercase code if possible."""
    if not country_str:
        return ''
    # If already looks like a code (1-3 chars, uppercase)
    stripped = country_str.strip().upper()
    if len(stripped) <= 3 and stripped.isalpha():
        return stripped[:2]
    return country_str[:2].upper()


def map_group_to_category(group_title: str) -> str:
    """Map iptv-org group-title to our standardized categories."""
    group_lower = (group_title or '').lower()
    if any(x in group_lower for x in ['sport', 'football', 'cricket', 'tennis', 'basketball']):
        return 'Sports'
    if any(x in group_lower for x in ['news', 'information']):
        return 'News'
    if any(x in group_lower for x in ['entertain', 'general']):
        return 'Entertainment'
    if any(x in group_lower for x in ['movie', 'film', 'cinema']):
        return 'Movies'
    if any(x in group_lower for x in ['kid', 'child', 'cartoon', 'animation']):
        return 'Kids'
    if any(x in group_lower for x in ['music', 'radio']):
        return 'Music'
    if group_title:
        return group_title.title()[:120]
    return 'Other'


def check_stream_health(url: str, timeout: int = 5) -> bool:
    """Quick HEAD request to check if stream URL is reachable."""
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code < 400
    except Exception:
        return False
