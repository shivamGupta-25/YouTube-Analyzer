import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from tkcalendar import DateEntry
from googleapiclient.discovery import build
import pandas as pd
import isodate
from datetime import datetime, timedelta
import re
import threading

# --- Configuration & Theme ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class YouTubeDataFetcherApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Modern YouTube Data Extractor")
        self.geometry("900x750")
        self.resizable(True, True)

        # Variables
        self.api_key_var = tk.StringVar()
        self.channel_input_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready")
        self.date_range_mode = tk.StringVar(value="Last 1 Month")
        
        # Layout Grid Config
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0) # Title
        self.grid_rowconfigure(1, weight=0) # Inputs
        self.grid_rowconfigure(2, weight=0) # Date
        self.grid_rowconfigure(3, weight=0) # Progress
        self.grid_rowconfigure(4, weight=1) # Log/Preview

        self._create_widgets()

    def _create_widgets(self):
        # 1. Header
        self.header_frame = ctk.CTkFrame(self, corner_radius=10)
        self.header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        self.title_label = ctk.CTkLabel(
            self.header_frame, 
            text="YouTube Channel Data Extractor", 
            font=("Roboto Medium", 24)
        )
        self.title_label.pack(pady=10)

        # 2. Input Section
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.input_frame.grid_columnconfigure(1, weight=1)

        # API Key
        ctk.CTkLabel(self.input_frame, text="Google API Key:").grid(row=0, column=0, padx=15, pady=15, sticky="w")
        self.entry_api = ctk.CTkEntry(self.input_frame, textvariable=self.api_key_var, placeholder_text="Paste your YouTube Data API v3 Key here", show="*")
        self.entry_api.grid(row=0, column=1, padx=15, pady=15, sticky="ew")

        # Channel ID/URL
        ctk.CTkLabel(self.input_frame, text="Channel (ID/URL/@Handle):").grid(row=1, column=0, padx=15, pady=15, sticky="w")
        self.entry_channel = ctk.CTkEntry(self.input_frame, textvariable=self.channel_input_var, placeholder_text="e.g., @MrBeast, UC..., or https://youtube.com/...")
        self.entry_channel.grid(row=1, column=1, padx=15, pady=15, sticky="ew")

        # 3. Date Selection Section
        self.date_frame = ctk.CTkFrame(self)
        self.date_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        ctk.CTkLabel(self.date_frame, text="Time Range:", font=("Roboto", 14, "bold")).pack(side="left", padx=15, pady=15)
        
        # Presets
        self.combo_range = ctk.CTkComboBox(
            self.date_frame, 
            values=["Last 1 Month", "Last 2 Months", "Last 5 Months", "Custom Range"],
            variable=self.date_range_mode,
            command=self._toggle_date_inputs
        )
        self.combo_range.pack(side="left", padx=10)

        # Custom Date Pickers (Hidden initially)
        self.custom_date_container = ctk.CTkFrame(self.date_frame, fg_color="transparent")
        
        self.lbl_from = ctk.CTkLabel(self.custom_date_container, text="From:")
        self.lbl_from.pack(side="left", padx=(10, 5))
        
        self.date_from = DateEntry(self.custom_date_container, width=12, background='#1f538d', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.date_from.pack(side="left", padx=5)

        self.lbl_to = ctk.CTkLabel(self.custom_date_container, text="To:")
        self.lbl_to.pack(side="left", padx=(10, 5))
        
        self.date_to = DateEntry(self.custom_date_container, width=12, background='#1f538d', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.date_to.pack(side="left", padx=5)

        # 4. Action & Progress
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        
        self.btn_fetch = ctk.CTkButton(self.action_frame, text="Fetch & Export Data", command=self.start_fetching_thread, height=40, font=("Roboto", 16))
        self.btn_fetch.pack(fill="x", padx=100)

        self.progress_bar = ctk.CTkProgressBar(self.action_frame)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=20, pady=(15, 5))
        
        self.status_label = ctk.CTkLabel(self.action_frame, textvariable=self.status_var)
        self.status_label.pack()

        # 5. Log Output
        self.log_box = ctk.CTkTextbox(self, state="disabled", font=("Consolas", 12))
        self.log_box.grid(row=4, column=0, padx=20, pady=(0, 20), sticky="nsew")

    def _toggle_date_inputs(self, choice):
        if choice == "Custom Range":
            self.custom_date_container.pack(side="left", padx=10)
        else:
            self.custom_date_container.pack_forget()

    def log(self, message):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def start_fetching_thread(self):
        api_key = self.api_key_var.get().strip()
        channel_input = self.channel_input_var.get().strip()
        
        if not api_key:
            messagebox.showerror("Error", "Please enter a valid API Key.")
            return
        if not channel_input:
            messagebox.showerror("Error", "Please enter a Channel ID, URL, or Handle.")
            return

        self.btn_fetch.configure(state="disabled")
        self.progress_bar.set(0)
        self.status_var.set("Initializing...")
        
        thread = threading.Thread(target=self.run_fetch_logic, args=(api_key, channel_input))
        thread.start()

    def _get_category_map(self, youtube):
        """Fetches category IDs and maps them to readable names."""
        try:
            request = youtube.videoCategories().list(
                part="snippet",
                regionCode="US" # Defaults to US for English names
            )
            response = request.execute()
            cat_map = {}
            for item in response['items']:
                cat_map[item['id']] = item['snippet']['title']
            return cat_map
        except Exception as e:
            self.log(f"Warning: Could not fetch category names ({str(e)}). Using IDs.")
            return {}

    def run_fetch_logic(self, api_key, channel_input):
        try:
            youtube = build('youtube', 'v3', developerKey=api_key)
            
            # 1. Fetch Category Map
            self.log("Fetching Category definitions...")
            category_map = self._get_category_map(youtube)
            
            # 2. Resolve Channel ID
            self.log(f"Resolving channel: {channel_input}...")
            channel_id = self.get_channel_id(youtube, channel_input)
            
            if not channel_id:
                raise Exception("Could not find Channel ID. Check your input.")
            
            # 3. Get Channel Details
            self.log(f"Fetching channel details for ID: {channel_id}")
            channel_response = youtube.channels().list(
                id=channel_id,
                part='contentDetails,snippet'
            ).execute()
            
            if not channel_response['items']:
                raise Exception("Channel not found in API.")

            channel_name = channel_response['items'][0]['snippet']['title']
            uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            self.log(f"Found Channel: {channel_name}")

            # 4. Determine Date Range
            end_date = datetime.now()
            start_date = None
            
            mode = self.date_range_mode.get()
            if mode == "Last 1 Month":
                start_date = end_date - timedelta(days=30)
            elif mode == "Last 2 Months":
                start_date = end_date - timedelta(days=60)
            elif mode == "Last 5 Months":
                start_date = end_date - timedelta(days=150)
            elif mode == "Custom Range":
                d_from = self.date_from.get_date()
                d_to = self.date_to.get_date()
                start_date = datetime.combine(d_from, datetime.min.time())
                end_date = datetime.combine(d_to, datetime.max.time())

            start_date = start_date.astimezone()
            end_date = end_date.astimezone()

            self.log(f"Fetching videos between {start_date.date()} and {end_date.date()}...")
            
            # 5. Fetch Video IDs from Playlist
            video_ids = []
            next_page_token = None
            keep_fetching = True
            
            while keep_fetching:
                pl_request = youtube.playlistItems().list(
                    playlistId=uploads_playlist_id,
                    part='snippet,contentDetails',
                    maxResults=50,
                    pageToken=next_page_token
                )
                pl_response = pl_request.execute()
                
                for item in pl_response['items']:
                    published_at_str = item['contentDetails'].get('videoPublishedAt') or item['snippet']['publishedAt']
                    published_at = isodate.parse_datetime(published_at_str)
                    
                    if published_at > end_date:
                        continue
                    if published_at < start_date:
                        keep_fetching = False
                        break
                    
                    video_ids.append(item['contentDetails']['videoId'])

                next_page_token = pl_response.get('nextPageToken')
                if not next_page_token:
                    break
                
                self.status_var.set(f"Found {len(video_ids)} videos so far...")

            if not video_ids:
                raise Exception("No videos found in the selected date range.")

            self.log(f"Total videos to fetch details for: {len(video_ids)}")
            self.progress_bar.set(0.2)

            # 6. Fetch Detailed Metrics
            video_data_list = []
            chunks = [video_ids[i:i + 50] for i in range(0, len(video_ids), 50)]
            total_chunks = len(chunks)

            for i, chunk in enumerate(chunks):
                self.status_var.set(f"Fetching details batch {i+1}/{total_chunks}...")
                self.progress_bar.set(0.2 + (0.7 * ((i+1)/total_chunks)))
                
                vid_request = youtube.videos().list(
                    id=','.join(chunk),
                    part='snippet,statistics,contentDetails,status,liveStreamingDetails'
                )
                vid_response = vid_request.execute()

                for vid in vid_response['items']:
                    stats = vid.get('statistics', {})
                    snippet = vid.get('snippet', {})
                    content = vid.get('contentDetails', {})
                    status = vid.get('status', {})
                    
                    # Duration Parsing
                    iso_duration = content.get('duration', 'PT0S')
                    try:
                        dur = isodate.parse_duration(iso_duration)
                        duration_str = str(dur)
                    except:
                        duration_str = iso_duration

                    # Thumbnails
                    thumb_url = snippet.get('thumbnails', {}).get('maxres', {}).get('url')
                    if not thumb_url:
                        thumb_url = snippet.get('thumbnails', {}).get('high', {}).get('url')

                    # Live Status
                    live_status = snippet.get('liveBroadcastContent', 'none')
                    is_live_upload = "Normal Upload"
                    if live_status != 'none':
                        is_live_upload = f"Live ({live_status})"
                    elif 'liveStreamingDetails' in vid:
                        is_live_upload = "Live Stream Archive"

                    # Category Name Lookup
                    cat_id = snippet.get('categoryId')
                    cat_name = category_map.get(cat_id, f"ID: {cat_id}")

                    data = {
                        'Video ID': vid['id'],
                        'Title': snippet.get('title'),
                        'Full Description': snippet.get('description'),
                        'Published At': snippet.get('publishedAt'),
                        'Views': stats.get('viewCount', 0),
                        'Likes': stats.get('likeCount', 0),
                        'Comment Count': stats.get('commentCount', 0),
                        'Duration': duration_str,
                        'Type': is_live_upload,
                        'Category': cat_name,  # Now shows Name instead of ID
                        'Definition': content.get('definition'),
                        'Privacy Status': status.get('privacyStatus'),
                        'Tags': ", ".join(snippet.get('tags', [])),
                        'Thumbnail URL': thumb_url,
                        'Video URL': f"https://www.youtube.com/watch?v={vid['id']}"
                    }
                    video_data_list.append(data)

            # 7. Export to CSV
            self.status_var.set("Exporting Data...")
            self.progress_bar.set(0.95)
            
            df = pd.DataFrame(video_data_list)
            
            safe_channel_name = "".join([c for c in channel_name if c.isalpha() or c.isdigit() or c==' ']).strip()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{safe_channel_name}_Videos_{timestamp}.csv"
            
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            
            self.log(f"Successfully exported {len(df)} videos to {filename}")
            self.status_var.set("Completed!")
            self.progress_bar.set(1.0)
            messagebox.showinfo("Success", f"Data exported successfully!\nFile: {filename}")

        except Exception as e:
            self.log(f"Error: {str(e)}")
            self.status_var.set("Error occurred")
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")
        finally:
            self.btn_fetch.configure(state="normal")

    def get_channel_id(self, youtube, input_str):
        """Resolves Channel ID from URL, Handle, or ID"""
        input_str = input_str.strip()
        
        # Case 1: Handle (@username)
        if input_str.startswith("@"):
            resp = youtube.channels().list(part="id", forHandle=input_str).execute()
            if resp.get('items'):
                return resp['items'][0]['id']
        
        # Case 2: Direct ID
        if input_str.startswith("UC") and len(input_str) == 24:
            return input_str
            
        # Case 3: Full URL parsing
        if "youtube.com" in input_str or "youtu.be" in input_str:
            handle_match = re.search(r"youtube\.com/(@[\w\-\.]+)", input_str)
            if handle_match:
                handle = handle_match.group(1)
                resp = youtube.channels().list(part="id", forHandle=handle).execute()
                if resp.get('items'):
                    return resp['items'][0]['id']
            
            channel_match = re.search(r"youtube\.com/channel/(UC[\w\-]+)", input_str)
            if channel_match:
                return channel_match.group(1)

        # Fallback
        if " " not in input_str:
            try:
                resp = youtube.channels().list(part="id", forHandle=f"@{input_str}").execute()
                if resp.get('items'):
                    return resp['items'][0]['id']
            except:
                pass

        return None

if __name__ == "__main__":
    app = YouTubeDataFetcherApp()
    app.mainloop()