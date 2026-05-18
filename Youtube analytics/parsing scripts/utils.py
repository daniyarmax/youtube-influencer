"""
utils.py — Shared helper utilities: URL parsing, duration conversion, link extraction.
"""

import re
import time
import logging
from urllib.parse import urlparse, parse_qs
from typing import Optional

import requests
from config import REQUEST_DELAY_SEC, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Channel ID extraction from various URL formats
# ─────────────────────────────────────────────────────────────────────────────

def extract_channel_id_from_url(url: str) -> Optional[str]:
    """
    Try to extract a channel ID directly from the URL.
    Handles formats like:
      - https://www.youtube.com/channel/UCxxxxxx
      - UCxxxxxx  (bare ID)
    Returns None for @handle or /c/ style URLs (need API resolution).
    """
    url = url.strip()

    # Bare channel ID: starts with UC and is ~24 chars
    if re.match(r'^UC[\w-]{20,}$', url):
        return url

    parsed = urlparse(url)
    path_parts = parsed.path.strip('/').split('/')

    # /channel/UCxxxxxx
    if len(path_parts) >= 2 and path_parts[0] == 'channel':
        candidate = path_parts[1]
        if candidate.startswith('UC'):
            return candidate

    return None  # needs API resolution


def normalize_channel_input(raw: str) -> dict:
    """
    Given a raw URL or ID string, return a dict with:
      - 'id'     : channel ID if immediately known, else None
      - 'handle' : @handle string if present, else None
      - 'custom' : custom /c/ name if present, else None
      - 'raw'    : original input
    """
    raw = raw.strip()
    result = {'id': None, 'handle': None, 'custom': None, 'raw': raw}

    # Direct ID
    direct = extract_channel_id_from_url(raw)
    if direct:
        result['id'] = direct
        return result

    parsed = urlparse(raw if '://' in raw else 'https://' + raw)
    path_parts = parsed.path.strip('/').split('/')

    if not path_parts:
        return result

    # @handle format
    if path_parts[0].startswith('@'):
        result['handle'] = path_parts[0]
        return result

    if len(path_parts) >= 2:
        if path_parts[0] == 'channel' and path_parts[1].startswith('UC'):
            result['id'] = path_parts[1]
        elif path_parts[0] in ('c', 'user'):
            result['custom'] = path_parts[1]
        elif path_parts[0].startswith('@'):
            result['handle'] = path_parts[0]

    return result


# ─────────────────────────────────────────────────────────────────────────────
# ISO 8601 duration parsing
# ─────────────────────────────────────────────────────────────────────────────

def parse_iso_duration(iso: str) -> tuple[str, int]:
    """
    Parse ISO 8601 duration string (e.g. PT1H3M45S).
    Returns (human_readable, total_seconds).
    """
    if not iso:
        return ("", 0)

    pattern = re.compile(
        r'P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
    )
    m = pattern.match(iso)
    if not m:
        return (iso, 0)

    days    = int(m.group(1) or 0)
    hours   = int(m.group(2) or 0)
    minutes = int(m.group(3) or 0)
    seconds = int(m.group(4) or 0)

    total = days * 86400 + hours * 3600 + minutes * 60 + seconds

    parts = []
    if hours or days:
        parts.append(f"{hours + days * 24}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds:
        parts.append(f"{seconds}s")

    human = ' '.join(parts) if parts else '0s'
    return (human, total)


# ─────────────────────────────────────────────────────────────────────────────
# Link / URL extraction from text
# ─────────────────────────────────────────────────────────────────────────────

URL_RE = re.compile(
    r'https?://[^\s\)\]\"\'<>]+',
    re.IGNORECASE
)


def extract_urls(text: str) -> list[str]:
    """Extract all HTTP/HTTPS URLs from a block of text."""
    if not text:
        return []
    return URL_RE.findall(text)


def get_domain(url: str) -> str:
    """Return lowercase domain (no www.) from a URL."""
    try:
        return urlparse(url).netloc.lower().replace('www.', '')
    except Exception:
        return ''


# ─────────────────────────────────────────────────────────────────────────────
# Keyword matching
# ─────────────────────────────────────────────────────────────────────────────

def find_keywords(text: str, keywords: list[str]) -> list[str]:
    """Return list of keywords found in text (case-insensitive)."""
    if not text:
        return []
    text_lower = text.lower()
    return [kw for kw in keywords if kw.lower() in text_lower]


def find_domains(urls: list[str], domains: list[str]) -> list[str]:
    """Return list of store/affiliate domains found among the given URLs."""
    found = set()
    for url in urls:
        d = get_domain(url)
        for domain in domains:
            if domain in d:
                found.add(domain)
    return sorted(found)


# ─────────────────────────────────────────────────────────────────────────────
# Social platform detection
# ─────────────────────────────────────────────────────────────────────────────

def detect_social_platforms(urls: list[str], platform_map: dict) -> dict[str, bool]:
    """
    Given a list of URLs and a platform_map like {'instagram': ['instagram.com'], ...},
    return a dict like {'instagram': True, 'telegram': False, ...}.
    """
    result = {platform: False for platform in platform_map}
    for url in urls:
        d = get_domain(url)
        for platform, patterns in platform_map.items():
            if any(p in d or p in url.lower() for p in patterns):
                result[platform] = True
    return result


# ─────────────────────────────────────────────────────────────────────────────
# HTTP helper with retry and delay
# ─────────────────────────────────────────────────────────────────────────────

def safe_get(url: str, headers: dict = None, retries: int = 2) -> Optional[requests.Response]:
    """
    GET request with retry logic and polite delay.
    Returns Response or None on failure.
    """
    time.sleep(REQUEST_DELAY_SEC)
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                return resp
            logger.warning(f"HTTP {resp.status_code} for {url}")
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout on attempt {attempt + 1} for {url}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request error: {e}")
        if attempt < retries:
            time.sleep(2 ** attempt)   # exponential back-off
    return None
