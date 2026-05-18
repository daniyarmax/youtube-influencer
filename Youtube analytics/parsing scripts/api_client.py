"""
api_client.py — YouTube Data API v3 wrapper.

Handles:
  - Resolving channel handles / custom URLs → channel IDs
  - Fetching channel metadata
  - Fetching latest N videos via the uploads playlist
  - Fetching detailed video statistics
  - Quota-aware error handling
"""

import logging
import time
from typing import Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from utils import normalize_channel_input, parse_iso_duration

logger = logging.getLogger(__name__)

# YouTube Data API v3 quota costs (units per call):
#   channels.list  → 1 unit
#   playlistItems  → 1 unit
#   videos.list    → 1 unit
#   search.list    → 100 units  ← expensive, use sparingly


class YouTubeAPIClient:
    """Thin wrapper around the YouTube Data API v3."""

    def __init__(self, api_key: str):
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        logger.info("YouTube API client initialised.")

    # ──────────────────────────────────────────────────────────────────────────
    # Channel ID resolution
    # ──────────────────────────────────────────────────────────────────────────

    def resolve_channel_id(self, raw_input: str) -> Optional[str]:
        """
        Convert any channel URL / handle / custom name to a channel ID.
        Returns None if resolution fails.
        """
        info = normalize_channel_input(raw_input)

        # Already have an ID
        if info['id']:
            return info['id']

        # @handle → use forHandle parameter (API v3 ≥ 2023)
        if info['handle']:
            return self._resolve_by_handle(info['handle'])

        # /c/customName or /user/name → use forUsername
        if info['custom']:
            return self._resolve_by_username(info['custom'])

        logger.warning(f"Could not parse channel input: {raw_input!r}")
        return None

    def _resolve_by_handle(self, handle: str) -> Optional[str]:
        """Resolve @handle to channel ID."""
        handle_clean = handle.lstrip('@')
        try:
            resp = self.youtube.channels().list(
                part='id',
                forHandle=handle_clean
            ).execute()
            items = resp.get('items', [])
            if items:
                return items[0]['id']
        except HttpError as e:
            logger.error(f"API error resolving handle {handle}: {e}")
        return None

    def _resolve_by_username(self, username: str) -> Optional[str]:
        """Resolve legacy username or custom URL to channel ID."""
        try:
            resp = self.youtube.channels().list(
                part='id',
                forUsername=username
            ).execute()
            items = resp.get('items', [])
            if items:
                return items[0]['id']
        except HttpError as e:
            logger.error(f"API error resolving username {username}: {e}")
        return None

    # ──────────────────────────────────────────────────────────────────────────
    # Channel metadata
    # ──────────────────────────────────────────────────────────────────────────

    def get_channel_info(self, channel_id: str) -> Optional[dict]:
        """
        Fetch channel metadata.
        Returns a flat dict or None on error.
        """
        try:
            resp = self.youtube.channels().list(
                part='snippet,statistics,contentDetails',
                id=channel_id
            ).execute()
        except HttpError as e:
            self._handle_http_error(e, context=f"channel {channel_id}")
            return None

        items = resp.get('items', [])
        if not items:
            logger.warning(f"No channel found for ID: {channel_id}")
            return None

        item      = items[0]
        snippet   = item.get('snippet', {})
        stats     = item.get('statistics', {})
        content   = item.get('contentDetails', {})

        uploads_playlist = (
            content.get('relatedPlaylists', {}).get('uploads', '')
        )

        return {
            # ── API fields ──────────────────────────────────────────────────
            'channel_id':          channel_id,
            'channel_title':       snippet.get('title', ''),
            'niche':               'Tech devices and computer peripherals',
            'description':         snippet.get('description', ''),
            'country':             snippet.get('country', ''),
            'published_at':        snippet.get('publishedAt', ''),
            'subscriber_count':    int(stats.get('subscriberCount', 0) or 0),
            'total_views':         int(stats.get('viewCount', 0) or 0),
            'video_count':         int(stats.get('videoCount', 0) or 0),
            'uploads_playlist_id': uploads_playlist,
            # ── will be filled by parser later ─────────────────────────────
            'data_source':         'YouTube Data API v3',
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Video collection via uploads playlist
    # ──────────────────────────────────────────────────────────────────────────

    def get_latest_video_ids(self, uploads_playlist_id: str, max_videos: int = 50) -> list[str]:
        """
        Page through the uploads playlist and return up to max_videos video IDs.
        Uses playlistItems.list (1 quota unit per page).
        """
        video_ids = []
        next_page_token = None

        while len(video_ids) < max_videos:
            batch_size = min(50, max_videos - len(video_ids))
            try:
                resp = self.youtube.playlistItems().list(
                    part='contentDetails',
                    playlistId=uploads_playlist_id,
                    maxResults=batch_size,
                    pageToken=next_page_token
                ).execute()
            except HttpError as e:
                self._handle_http_error(e, context=f"playlist {uploads_playlist_id}")
                break

            for item in resp.get('items', []):
                vid = item.get('contentDetails', {}).get('videoId')
                if vid:
                    video_ids.append(vid)

            next_page_token = resp.get('nextPageToken')
            if not next_page_token:
                break

        return video_ids[:max_videos]

    # ──────────────────────────────────────────────────────────────────────────
    # Video details (stats + snippet) in batches of 50
    # ──────────────────────────────────────────────────────────────────────────

    def get_video_details(self, video_ids: list[str], channel_id: str) -> list[dict]:
        """
        Fetch full details for a list of video IDs.
        Batches requests to stay within API limits (50 IDs per call).
        Returns list of flat video dicts.
        """
        results = []
        for i in range(0, len(video_ids), 50):
            batch = video_ids[i:i + 50]
            try:
                resp = self.youtube.videos().list(
                    part='snippet,statistics,contentDetails',
                    id=','.join(batch)
                ).execute()
            except HttpError as e:
                self._handle_http_error(e, context=f"videos batch {i}")
                continue

            for item in resp.get('items', []):
                vid = self._parse_video_item(item, channel_id)
                if vid:
                    results.append(vid)

        return results

    def _parse_video_item(self, item: dict, channel_id: str) -> Optional[dict]:
        """Parse a single video API item into a flat dict."""
        try:
            vid_id  = item.get('id', '')
            snippet = item.get('snippet', {})
            stats   = item.get('statistics', {})
            content = item.get('contentDetails', {})

            iso_dur  = content.get('duration', '')
            dur_human, dur_sec = parse_iso_duration(iso_dur)

            tags = snippet.get('tags', [])

            return {
                # ── identification ─────────────────────────────────────────
                'channel_id':       channel_id,
                'video_id':         vid_id,
                'video_url':        f'https://www.youtube.com/watch?v={vid_id}',
                # ── metadata (API) ─────────────────────────────────────────
                'title':            snippet.get('title', ''),
                'published_at':     snippet.get('publishedAt', ''),
                'duration':         dur_human,
                'duration_seconds': dur_sec,
                'tags':             '|'.join(tags),
                'description':      snippet.get('description', ''),
                # ── statistics (API) ───────────────────────────────────────
                'view_count':       int(stats.get('viewCount', 0) or 0),
                'like_count':       int(stats.get('likeCount', 0) or 0),
                'comment_count':    int(stats.get('commentCount', 0) or 0),
                'data_source':      'YouTube Data API v3',
            }
        except Exception as e:
            logger.error(f"Error parsing video item: {e}")
            return None

    # ──────────────────────────────────────────────────────────────────────────
    # Error handling
    # ──────────────────────────────────────────────────────────────────────────

    def _handle_http_error(self, error: HttpError, context: str = ''):
        """Log meaningful messages for common API errors."""
        code = error.resp.status
        if code == 403:
            logger.error(
                f"[{context}] 403 Forbidden — likely quota exceeded or API key invalid. "
                f"Details: {error}"
            )
        elif code == 404:
            logger.warning(f"[{context}] 404 Not Found — resource may be deleted or private.")
        elif code == 400:
            logger.error(f"[{context}] 400 Bad Request — check parameters. Details: {error}")
        else:
            logger.error(f"[{context}] HTTP {code}: {error}")
