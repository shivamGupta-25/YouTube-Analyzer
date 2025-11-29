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

        # Calculate Overall Engagement Rate (%)
        # Total interactions (likes + comments) divided by views
        engagement_rate = None
        if view_count is not None and view_count > 0:
            total_interactions = (like_count or 0) + (comment_count or 0)
            engagement_rate = (total_interactions / view_count) * 100

        # Calculate Engagement Score (1-10 scale)
        # Weighted formula combining multiple engagement signals
        engagement_score = None
        if like_to_view is not None or comment_to_view is not None:
            # Use 0 as default if a ratio is None
            like_ratio = like_to_view if like_to_view is not None else 0
            comment_ratio = comment_to_view if comment_to_view is not None else 0
            
            # Velocity component: normalize avgViewsPerDay (cap at 1000 views/day = max score)
            velocity_score = 0
            if avg_views_per_day is not None:
                velocity_score = min(avg_views_per_day / 1000, 1.0)
            
            # Weighted formula (scale 0-1, then convert to 1-10)
            # 50% weight on likes, 30% on comments, 20% on velocity
            raw_score = (
                (like_ratio * 50) +
                (comment_ratio * 30) +
                (velocity_score * 20)
            )
            
            # Convert to 1-10 scale
            # Multiply by 100 to get 0-100 range, then divide by 10 to get 1-10
            # Add 1 to ensure minimum score is 1 (not 0)
            engagement_score = min(max((raw_score * 100) / 10, 1.0), 10.0)


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
            "engagementRate": engagement_rate,
            "engagementScore": engagement_score,
            "durationSeconds": duration_seconds,
            "categoryId": category_id,
            "tags": ",".join(tags) if tags else "",
            "thumbnailUrl": thumbnail,
            "videoUrl": YOUTUBE_VIDEO_URL.format(id=video_id)
        })
    df = pd.DataFrame(rows)
    return df
