"""
main.py — Entry point for the YouTube Tech Channel Research Tool.

Usage:
    python main.py
    python main.py --max-videos 30 --output-dir ./results --no-excel

Edit the CHANNEL_INPUTS list below to specify your channels.
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

from api_client import YouTubeAPIClient
from parser    import analyse_channel_text, scrape_channel_about
from analytics import build_summary_row
from exporter  import save_all
from config    import MAX_VIDEOS_DEFAULT

# ─────────────────────────────────────────────────────────────────────────────
# EDIT THIS LIST — add 30–50 YouTube channel URLs or IDs
# ─────────────────────────────────────────────────────────────────────────────
CHANNEL_INPUTS = [
    # 🔝 TOP TIER (1M+)
    "https://www.youtube.com/@Wylsacom",
    "https://www.youtube.com/@rozetked",
    "https://www.youtube.com/@droider",
    "https://www.youtube.com/@ixbt",
    "https://www.youtube.com/@IXBT_live",
    "https://www.youtube.com/@ProHiTech",
    "https://www.youtube.com/@AlexGyver",
    "https://www.youtube.com/@Romancev768",
    "https://www.youtube.com/@TechZone",
    "https://www.youtube.com/@Valaybalalay",

    # 📱 GADGETS / SMARTPHONES
    "https://www.youtube.com/@AndroNews",
    "https://www.youtube.com/@FERUMM",
    "https://www.youtube.com/@MobileReviewcom",
    "https://www.youtube.com/@BigGeekRu",
    "https://www.youtube.com/@RozetkedLive",
    "https://www.youtube.com/@QukeRu",
    "https://www.youtube.com/@Smartobzor",
    "https://www.youtube.com/@ChudoTech",
    "https://www.youtube.com/@TechnoArena",
    "https://www.youtube.com/@HonestTechReviews",

    # 💻 IT / PROGRAMMING / HARDWARE
    "https://www.youtube.com/@ХаудиХо",
    "https://www.youtube.com/@EgoroffChannel",
    "https://www.youtube.com/@LoftBlog",
    "https://www.youtube.com/@GloAcademy",
    "https://www.youtube.com/@UlbiTV",
    "https://www.youtube.com/@ITDoctor",
    "https://www.youtube.com/@SelfEdu",
    "https://www.youtube.com/@SimpleCode",
    "https://www.youtube.com/@WebDeveloperBlog",
    "https://www.youtube.com/@PurpleSchool",

    # 🖥 PC / DIY / ENGINEERING
    "https://www.youtube.com/@OverclockersRussia",
    "https://www.youtube.com/@DigitalRazor",
    "https://www.youtube.com/@PC-Expert",
    "https://www.youtube.com/@HardWareMan",
    "https://www.youtube.com/@Remonter",
    "https://www.youtube.com/@FixitBlog",
    "https://www.youtube.com/@TechnoKitchen",
    "https://www.youtube.com/@AlexGyverLive",
    "https://www.youtube.com/@RadioKot",
    "https://www.youtube.com/@DIYTechRU",

    # 🔬 SCIENCE / TECH EXPLAINERS
    "https://www.youtube.com/@GEO",
    "https://www.youtube.com/@Keddr",
    "https://www.youtube.com/@GadgetPage",
    "https://www.youtube.com/@TechInsiderRussia",
    "https://www.youtube.com/@Nplus1",
    "https://www.youtube.com/@Science4People",

    # 🇰🇿 / CIS LOCAL (IMPORTANT FOR ADS)
    "https://www.youtube.com/@AlisherTech",
    "https://www.youtube.com/@SimpleIdea",
    "https://www.youtube.com/@stupidmadworld",

    # 🔥 MIXED TECH / EXPERIMENT / HIGH ENGAGEMENT
    "https://www.youtube.com/@CrazyRussianHacker",
    "https://www.youtube.com/@SlivkiShow",
    "https://www.youtube.com/@ItsMamix",
    "https://www.youtube.com/@SuperCrastan",

    # 📦 SMALL / MID (BEST ROI FOR ADS)
    "https://www.youtube.com/@TechnoBlog",
    "https://www.youtube.com/@DailyTechRu",
    "https://www.youtube.com/@ReviewZoneRU",
    "https://www.youtube.com/@SmartLifeTech",
    "https://www.youtube.com/@GadgetReviewRU",
    "https://www.youtube.com/@DeviceLab",
    "https://www.youtube.com/@TechnoExpertRU",
    "https://www.youtube.com/@MobileExpertRU",
    # Add more channels here ↓
    # "UCxxxxxxxxxxxxxx",                     # by channel ID
    # "https://www.youtube.com/@handle",      # by @handle
    # "https://www.youtube.com/channel/UCxx", # by /channel/ URL
]


# ─────────────────────────────────────────────────────────────────────────────
# Logging setup
# ─────────────────────────────────────────────────────────────────────────────

def setup_logging(log_file: str = 'research.log') -> None:
    fmt = '%(asctime)s [%(levelname)s] %(name)s — %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=fmt,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding='utf-8'),
        ]
    )


logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Core pipeline
# ─────────────────────────────────────────────────────────────────────────────

def run_pipeline(
    channel_inputs: list[str],
    api_key:        str,
    max_videos:     int  = MAX_VIDEOS_DEFAULT,
    output_dir:     str  = './output',
    do_scrape:      bool = False,
    save_excel:     bool = True,
    save_json:      bool = True,
) -> None:
    """
    Main pipeline:
      1. Resolve channel IDs
      2. Fetch channel metadata via API
      3. Fetch latest N videos via API
      4. Analyse text content (descriptions, tags)
      5. Optionally scrape About page
      6. Compute aggregate metrics
      7. Save to CSV / Excel / JSON
    """
    client = YouTubeAPIClient(api_key)

    all_channels  = []
    all_videos    = []
    all_summaries = []

    total = len(channel_inputs)
    logger.info(f"Starting pipeline for {total} channel(s). max_videos={max_videos}")

    for idx, raw_input in enumerate(channel_inputs, start=1):
        logger.info(f"[{idx}/{total}] Processing: {raw_input!r}")

        # ── Step 1: Resolve channel ID ─────────────────────────────────────
        channel_id = client.resolve_channel_id(raw_input)
        if not channel_id:
            logger.warning(f"  ↳ Could not resolve channel ID, skipping.")
            continue

        # ── Step 2: Channel metadata ───────────────────────────────────────
        channel = client.get_channel_info(channel_id)
        if not channel:
            logger.warning(f"  ↳ Channel info unavailable for {channel_id}, skipping.")
            continue

        logger.info(f"  ↳ Channel: {channel['channel_title']} ({channel['subscriber_count']:,} subs)")

        # ── Step 3: Fetch video IDs ────────────────────────────────────────
        uploads_id = channel.get('uploads_playlist_id', '')
        if not uploads_id:
            logger.warning(f"  ↳ No uploads playlist found, skipping videos.")
            video_records = []
        else:
            video_ids = client.get_latest_video_ids(uploads_id, max_videos=max_videos)
            logger.info(f"  ↳ Found {len(video_ids)} video IDs, fetching details...")
            video_records = client.get_video_details(video_ids, channel_id)
            logger.info(f"  ↳ Retrieved details for {len(video_records)} videos.")

        # ── Step 4: Content analysis (API text) ───────────────────────────
        parsed = analyse_channel_text(
            channel_description=channel.get('description', ''),
            video_records=video_records
        )

        # Extract per-video analysis and remove from channel-level dict
        video_analysis_rows = parsed.pop('_video_analysis', [])

        # Merge parsed signals into channel dict
        channel.update(parsed)

        # ── Step 5: Optional HTML scrape ──────────────────────────────────
        if do_scrape:
            scrape_data = scrape_channel_about(channel_id)
            channel['scrape_status']       = scrape_data.get('scrape_status', '')
            channel['scraped_description'] = scrape_data.get('scraped_description', '')
            channel['scraped_links']       = scrape_data.get('scraped_links', '')

        # ── Step 6: Merge per-video analysis into video records ───────────
        video_analysis_map = {
            row['video_id']: row for row in video_analysis_rows
        }
        for v in video_records:
            vid_id = v.get('video_id', '')
            extra  = video_analysis_map.get(vid_id, {})
            # Remove redundant key before merging
            extra.pop('video_id', None)
            v.update(extra)

        # ── Step 7: Summary metrics ────────────────────────────────────────
        summary = build_summary_row(channel, video_records)

        # ── Collect results ────────────────────────────────────────────────
        all_channels.append(channel)
        all_videos.extend(video_records)
        all_summaries.append(summary)

        # Polite pause between channels
        if idx < total:
            time.sleep(0.5)

    logger.info(
        f"Pipeline complete. "
        f"Channels: {len(all_channels)}, "
        f"Videos: {len(all_videos)}"
    )

    # ── Step 8: Save output ────────────────────────────────────────────────
    save_all(
        channels=all_channels,
        videos=all_videos,
        summaries=all_summaries,
        output_dir=output_dir,
        save_excel=save_excel,
        save_json=save_json,
    )

    logger.info(f"All files saved to: {Path(output_dir).resolve()}")


# ─────────────────────────────────────────────────────────────────────────────
# CLI argument parsing
# ─────────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description='YouTube Tech Channel Research Tool'
    )
    p.add_argument(
        '--max-videos', type=int, default=MAX_VIDEOS_DEFAULT,
        help=f'Max videos per channel (default: {MAX_VIDEOS_DEFAULT})'
    )
    p.add_argument(
        '--output-dir', type=str, default='./output',
        help='Directory to save output files (default: ./output)'
    )
    p.add_argument(
        '--scrape', action='store_true',
        help='Also attempt to scrape YouTube About pages (partial results only)'
    )
    p.add_argument(
        '--no-excel', action='store_true',
        help='Skip Excel export'
    )
    p.add_argument(
        '--no-json', action='store_true',
        help='Skip JSON export'
    )
    return p.parse_args()


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    setup_logging()
    load_dotenv()

    args = parse_args()

    api_key = os.getenv('YOUTUBE_API_KEY', '')
    if not api_key:
        logger.error(
            "YOUTUBE_API_KEY not found. "
            "Create a .env file with YOUTUBE_API_KEY=your_key_here"
        )
        sys.exit(1)

    run_pipeline(
        channel_inputs=CHANNEL_INPUTS,
        api_key=api_key,
        max_videos=args.max_videos,
        output_dir=args.output_dir,
        do_scrape=args.scrape,
        save_excel=not args.no_excel,
        save_json=not args.no_json,
    )
