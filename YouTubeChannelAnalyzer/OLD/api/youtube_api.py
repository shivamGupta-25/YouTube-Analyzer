#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YouTube API interaction functions.
"""

import re
import time
import json
import requests
import datetime


# Custom exception for API errors
class APIError(Exception):
    """Custom exception for YouTube API errors with user-friendly messages."""
    def __init__(self, error_type, user_message, technical_details):
        self.error_type = error_type
        self.user_message = user_message
        self.technical_details = technical_details
        super().__init__(user_message)


# API Endpoints
YOUTUBE_VIDEO_URL = "https://www.youtube.com/watch?v={id}"
YOUTUBE_API_SEARCH = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_API_VIDEOS = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_API_CHANNELS = "https://www.googleapis.com/youtube/v3/channels"
YOUTUBE_API_PLAYLIST_ITEMS = "https://www.googleapis.com/youtube/v3/playlistItems"


def parse_api_error(status_code: int, response_text: str) -> tuple:
    """
    Parse YouTube API error and return user-friendly message.
    Returns: (error_type, user_message, technical_details)
    """
    try:
        error_data = json.loads(response_text)
        error_info = error_data.get("error", {})
        errors_list = error_info.get("errors", [{}])
        reason = errors_list[0].get("reason", "") if errors_list else ""
        message = error_info.get("message", "")
    except:
        reason = ""
        message = response_text[:200]  # Truncate long responses
    
    # Quota exceeded - Most common error
    if status_code == 403 and ("quota" in reason.lower() or "quota" in message.lower()):
        return (
            "quota_exceeded",
            "⚠️ Daily API Quota Exceeded\n\n"
            "YouTube allows 10,000 quota units per day (free tier).\n\n"
            "Solutions:\n"
            "• Wait until tomorrow (quota resets at midnight Pacific Time)\n"
            "• Request quota increase in Google Cloud Console\n"
            "• Reduce date range to fetch fewer videos\n"
            "• Use a different API key if available",
            f"Status: {status_code}, Reason: {reason}"
        )
    
    # Invalid API key
    if status_code == 400 and ("API key" in message or "invalid" in message.lower()):
        return (
            "invalid_api_key",
            "🔑 Invalid API Key\n\n"
            "Please verify:\n"
            "• API key is correct (no extra spaces or characters)\n"
            "• YouTube Data API v3 is enabled in Google Cloud Console\n"
            "• API key restrictions allow YouTube Data API v3\n"
            "• API key hasn't been deleted or disabled",
            f"Status: {status_code}"
        )
    
    # Forbidden/Authentication
    if status_code == 403:
        return (
            "forbidden",
            "🚫 Access Forbidden\n\n"
            "Possible causes:\n"
            "• API key restrictions are blocking this request\n"
            "• YouTube Data API v3 is not enabled\n"
            "• API key may be disabled or deleted\n"
            "• IP address or referrer restrictions",
            f"Status: {status_code}, Message: {message}"
        )
    
    # Not found
    if status_code == 404:
        return (
            "not_found",
            "❌ Resource Not Found\n\n"
            "The channel or video may:\n"
            "• Not exist or have been deleted\n"
            "• Be private or unlisted\n"
            "• Have an incorrect ID",
            f"Status: {status_code}"
        )
    
    # Rate limit (too many requests)
    if status_code == 429:
        return (
            "rate_limit",
            "⏱️ Too Many Requests\n\n"
            "You're making requests too quickly.\n"
            "Please wait a moment and try again.",
            f"Status: {status_code}"
        )
    
    # Bad request
    if status_code == 400:
        return (
            "bad_request",
            "⚠️ Invalid Request\n\n"
            "The request parameters may be incorrect.\n"
            "Please check:\n"
            "• Date format is YYYY-MM-DD\n"
            "• Channel ID is valid\n"
            "• All required fields are filled",
            f"Status: {status_code}, Message: {message}"
        )
    
    # Server errors (500+)
    if status_code >= 500:
        return (
            "server_error",
            "🔧 YouTube Server Error\n\n"
            "This is a temporary issue on YouTube's side.\n"
            "The service should be back shortly.\n\n"
            "Please try again in a few moments.",
            f"Status: {status_code}, Message: {message}"
        )
    
    # Generic error
    return (
        "unknown",
        f"❌ API Request Failed (Status {status_code})\n\n"
        "Please check:\n"
        "• Your internet connection is stable\n"
        "• YouTube API is accessible\n"
        "• Try again in a few moments",
        f"Status: {status_code}, Message: {message}"
    )


def resolve_channel_id(api_key: str, maybe_id_or_url: str) -> str:
    """
    If the input is a raw channel ID -> return it.
    If it's a full URL or a custom name, try to resolve via channels.list for 'forUsername' or 'id' or 'topicDetails'.
    """
    candidate = maybe_id_or_url.strip()
    if candidate.startswith("UC") and len(candidate) > 20:
        return candidate
    # check if URL contains /channel/
    m = re.search(r"(?:youtube\.com\/channel\/)([A-Za-z0-9_\-]+)", candidate)
    if m:
        return m.group(1)

    # try to parse if it is a full URL or custom handle
    # Try to resolve as "forUsername" (older user handles)
    params = {
        "part": "id",
        "key": api_key,
    }
    # Try forUsername attempt if looks like a simple name (no slashes)
    name = candidate
    if "/" not in candidate and "http" not in candidate:
        params["forUsername"] = name
        r = requests.get(YOUTUBE_API_CHANNELS, params=params)
        if r.ok:
            r.encoding = 'utf-8'  # Ensure UTF-8 encoding
            js = r.json()
            if "items" in js and len(js["items"]) > 0:
                return js["items"][0]["id"]
    # As fallback, if input is a full URL (like /c/ or /user/), try to use search endpoint to find channel
    # Use search with type=channel and q=the last path segment
    # Extract the last part
    last_part = candidate.rstrip("/").split("/")[-1]
    if last_part:
        p2 = {
            "part": "snippet",
            "q": last_part,
            "type": "channel",
            "maxResults": 5,
            "key": api_key
        }
        r2 = requests.get(YOUTUBE_API_SEARCH, params=p2)
        if r2.ok:
            r2.encoding = 'utf-8'  # Ensure UTF-8 encoding
            js2 = r2.json()
            items = js2.get("items", [])
            if items:
                # pick top result's channelId
                cid = items[0]["snippet"]["channelId"]
                return cid
    raise ValueError("Could not resolve channel ID. Provide a proper channel ID (starts with 'UC...') or a full channel URL.")


def get_uploads_playlist_id(api_key: str, channel_id: str) -> str:
    """Get the ID of the 'Uploads' playlist for a channel."""
    params = {
        "part": "contentDetails",
        "id": channel_id,
        "key": api_key
    }
    r = requests.get(YOUTUBE_API_CHANNELS, params=params)
    if not r.ok:
        error_type, user_msg, tech_details = parse_api_error(r.status_code, r.text)
        raise APIError(error_type, user_msg, tech_details)
    
    r.encoding = 'utf-8'
    js = r.json()
    items = js.get("items", [])
    if not items:
        # Channel might not exist or be accessible
        raise APIError("not_found", "Channel not found or no access.", f"Channel ID: {channel_id}")
        
    # extract uploads playlist id
    return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]


def fetch_video_ids_for_channel(api_key: str, channel_id: str, published_after_iso: str, published_before_iso: str = None) -> list:
    """
    Uses playlistItems.list (Uploads playlist) to fetch video IDs.
    This is more reliable than search.list and captures all videos.
    
    Args:
        api_key: YouTube Data API key
        channel_id: YouTube channel ID
        published_after_iso: ISO 8601 timestamp for start of range (inclusive)
        published_before_iso: Optional ISO 8601 timestamp for end of range (exclusive)
        
    Returns:
        List of video IDs (strings)
    """
    # 1. Get Uploads Playlist ID
    uploads_id = get_uploads_playlist_id(api_key, channel_id)
    
    video_ids = []
    
    # Parse dates for comparison
    # Helper to parse YYYY-MM-DDTHH:MM:SSZ
    def parse_dt(s):
        # Handle cases with or without Z
        s = s.replace("Z", "+00:00")
        return datetime.datetime.fromisoformat(s)

    dt_after = parse_dt(published_after_iso)
    dt_before = parse_dt(published_before_iso) if published_before_iso else None
    
    params = {
        "part": "contentDetails,snippet",
        "playlistId": uploads_id,
        "maxResults": 50,
        "key": api_key
    }
    
    next_page_token = None
    while True:
        if next_page_token:
            params["pageToken"] = next_page_token
            
        r = requests.get(YOUTUBE_API_PLAYLIST_ITEMS, params=params)
        if not r.ok:
            error_type, user_msg, tech_details = parse_api_error(r.status_code, r.text)
            raise APIError(error_type, user_msg, tech_details)
            
        r.encoding = 'utf-8'
        js = r.json()
        items = js.get("items", [])
        
        if not items:
            break
            
        for it in items:
            # For playlistItems, the date is in snippet.publishedAt or contentDetails.videoPublishedAt
            # We prefer contentDetails.videoPublishedAt if available
            pub_str = it.get("contentDetails", {}).get("videoPublishedAt") or it.get("snippet", {}).get("publishedAt")
            vid = it.get("contentDetails", {}).get("videoId")
            
            if not vid or not pub_str:
                continue
                
            try:
                vid_dt = parse_dt(pub_str)
            except:
                continue
                
            # Logic: Uploads are usually returned newest first.
            # If vid_dt > dt_before, we simply skip this video but continue (it's too new)
            # If vid_dt < dt_after, we stop (it's too old, and since they are ordered, subsequent ones will be older)
            
            if dt_before and vid_dt > dt_before:
                continue
                
            if vid_dt < dt_after:
                # Found a video older than our start date.
                # Since playlist is usually reverse-chronological, we can stop here.
                # However, sometimes order isn't perfect, but for 'Uploads' it's generally reliable.
                # To be safe, we can stop.
                return video_ids
            
            video_ids.append(vid)
            
        next_page_token = js.get("nextPageToken")
        if not next_page_token:
            break
            
        # small sleep to be polite
        time.sleep(0.1)
        
    return video_ids


def chunked(iterable, n):
    """Split an iterable into chunks of size n."""
    for i in range(0, len(iterable), n):
        yield iterable[i:i+n]


def fetch_videos_details(api_key: str, video_ids: list) -> list:
    """
    Fetches videos.list for batches of up to 50 IDs. Returns list of item dicts.
    """
    all_items = []
    for batch in chunked(video_ids, 50):
        params = {
            "part": "snippet,statistics,contentDetails",
            "id": ",".join(batch),
            "key": api_key,
            "maxResults": 50
        }
        r = requests.get(YOUTUBE_API_VIDEOS, params=params)
        if not r.ok:
            error_type, user_msg, tech_details = parse_api_error(r.status_code, r.text)
            raise APIError(error_type, user_msg, tech_details)
        r.encoding = 'utf-8'  # Ensure UTF-8 encoding
        js = r.json()
        items = js.get("items", [])
        all_items.extend(items)
        time.sleep(0.1)
    return all_items


def get_channel_title(api_key: str, channel_id: str) -> str:
    """Get the title of a YouTube channel by its ID."""
    params = {"part": "snippet", "id": channel_id, "key": api_key}
    r = requests.get(YOUTUBE_API_CHANNELS, params=params)
    if r.ok:
        r.encoding = 'utf-8'  # Ensure UTF-8 encoding
        js = r.json()
        items = js.get("items", [])
        if items:
            return items[0]["snippet"].get("title", "")
    return ""
