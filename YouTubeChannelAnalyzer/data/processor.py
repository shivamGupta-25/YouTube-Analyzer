#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Data processing functions for YouTube video analysis.
"""

import datetime
import pandas as pd
from utils.helpers import parse_iso8601_duration, iso8601_to_datetime, safe_int
from api.youtube_api import YOUTUBE_VIDEO_URL


def items_to_dataframe(items: list) -> pd.DataFrame:
    """
    Convert video items (videos.list response) into a pandas DataFrame with computed metrics.
    """
    rows = []
    now = datetime.datetime.now(datetime.timezone.utc)
    for it in items:
        snip = it.get("snippet", {})
        stats = it.get("statistics", {})
        content = it.get("contentDetails", {})
        video_id = it.get("id")
        # Ensure Unicode strings are properly handled
        title = str(snip.get("title", "")) if snip.get("title") else ""
        description = str(snip.get("description", "")) if snip.get("description") else ""
        publish_str = snip.get("publishedAt")
        try:
            publish_dt = iso8601_to_datetime(publish_str) if publish_str else None
        except Exception:
            publish_dt = None
        duration_iso = content.get("duration")
        duration_seconds = parse_iso8601_duration(duration_iso)
        category_id = snip.get("categoryId")
        # Ensure tags are Unicode strings
        tags = [str(tag) if tag else "" for tag in snip.get("tags", [])]
        thumbnail = snip.get("thumbnails", {}).get("high", {}).get("url") or snip.get("thumbnails", {}).get("default", {}).get("url")
        view_count = safe_int(stats.get("viewCount"))
        like_count = safe_int(stats.get("likeCount"))
        # dislikeCount no longer available
        comment_count = safe_int(stats.get("commentCount"))

        # compute days since publish (using fractional days for accuracy)
        days_since = None
        if publish_dt:
            delta = now - publish_dt
            # Use total_seconds for fractional days to get accurate avgViewsPerDay
            # Minimum 0.1 days (2.4 hours) to avoid division by zero and handle very recent videos
            days_since = max(0.1, delta.total_seconds() / 86400)
        avg_views_per_day = None
        if view_count is not None and days_since is not None:
            avg_views_per_day = view_count / days_since
        like_to_view = None
        if like_count is not None and view_count is not None and view_count > 0:
            like_to_view = like_count / view_count
        comment_to_view = None
        if comment_count is not None and view_count is not None and view_count > 0:
            comment_to_view = comment_count / view_count

        rows.append({
            "video_id": video_id,
            "title": title,
            "description": description,
            "viewCount": view_count,
            "likeCount": like_count,
            "commentCount": comment_count,
            "publishDate": publish_dt.isoformat() if publish_dt else None,
            "daysSincePublish": days_since,
            "avgViewsPerDay": avg_views_per_day,
            "likeToViewRatio": like_to_view,
            "commentToViewRatio": comment_to_view,
            "durationSeconds": duration_seconds,
            "categoryId": category_id,
            "tags": ",".join(tags) if tags else "",
            "thumbnailUrl": thumbnail,
            "videoUrl": YOUTUBE_VIDEO_URL.format(id=video_id)
        })
    df = pd.DataFrame(rows)
    return df
