#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import datetime
import time
import re
import webbrowser
import pandas as pd
from config import load_api_key

# ----------------------------
# Helper functions
# ----------------------------

YOUTUBE_VIDEO_URL = "https://www.youtube.com/watch?v={id}"
YOUTUBE_API_SEARCH = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_API_VIDEOS = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_API_CHANNELS = "https://www.googleapis.com/youtube/v3/channels"

def extract_channel_id_from_url(url_or_id: str) -> str:
    """
    Accepts:
      - a channel ID (starts with UC...)
      - a channel URL (https://www.youtube.com/channel/UC...)
      - a user or custom URL (https://www.youtube.com/c/SomeName) [falls back to API lookup]
    Returns channelId or raises ValueError if can't find.
    """
    text = url_or_id.strip()
    if text.startswith("UC") and len(text) > 20:
        return text
    # try channel URL pattern
    m = re.search(r"(?:youtube\.com\/channel\/)([A-Za-z0-9_\-]+)", text)
    if m:
        return m.group(1)
    # if it's a /user/ or /c/, return as-is and let API resolve
    m2 = re.search(r"(?:youtube\.com\/(?:user|c)\/)([^\/\?\&]+)", text)
    if m2:
        return text  # will resolve below
    # maybe user pasted full url with query or short url
    # If none matched, return as-is (might be the channel id)
    return text

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

def parse_iso8601_duration(dur: str) -> int:
    """
    Parse ISO 8601 duration (e.g., PT1H2M20S) and return seconds.
    Simple parser without external libs.
    """
    if not dur:
        return 0
    # regex to capture hours/minutes/seconds
    pattern = re.compile(r'P(?:(?P<days>\d+)D)?T?(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?')
    m = pattern.match(dur)
    if not m:
        return 0
    parts = m.groupdict()
    seconds = int(parts.get("days") or 0) * 86400 + int(parts.get("hours") or 0) * 3600 + int(parts.get("minutes") or 0) * 60 + int(parts.get("seconds") or 0)
    return seconds

def iso8601_to_datetime(s: str) -> datetime.datetime:
    # Example: 2021-08-03T15:30:20Z
    return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))

def safe_int(x):
    try:
        return int(x)
    except Exception:
        return None

def sanitize_filename(name: str) -> str:
    """Remove invalid characters from filename, handling Unicode properly"""
    if not name:
        return "youtube_data"
    # Ensure we have a Unicode string
    name = str(name)
    # Replace invalid characters with underscore (Windows filename restrictions)
    invalid_chars = '<>:"/\\|?*\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f'
    for char in invalid_chars:
        name = name.replace(char, '_')
    # Remove leading/trailing spaces and dots
    name = name.strip('. ')
    # Limit length to avoid Windows path issues (max 255 chars for filename)
    if len(name) > 200:
        name = name[:200]
    # Ensure name is not empty after sanitization
    if not name:
        return "youtube_data"
    return name

# ----------------------------
# YouTube API functions
# ----------------------------

def fetch_video_ids_for_channel(api_key: str, channel_id: str, published_after_iso: str) -> list:
    """
    Uses search.list to fetch video IDs for a channel after publishedAfter date.
    Returns list of video IDs (strings).
    """
    video_ids = []
    params = {
        "part": "id",
        "channelId": channel_id,
        "maxResults": 50,
        "order": "date",
        "publishedAfter": published_after_iso,
        "type": "video",
        "key": api_key
    }
    next_page_token = None
    while True:
        if next_page_token:
            params["pageToken"] = next_page_token
        r = requests.get(YOUTUBE_API_SEARCH, params=params)
        if not r.ok:
            raise RuntimeError(f"Search API error: {r.status_code} - {r.text}")
        r.encoding = 'utf-8'  # Ensure UTF-8 encoding
        js = r.json()
        items = js.get("items", [])
        for it in items:
            vid = it["id"].get("videoId")
            if vid:
                video_ids.append(vid)
        next_page_token = js.get("nextPageToken")
        if not next_page_token:
            break
        # small sleep to be polite with quota
        time.sleep(0.1)
    return video_ids

def chunked(iterable, n):
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
            raise RuntimeError(f"Videos API error: {r.status_code} - {r.text}")
        r.encoding = 'utf-8'  # Ensure UTF-8 encoding
        js = r.json()
        items = js.get("items", [])
        all_items.extend(items)
        time.sleep(0.1)
    return all_items

def get_channel_title(api_key: str, channel_id: str) -> str:
    params = {"part": "snippet", "id": channel_id, "key": api_key}
    r = requests.get(YOUTUBE_API_CHANNELS, params=params)
    if r.ok:
        r.encoding = 'utf-8'  # Ensure UTF-8 encoding
        js = r.json()
        items = js.get("items", [])
        if items:
            return items[0]["snippet"].get("title", "")
    return ""

# ----------------------------
# Analysis conversion
# ----------------------------

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

# ----------------------------
# Tkinter GUI
# ----------------------------

class YouTubeAnalyzerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Channel Analyzer - EdTech Research Tool")
        self.geometry("1100x650")
        self.minsize(900, 500)
        self.df = None
        self.channel_id = None
        self.channel_title = None
        self.create_widgets()

    def create_widgets(self):
        frm_inputs = ttk.Frame(self, padding=8)
        frm_inputs.pack(fill=tk.X, padx=6, pady=6)

        ttk.Label(frm_inputs, text="YouTube API Key:").grid(row=0, column=0, sticky=tk.W)
        self.api_key_var = tk.StringVar(value=load_api_key())
        self.entry_api = ttk.Entry(frm_inputs,textvariable=self.api_key_var, width=64)
        self.entry_api.grid(row=0, column=1, columnspan=3, sticky=tk.W, padx=4)

        ttk.Label(frm_inputs, text="Channel ID / URL:").grid(row=1, column=0, sticky=tk.W, pady=(6,0))
        self.entry_channel = ttk.Entry(frm_inputs, width=64)
        self.entry_channel.grid(row=1, column=1, columnspan=3, sticky=tk.W, padx=4, pady=(6,0))

        ttk.Label(frm_inputs, text="Date Range:").grid(row=2, column=0, sticky=tk.W, pady=(8,0))
        self.range_var = tk.StringVar(value="1m")
        rb1 = ttk.Radiobutton(frm_inputs, text="Last 1 month", variable=self.range_var, value="1m", command=self.on_range_change)
        rb2 = ttk.Radiobutton(frm_inputs, text="Last 2 months", variable=self.range_var, value="2m", command=self.on_range_change)
        rb3 = ttk.Radiobutton(frm_inputs, text="Last 5 months", variable=self.range_var, value="5m", command=self.on_range_change)
        rb4 = ttk.Radiobutton(frm_inputs, text="Custom", variable=self.range_var, value="custom", command=self.on_range_change)
        rb1.grid(row=2, column=1, sticky=tk.W)
        rb2.grid(row=2, column=2, sticky=tk.W)
        rb3.grid(row=2, column=3, sticky=tk.W)
        rb4.grid(row=2, column=4, sticky=tk.W)

        # Custom date range inputs
        ttk.Label(frm_inputs, text="From (YYYY-MM-DD):").grid(row=3, column=0, sticky=tk.W, pady=(6,0))
        self.entry_from = ttk.Entry(frm_inputs, width=18, state="disabled")
        self.entry_from.grid(row=3, column=1, sticky=tk.W, pady=(6,0))
        ttk.Label(frm_inputs, text="To (YYYY-MM-DD):").grid(row=3, column=2, sticky=tk.W, pady=(6,0))
        self.entry_to = ttk.Entry(frm_inputs, width=18, state="disabled")
        self.entry_to.grid(row=3, column=3, sticky=tk.W, pady=(6,0))

        # Buttons
        btn_fetch = ttk.Button(frm_inputs, text="Fetch Videos", command=self.on_fetch)
        btn_fetch.grid(row=4, column=1, pady=10, sticky=tk.W)
        btn_export = ttk.Button(frm_inputs, text="Export CSV", command=self.on_export)
        btn_export.grid(row=4, column=2, pady=10, sticky=tk.W)
        btn_open = ttk.Button(frm_inputs, text="Open Selected Video", command=self.on_open_video)
        btn_open.grid(row=4, column=3, pady=10, sticky=tk.W)

        # Status label
        self.status_var = tk.StringVar(value="Idle")
        ttk.Label(frm_inputs, textvariable=self.status_var).grid(row=5, column=0, columnspan=5, sticky=tk.W)

        # Treeview for results
        columns = ("video_id", "title", "viewCount", "likeCount", "commentCount", "publishDate", "avgViewsPerDay", "likeToViewRatio", "commentToViewRatio", "durationSeconds", "tags")
        frm_table = ttk.Frame(self)
        frm_table.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0,6))

        self.tree = ttk.Treeview(frm_table, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_by(c, False))
            # adjust width heuristically
            w = 120 if col in ("title", "tags") else 100
            self.tree.column(col, width=w, anchor=tk.W)
        vsb = ttk.Scrollbar(frm_table, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(frm_table, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        frm_table.grid_rowconfigure(0, weight=1)
        frm_table.grid_columnconfigure(0, weight=1)

        # Tooltip / help
        help_text = ("Notes: Dislike count is not available via YouTube API.\n"
                     "Make sure your API key has YouTube Data API v3 enabled.\n"
                     "Average views/day uses days since publish (min 1).")
        ttk.Label(self, text=help_text, foreground="gray").pack(side=tk.BOTTOM, anchor=tk.W, padx=6, pady=6)

    def on_range_change(self):
        """Enable/disable date entry fields based on selected range"""
        if self.range_var.get() == "custom":
            self.entry_from.config(state="normal")
            self.entry_to.config(state="normal")
        else:
            self.entry_from.config(state="disabled")
            self.entry_to.config(state="disabled")

    def set_status(self, text):
        self.status_var.set(text)
        self.update_idletasks()

    def on_fetch(self):
        api_key = self.entry_api.get().strip()
        channel_input = self.entry_channel.get().strip()
        if not api_key:
            messagebox.showerror("Missing API Key", "Please enter your YouTube Data API key.")
            return
        if not channel_input:
            messagebox.showerror("Missing Channel", "Please enter a YouTube channel ID or URL.")
            return

        # Determine date range
        rng = self.range_var.get()
        to_date = datetime.datetime.now(datetime.timezone.utc)
        if rng == "1m":
            from_date = to_date - datetime.timedelta(days=30)
        elif rng == "2m":
            from_date = to_date - datetime.timedelta(days=60)
        elif rng == "5m":
            from_date = to_date - datetime.timedelta(days=150)
        else:
            # custom
            fstr = self.entry_from.get().strip()
            tstr = self.entry_to.get().strip()
            try:
                if not fstr:
                    messagebox.showerror("Custom Date", "Please enter From date (YYYY-MM-DD).")
                    return
                from_date = datetime.datetime.fromisoformat(fstr).replace(tzinfo=datetime.timezone.utc)
                if tstr:
                    to_date = datetime.datetime.fromisoformat(tstr).replace(tzinfo=datetime.timezone.utc)
                else:
                    to_date = datetime.datetime.now(datetime.timezone.utc)
            except Exception as e:
                messagebox.showerror("Date parse error", f"Could not parse dates: {e}")
                return
        # convert to RFC3339 ISO for API
        published_after_iso = from_date.isoformat().replace("+00:00", "Z")
        # Resolve channel ID
        self.set_status("Resolving channel ID...")
        try:
            maybe = extract_channel_id_from_url(channel_input)
            channel_id = resolve_channel_id(api_key, maybe)
            self.channel_id = channel_id
        except Exception as e:
            messagebox.showerror("Channel Resolution Error", f"Could not resolve channel ID: {e}")
            self.set_status("Idle")
            return
        self.set_status(f"Fetching videos for channel {channel_id} since {published_after_iso} ...")
        try:
            video_ids = fetch_video_ids_for_channel(api_key, channel_id, published_after_iso)
        except Exception as e:
            messagebox.showerror("API Error", f"Error fetching video IDs: {e}")
            self.set_status("Idle")
            return
        if not video_ids:
            messagebox.showinfo("No videos", "No videos found for the specified range.")
            self.tree.delete(*self.tree.get_children())
            self.df = None
            self.set_status("Idle")
            return
        self.set_status(f"Found {len(video_ids)} videos. Fetching details...")
        try:
            items = fetch_videos_details(api_key, video_ids)
        except Exception as e:
            messagebox.showerror("API Error", f"Error fetching video details: {e}")
            self.set_status("Idle")
            return
        self.set_status("Processing data...")
        df = items_to_dataframe(items)
        # optionally filter to <= to_date just in case
        if "publishDate" in df.columns and df["publishDate"].notna().any():
            try:
                df["publish_dt_obj"] = pd.to_datetime(df["publishDate"], utc=True)
                df = df[(df["publish_dt_obj"] <= to_date)]
                df = df.drop(columns=["publish_dt_obj"])
            except Exception:
                pass
        self.df = df.sort_values(by="publishDate", ascending=False).reset_index(drop=True)
        self._populate_tree(self.df)
        ch_title = get_channel_title(api_key, channel_id)
        self.channel_title = ch_title
        pretty_name = f"{ch_title} ({channel_id})" if ch_title else channel_id
        self.set_status(f"Loaded {len(self.df)} videos for {pretty_name} — ready.")

    def _populate_tree(self, df: pd.DataFrame):
        self.tree.delete(*self.tree.get_children())
        # Insert rows
        for idx, row in df.iterrows():
            vals = (
                row.get("video_id"),
                (row.get("title")[:120] + "...") if row.get("title") and len(row.get("title"))>120 else row.get("title"),
                row.get("viewCount"),
                row.get("likeCount"),
                row.get("commentCount"),
                row.get("publishDate"),
                round(row.get("avgViewsPerDay"),2) if row.get("avgViewsPerDay") is not None else None,
                round(row.get("likeToViewRatio"),4) if row.get("likeToViewRatio") is not None else None,
                round(row.get("commentToViewRatio"),4) if row.get("commentToViewRatio") is not None else None,
                row.get("durationSeconds"),
                (row.get("tags")[:80] + "...") if row.get("tags") and len(row.get("tags"))>80 else row.get("tags"),
            )
            self.tree.insert("", tk.END, values=vals)

    def on_export(self):
        if self.df is None or self.df.empty:
            messagebox.showinfo("No data", "No data to export. Fetch videos first.")
            return
        
        # Generate default filename from channel title or ID
        if self.channel_title:
            default_name = sanitize_filename(self.channel_title)
        elif self.channel_id:
            default_name = self.channel_id
        else:
            default_name = "youtube_data"
        
        default_name += ".csv"
        
        fname = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=default_name,
            filetypes=[("CSV files","*.csv"),("All files","*.*")]
        )
        if not fname:
            return
        try:
            # Save df to CSV with UTF-8 BOM for Excel compatibility on Windows
            self.df.to_csv(fname, index=False, encoding="utf-8-sig")
            messagebox.showinfo("Exported", f"Saved CSV to: {fname}")
        except Exception as e:
            messagebox.showerror("Export error", f"Could not save file: {e}")

    def on_open_video(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Select video", "Select a video row and click Open Selected Video.")
            return
        vid_id = self.tree.item(sel[0])["values"][0]
        if not vid_id:
            messagebox.showerror("No video id", "Selected row has no video id.")
            return
        url = YOUTUBE_VIDEO_URL.format(id=vid_id)
        webbrowser.open(url)

    def sort_by(self, col, descending):
        # Adapted sorting for displayed columns
        data = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]
        # try numeric sort
        try:
            data = [(float(d[0]) if d[0] not in (None, "") else float('-inf'), d[1]) for d in data]
        except Exception:
            pass
        data.sort(reverse=descending)
        for index, item in enumerate(data):
            self.tree.move(item[1], '', index)
        # reverse sort next time
        self.tree.heading(col, command=lambda c=col: self.sort_by(c, not descending))

# ----------------------------
# Run
# ----------------------------

def main():
    app = YouTubeAnalyzerApp()
    app.mainloop()

if __name__ == "__main__":
    main()