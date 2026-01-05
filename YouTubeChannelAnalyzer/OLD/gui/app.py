#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tkinter GUI application for YouTube Channel Analyzer.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import datetime
import webbrowser
import pandas as pd

from config import load_api_key
from utils.helpers import extract_channel_id_from_url, sanitize_filename
from api.youtube_api import (
    resolve_channel_id,
    fetch_video_ids_for_channel,
    fetch_videos_details,
    get_channel_title,
    YOUTUBE_VIDEO_URL,
    APIError  # Import custom exception
)
from data.processor import items_to_dataframe


class YouTubeAnalyzerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Channel Analyzer - EdTech Research Tool")
        self.geometry("1200x700")
        self.minsize(1000, 600)
        self.df = None
        self.channel_id = None
        self.channel_title = None
        self.create_widgets()

    def create_widgets(self):
        # Main container with padding
        main_container = ttk.Frame(self, padding="10")
        main_container.pack(fill=tk.BOTH, expand=True)

        # ===== CONFIGURATION SECTION =====
        config_frame = ttk.LabelFrame(main_container, text="Configuration", padding="10")
        config_frame.pack(fill=tk.X, padx=5, pady=5)

        # API Key
        ttk.Label(config_frame, text="YouTube API Key:", font=('', 9, 'bold')).grid(
            row=0, column=0, sticky=tk.W, padx=(0, 10), pady=5
        )
        self.api_key_var = tk.StringVar(value=load_api_key())
        self.entry_api = ttk.Entry(config_frame, textvariable=self.api_key_var, show="*")
        self.entry_api.grid(row=0, column=1, columnspan=3, sticky=(tk.W, tk.E), pady=5, padx=(0, 5))

        # Channel Input
        ttk.Label(config_frame, text="Channel ID / URL / Username:", font=('', 9, 'bold')).grid(
            row=1, column=0, sticky=tk.W, padx=(0, 10), pady=5
        )
        self.entry_channel = ttk.Entry(config_frame)
        self.entry_channel.grid(row=1, column=1, columnspan=3, sticky=(tk.W, tk.E), pady=5, padx=(0, 5))

        # Help text for channel input
        # help_channel = ttk.Label(
        #     config_frame,
        #     text="Accepts: Channel ID (UC...), Full URL, Custom URL (/c/...), User URL (/user/...), or Username",
        #     foreground="gray",
        #     font=('', 8)
        # )
        # help_channel.grid(row=2, column=1, columnspan=3, sticky=tk.W, pady=(0, 5))

        # Make column 1 expandable
        config_frame.columnconfigure(1, weight=1)

        # ===== DATE RANGE SECTION =====
        date_frame = ttk.LabelFrame(main_container, text="Date Range", padding="10")
        date_frame.pack(fill=tk.X, padx=5, pady=5)

        # Preset ranges
        preset_frame = ttk.Frame(date_frame)
        preset_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(preset_frame, text="Preset Ranges:", font=('', 9, 'bold')).pack(side=tk.LEFT, padx=(0, 15))

        self.range_var = tk.StringVar(value="1m")
        ttk.Radiobutton(preset_frame, text="Last 1 Month", variable=self.range_var, value="1m", command=self.on_range_change).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(preset_frame, text="Last 2 Months", variable=self.range_var, value="2m", command=self.on_range_change).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(preset_frame, text="Last 5 Months", variable=self.range_var, value="5m", command=self.on_range_change).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(preset_frame, text="Custom Range", variable=self.range_var, value="custom", command=self.on_range_change).pack(side=tk.LEFT, padx=5)

        # Custom date range
        custom_frame = ttk.Frame(date_frame)
        custom_frame.pack(fill=tk.X)

        ttk.Label(custom_frame, text="Custom Range:", font=('', 9, 'bold')).grid(row=0, column=0, sticky=tk.W, padx=(0, 15))
        ttk.Label(custom_frame, text="From (YYYY-MM-DD):").grid(row=0, column=1, sticky=tk.W, padx=5)
        self.entry_from = ttk.Entry(custom_frame, state="disabled")
        self.entry_from.grid(row=0, column=2, padx=5, sticky=(tk.W, tk.E))
        ttk.Label(custom_frame, text="To (YYYY-MM-DD):").grid(row=0, column=3, sticky=tk.W, padx=5)
        self.entry_to = ttk.Entry(custom_frame, state="disabled")
        self.entry_to.grid(row=0, column=4, padx=5, sticky=(tk.W, tk.E))
        
        # Make date entry columns expandable
        custom_frame.columnconfigure(2, weight=1)
        custom_frame.columnconfigure(4, weight=1)

        # ===== ACTIONS SECTION =====
        actions_frame = ttk.Frame(main_container)
        actions_frame.pack(fill=tk.X, padx=5, pady=10)

        # Buttons with better styling
        btn_frame = ttk.Frame(actions_frame)
        btn_frame.pack(side=tk.LEFT)

        ttk.Button(btn_frame, text="🔍 Fetch Videos", command=self.on_fetch, width=18).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="💾 Export to CSV", command=self.on_export, width=18).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🎬 Open Selected Video", command=self.on_open_video, width=22).pack(side=tk.LEFT, padx=5)

        # Status label
        status_frame = ttk.Frame(actions_frame)
        status_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(20, 0))

        ttk.Label(status_frame, text="Status:", font=('', 9, 'bold')).pack(side=tk.LEFT, padx=(0, 5))
        self.status_var = tk.StringVar(value="Idle")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, foreground="blue", font=('', 9))
        status_label.pack(side=tk.LEFT)

        # ===== FOOTER INFO =====
        # Pack footer BEFORE results so it stays visible at bottom
        footer_frame = ttk.Frame(main_container)
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=(5, 0))

        info_text = "ℹ️ Note: Dislike count is not available via YouTube API. Ensure your API key has YouTube Data API v3 enabled."
        ttk.Label(footer_frame, text=info_text, foreground="gray", font=('', 8)).pack(side=tk.LEFT)

        # ===== RESULTS SECTION =====
        results_frame = ttk.LabelFrame(main_container, text="Video Results", padding="5")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Treeview for results
        columns = ("video_id", "title", "viewCount", "likeCount", "commentCount", "publishDate", 
                   "avgViewsPerDay", "likeToViewRatio", "commentToViewRatio", "engagementRate", 
                   "engagementScore", "durationStr", "tags")
        
        # Create treeview with scrollbars
        tree_container = ttk.Frame(results_frame)
        tree_container.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(tree_container, columns=columns, show="headings", height=15)
        
        # Configure columns with responsive widths
        column_config = {
            "video_id": ("Video ID", 100, 80),
            "title": ("Title", 250, 150),
            "viewCount": ("Views", 80, 60),
            "likeCount": ("Likes", 80, 60),
            "commentCount": ("Comments", 80, 60),
            "publishDate": ("Published", 150, 100),
            "avgViewsPerDay": ("Avg Views/Day", 100, 80),
            "likeToViewRatio": ("Like Ratio", 80, 70),
            "commentToViewRatio": ("Comment Ratio", 100, 80),
            "engagementRate": ("Engagement %", 100, 80),
            "engagementScore": ("Score (1-10)", 90, 80),
            "durationStr": ("Duration", 90, 70),
            "tags": ("Tags", 150, 100)
        }
        
        for col, (heading, width, minwidth) in column_config.items():
            self.tree.heading(col, text=heading, command=lambda c=col: self.sort_by(c, False))
            self.tree.column(col, width=width, minwidth=minwidth, anchor=tk.W, stretch=True)

        # Scrollbars
        vsb = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

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
            messagebox.showerror("Missing Channel", "Please enter a YouTube channel ID, URL, or username.")
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
                    messagebox.showerror(
                        "Missing Start Date",
                        "Please enter a start date (From field).\n\n"
                        "Format: YYYY-MM-DD\n"
                        "Example: 2024-01-15"
                    )
                    return
                from_date = datetime.datetime.fromisoformat(fstr).replace(tzinfo=datetime.timezone.utc)
                if tstr:
                    # Parse 'to' date and set it to end of day (23:59:59) for inclusivity
                    base_to = datetime.datetime.fromisoformat(tstr)
                    to_date = base_to.replace(hour=23, minute=59, second=59, tzinfo=datetime.timezone.utc)
                    # Validate date range
                    if to_date < from_date:
                        messagebox.showerror(
                            "Invalid Date Range",
                            "End date must be after start date.\n\n"
                            f"From: {fstr}\n"
                            f"To: {tstr}"
                        )
                        return
                else:
                    to_date = datetime.datetime.now(datetime.timezone.utc)
            except ValueError as e:
                messagebox.showerror(
                    "Invalid Date Format",
                    "Please use YYYY-MM-DD format.\n\n"
                    "Examples:\n"
                    "• 2024-01-15\n"
                    "• 2024-12-31\n\n"
                    f"Error: {str(e)}"
                )
                return
            except Exception as e:
                messagebox.showerror("Date Error", f"Could not parse dates: {e}")
                return
        # convert to RFC3339 ISO for API
        # convert to RFC3339 ISO for API
        # Use timespec='seconds' to strip microseconds which API might reject
        published_after_iso = from_date.isoformat(timespec='seconds').replace("+00:00", "Z")
        published_before_iso = to_date.isoformat(timespec='seconds').replace("+00:00", "Z")
        
        # Resolve channel ID
        self.set_status("Resolving channel ID...")
        try:
            maybe = extract_channel_id_from_url(channel_input)
            channel_id = resolve_channel_id(api_key, maybe)
            self.channel_id = channel_id
        except APIError as e:
            messagebox.showerror(
                f"API Error: {e.error_type.replace('_', ' ').title()}",
                e.user_message
            )
            self.set_status(f"Error: {e.technical_details}")
            return
        except ValueError as e:
            messagebox.showerror(
                "Channel Not Found",
                f"{str(e)}\n\n"
                "Supported formats:\n"
                "• Channel ID: UCxxx...\n"
                "• Channel URL: youtube.com/channel/UCxxx...\n"
                "• Custom URL: youtube.com/c/ChannelName\n"
                "• Username: youtube.com/user/Username"
            )
            self.set_status("Idle")
            return
        except Exception as e:
            messagebox.showerror(
                "Channel Resolution Error",
                f"Could not resolve channel ID.\n\n"
                f"Error: {str(e)}\n\n"
                "Please check your internet connection and try again."
            )
            self.set_status("Idle")
            return
        self.set_status(f"Fetching videos for channel {channel_id} from {published_after_iso} to {published_before_iso}...")
        try:
            video_ids = fetch_video_ids_for_channel(api_key, channel_id, published_after_iso, published_before_iso)
        except APIError as e:
            messagebox.showerror(
                f"API Error: {e.error_type.replace('_', ' ').title()}",
                e.user_message
            )
            self.set_status(f"Error: {e.technical_details}")
            return
        except Exception as e:
            messagebox.showerror(
                "Unexpected Error",
                f"An unexpected error occurred while fetching videos.\n\n"
                f"Error: {str(e)}\n\n"
                "Please check your internet connection and try again."
            )
            self.set_status("Error occurred")
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
        except APIError as e:
            messagebox.showerror(
                f"API Error: {e.error_type.replace('_', ' ').title()}",
                e.user_message
            )
            self.set_status(f"Error: {e.technical_details}")
            return
        except Exception as e:
            messagebox.showerror(
                "Unexpected Error",
                f"An unexpected error occurred while fetching video details.\n\n"
                f"Error: {str(e)}\n\n"
                "Please check your internet connection and try again."
            )
            self.set_status("Error occurred")
            return
        self.set_status("Processing data...")
        df = items_to_dataframe(items)
        # No need for client-side date filtering anymore - API handles it
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
                round(row.get("engagementRate"),2) if row.get("engagementRate") is not None else None,
                round(row.get("engagementScore"),2) if row.get("engagementScore") is not None else None,
                row.get("durationStr"),
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
            messagebox.showinfo("Export Successful", f"✅ Data saved successfully!\n\nLocation:\n{fname}")
        except PermissionError:
            messagebox.showerror(
                "Permission Denied",
                "💾 Cannot write to file.\n\n"
                "Possible causes:\n"
                "• File is open in another program (close Excel/CSV viewer)\n"
                "• No write permission for this folder\n"
                "• Disk is full or write-protected\n\n"
                "Try:\n"
                "• Close the file if it's open\n"
                "• Save to a different location (e.g., Desktop)"
            )
        except Exception as e:
            messagebox.showerror(
                "Export Failed",
                f"❌ Could not save file.\n\n"
                f"Error: {str(e)}\n\n"
                "Try saving to a different location (e.g., Desktop)."
            )

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
