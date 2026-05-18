"""
exporter.py — Save collected data to CSV, Excel (.xlsx), and JSON.
"""

import json
import logging
from pathlib import Path

import pandas as pd

from config import (
    OUT_CHANNELS_CSV,
    OUT_VIDEOS_CSV,
    OUT_SUMMARY_CSV,
    OUT_EXCEL,
    OUT_JSON_CHANNELS,
    OUT_JSON_VIDEOS,
)

logger = logging.getLogger(__name__)


def save_all(
    channels: list[dict],
    videos:   list[dict],
    summaries: list[dict],
    output_dir: str = '.',
    save_excel: bool = True,
    save_json:  bool = True,
) -> None:
    """
    Save all three datasets to CSV (and optionally Excel + JSON).

    Args:
        channels:   list of channel dicts
        videos:     list of video dicts (all channels combined)
        summaries:  list of summary dicts (one per channel)
        output_dir: folder to write files into
        save_excel: also write an .xlsx file with multiple sheets
        save_json:  also write JSON exports
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    df_channels  = pd.DataFrame(channels)
    df_videos    = pd.DataFrame(videos)
    df_summaries = pd.DataFrame(summaries)

    # ── CSV ──────────────────────────────────────────────────────────────────
    _write_csv(df_channels,  out / OUT_CHANNELS_CSV,  'channels')
    _write_csv(df_videos,    out / OUT_VIDEOS_CSV,    'videos')
    _write_csv(df_summaries, out / OUT_SUMMARY_CSV,   'summary')

    # ── Excel ────────────────────────────────────────────────────────────────
    if save_excel:
        excel_path = out / OUT_EXCEL
        try:
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                df_channels.to_excel(writer,  sheet_name='Channels',  index=False)
                df_videos.to_excel(writer,    sheet_name='Videos',    index=False)
                df_summaries.to_excel(writer, sheet_name='Summary',   index=False)
                _write_readme_sheet(writer)
            logger.info(f"Excel saved → {excel_path}")
        except Exception as e:
            logger.error(f"Excel export failed: {e}")

    # ── JSON ─────────────────────────────────────────────────────────────────
    if save_json:
        _write_json(channels,  out / OUT_JSON_CHANNELS, 'channels')
        _write_json(videos,    out / OUT_JSON_VIDEOS,   'videos')


def _write_csv(df: pd.DataFrame, path: Path, label: str) -> None:
    if df.empty:
        logger.warning(f"No data for {label}, skipping CSV.")
        return
    df.to_csv(path, index=False, encoding='utf-8-sig')
    logger.info(f"{label.capitalize()} CSV saved → {path}  ({len(df)} rows)")


def _write_json(data: list, path: Path, label: str) -> None:
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        logger.info(f"{label.capitalize()} JSON saved → {path}")
    except Exception as e:
        logger.error(f"JSON export failed for {label}: {e}")


def _write_readme_sheet(writer) -> None:
    """Add a README sheet explaining the dataset."""
    readme_data = {
        'Sheet': ['Channels', 'Videos', 'Summary'],
        'Description': [
            'One row per YouTube channel — metadata from the API + parsed signals',
            'One row per video — stats from the API + per-video content analysis',
            'One row per channel — aggregated metrics (avg views, engagement rate, etc.)',
        ],
        'Primary data source': [
            'YouTube Data API v3',
            'YouTube Data API v3',
            'Computed from API data',
        ],
    }
    pd.DataFrame(readme_data).to_excel(writer, sheet_name='README', index=False)
