"""
analytics.py — Compute channel-level aggregate metrics from video data.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


def compute_channel_metrics(channel: dict, videos: list[dict]) -> dict:
    """
    Given a channel dict and its list of video dicts,
    return a dict of computed aggregate metrics.
    """
    if not videos:
        return _empty_metrics()

    df = pd.DataFrame(videos)

    # ── Basic averages ───────────────────────────────────────────────────────
    avg_views    = _safe_mean(df, 'view_count')
    avg_likes    = _safe_mean(df, 'like_count')
    avg_comments = _safe_mean(df, 'comment_count')

    # ── Engagement rate ──────────────────────────────────────────────────────
    # engagement = (likes + comments) / views per video, then averaged
    if 'view_count' in df.columns and 'like_count' in df.columns:
        mask = df['view_count'] > 0
        if mask.any():
            df_eng = df[mask].copy()
            df_eng['eng'] = (
                (df_eng['like_count'].fillna(0) + df_eng['comment_count'].fillna(0))
                / df_eng['view_count']
            )
            engagement_rate = round(df_eng['eng'].mean(), 6)
        else:
            engagement_rate = 0.0
    else:
        engagement_rate = 0.0

    # ── Upload frequency ─────────────────────────────────────────────────────
    upload_freq = _compute_upload_frequency(df)

    return {
        'avg_views_last_50':      round(avg_views, 2),
        'avg_likes_last_50':      round(avg_likes, 2),
        'avg_comments_last_50':   round(avg_comments, 2),
        'engagement_rate_estimate': engagement_rate,
        'upload_frequency_estimate': upload_freq,
        'videos_analysed':        len(videos),
    }


def _safe_mean(df: pd.DataFrame, col: str) -> float:
    if col not in df.columns:
        return 0.0
    return float(df[col].fillna(0).mean())


def _compute_upload_frequency(df: pd.DataFrame) -> str:
    """
    Estimate uploads per week based on date range of the fetched videos.
    Returns a human-readable string like '2.3 videos/week'.
    """
    if 'published_at' not in df.columns or df.empty:
        return 'unknown'

    try:
        dates = pd.to_datetime(df['published_at'], utc=True, errors='coerce').dropna()
        if len(dates) < 2:
            return 'insufficient data'

        date_range_days = (dates.max() - dates.min()).days
        if date_range_days == 0:
            return 'insufficient data'

        videos_per_day  = len(dates) / date_range_days
        videos_per_week = videos_per_day * 7

        return f'{videos_per_week:.1f} videos/week'
    except Exception as e:
        logger.warning(f"Could not compute upload frequency: {e}")
        return 'error'


def _empty_metrics() -> dict:
    return {
        'avg_views_last_50':         0,
        'avg_likes_last_50':         0,
        'avg_comments_last_50':      0,
        'engagement_rate_estimate':  0,
        'upload_frequency_estimate': 'no videos',
        'videos_analysed':           0,
    }


def build_summary_row(channel: dict, videos: list[dict]) -> dict:
    """
    Merge channel info, parsed signals, and computed metrics into a
    single flat summary dict (one row in summary_report.csv).
    """
    metrics = compute_channel_metrics(channel, videos)

    # Fields to include from the channel dict (exclude internal ones)
    EXCLUDE = {'uploads_playlist_id', '_video_analysis', 'description'}
    summary = {k: v for k, v in channel.items() if k not in EXCLUDE}
    summary.update(metrics)

    return summary
