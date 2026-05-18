"""
parser.py — Content analysis and optional web scraping.

PRIMARY approach: analyse text already fetched via the API
  (channel description + video descriptions).

OPTIONAL scraping approach: fetch YouTube channel About page via HTTP
  (works for static elements; YouTube is heavily JavaScript-rendered so
   scraping results are often incomplete — see notes at bottom).
"""

import logging
from typing import Optional
from bs4 import BeautifulSoup

from config import (
    ALL_AD_KEYWORDS,
    STORE_DOMAINS,
    SOCIAL_PLATFORMS,
)
from utils import (
    extract_urls,
    get_domain,
    find_keywords,
    find_domains,
    detect_social_platforms,
    safe_get,
)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Headers that mimic a normal browser (helps avoid bot-blocking)
# ─────────────────────────────────────────────────────────────────────────────
HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/122.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8',
}


# ─────────────────────────────────────────────────────────────────────────────
# Main analysis function — works entirely from API text data
# ─────────────────────────────────────────────────────────────────────────────

def analyse_channel_text(channel_description: str, video_records: list[dict]) -> dict:
    """
    Analyse a channel's description and all video descriptions for:
      - advertising / commercial keywords
      - external URLs and their categories
      - social platform presence
      - store / marketplace links

    Returns a dict of derived analytical fields.
    Source: API text data (no scraping needed for this step).
    """

    # ── Combine all text sources ─────────────────────────────────────────────
    all_text_parts = [channel_description or '']
    all_video_descriptions = []

    for v in video_records:
        desc = v.get('description', '') or ''
        all_text_parts.append(desc)
        all_video_descriptions.append(desc)

    combined_text = '\n'.join(all_text_parts)

    # ── Extract all URLs ─────────────────────────────────────────────────────
    all_urls       = extract_urls(combined_text)
    channel_urls   = extract_urls(channel_description or '')

    # ── Ad keyword matching ──────────────────────────────────────────────────
    matched_keywords = find_keywords(combined_text, ALL_AD_KEYWORDS)

    # ── Store / marketplace domain matching ──────────────────────────────────
    matched_store_domains = find_domains(all_urls, STORE_DOMAINS)

    # ── Social platform detection (from channel description) ─────────────────
    social_flags = detect_social_platforms(channel_urls, SOCIAL_PLATFORMS)

    # ── Affiliate signal heuristic ───────────────────────────────────────────
    affiliate_keywords = ['affiliate', 'referral', 'amzn.to', 'aliexpress', 'go.link']
    has_affiliate = any(kw in combined_text.lower() for kw in affiliate_keywords)
    if find_domains(all_urls, ['amzn.to', 'aliexpress.com', 'aliexpress.ru']):
        has_affiliate = True

    # ── Per-video signals ────────────────────────────────────────────────────
    videos_with_ad_signals   = 0
    videos_with_ext_links    = 0
    video_analysis           = []

    for v in video_records:
        desc = v.get('description', '') or ''
        v_urls     = extract_urls(desc)
        v_keywords = find_keywords(desc, ALL_AD_KEYWORDS)

        has_ad    = len(v_keywords) > 0
        has_links = len(v_urls) > 0

        if has_ad:    videos_with_ad_signals += 1
        if has_links: videos_with_ext_links  += 1

        video_analysis.append({
            'video_id':              v.get('video_id', ''),
            'has_ad_keywords':       has_ad,
            'matched_ad_keywords':   '|'.join(v_keywords),
            'has_external_links':    has_links,
            'external_links_count':  len(v_urls),
            'external_links':        '|'.join(v_urls[:20]),  # cap at 20
            'data_source':           'API text analysis',
        })

    n_videos = len(video_records)
    prop_ad    = round(videos_with_ad_signals / n_videos, 4) if n_videos else 0
    prop_links = round(videos_with_ext_links  / n_videos, 4) if n_videos else 0

    # ── External-ecosystem detection ─────────────────────────────────────────
    ecosystem = (
        any(social_flags.values())
        or bool(matched_store_domains)
        or has_affiliate
        or bool(matched_keywords)
    )

    return {
        # ── boolean channel-level flags ─────────────────────────────────────
        'has_ad_keywords':        len(matched_keywords) > 0,
        'has_affiliate_signals':  has_affiliate,
        'has_marketplace_links':  len(matched_store_domains) > 0,
        'has_brand_store_links':  bool(find_domains(all_urls, STORE_DOMAINS)),
        'has_instagram':          social_flags.get('instagram', False),
        'has_telegram':           social_flags.get('telegram', False),
        'has_tiktok':             social_flags.get('tiktok', False),
        'has_vk':                 social_flags.get('vk', False),
        'has_twitter_x':          social_flags.get('twitter_x', False),
        'has_facebook':           social_flags.get('facebook', False),
        'has_discord':            social_flags.get('discord', False),
        'has_external_links':     len(all_urls) > 0,
        'external_links_count':   len(all_urls),
        'ecosystem_detected':     ecosystem,
        # ── string detail fields ─────────────────────────────────────────────
        'matched_ad_keywords':    '|'.join(matched_keywords),
        'matched_store_domains':  '|'.join(matched_store_domains),
        'channel_external_links': '|'.join(channel_urls[:30]),
        # ── per-video proportions ────────────────────────────────────────────
        'proportion_videos_with_ad_signals':    prop_ad,
        'proportion_videos_with_external_links': prop_links,
        # ── per-video detail (list of dicts, merged back in main.py) ────────
        '_video_analysis':        video_analysis,
        # ── source tag ───────────────────────────────────────────────────────
        'parser_data_source':     'API text analysis',
    }


# ─────────────────────────────────────────────────────────────────────────────
# Optional: Attempt to scrape the YouTube About page (static HTML only)
# ─────────────────────────────────────────────────────────────────────────────

def scrape_channel_about(channel_id: str) -> dict:
    """
    Attempt to fetch the channel's /about page via plain HTTP.

    ⚠️ LIMITATION: YouTube renders most content via JavaScript.
    Plain HTTP requests will receive a mostly empty page.
    This function extracts what it can from the initial HTML payload
    (sometimes description / link metadata is in <meta> or JSON-LD tags).

    For full scraping you would need Selenium / Playwright.
    Returns a dict with any additionally found data plus a 'scrape_status' key.
    """
    url = f'https://www.youtube.com/@/about'   # generic fallback
    # Build URL using channel ID
    about_url = f'https://www.youtube.com/channel/{channel_id}/about'

    result = {
        'scrape_status':        'not_attempted',
        'scraped_description':  '',
        'scraped_links':        '',
        'data_source':          'HTTP scrape (partial – JS-rendered content not available)',
    }

    resp = safe_get(about_url, headers=HEADERS)
    if resp is None:
        result['scrape_status'] = 'request_failed'
        return result

    soup = BeautifulSoup(resp.text, 'lxml')

    # Try to extract description from <meta> tags
    desc_tag = (
        soup.find('meta', {'name': 'description'}) or
        soup.find('meta', {'property': 'og:description'})
    )
    if desc_tag and desc_tag.get('content'):
        result['scraped_description'] = desc_tag['content']

    # Try to find any links in the page
    links_found = []
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if href.startswith('http') and 'youtube.com' not in href:
            links_found.append(href)

    result['scraped_links']  = '|'.join(links_found[:30])
    result['scrape_status']  = 'partial'  # JS content likely missing

    logger.info(
        f"Scraped About page for {channel_id}: "
        f"desc={'yes' if result['scraped_description'] else 'no'}, "
        f"links={len(links_found)}"
    )
    return result


# ─────────────────────────────────────────────────────────────────────────────
# NOTE ON YOUTUBE SCRAPING LIMITATIONS
# ─────────────────────────────────────────────────────────────────────────────
#
# YouTube is a Single-Page Application (SPA).
# When you make a plain HTTP GET to a YouTube URL, the server returns a
# skeletal HTML page. The actual channel description, link list, and
# subscriber count are injected by JavaScript after page load.
#
# This means:
#   ✅ Meta tags (og:description, og:title) — sometimes present in static HTML
#   ❌ Full "About" tab text              — requires JS execution
#   ❌ "Links" section in About           — requires JS execution
#   ❌ Dynamic subscriber counts          — requires JS execution
#
# Alternatives:
#   1. Use the official YouTube Data API (preferred, used in api_client.py)
#   2. Use Selenium or Playwright to render the page (heavy, slow, fragile)
#   3. Use yt-dlp's channel metadata extraction (unofficial, may break)
#
# This project uses the API as the primary source and scraping only as a
# supplementary / best-effort attempt.
