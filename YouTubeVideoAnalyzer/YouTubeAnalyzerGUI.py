import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import re
from typing import List, Dict, Optional
import threading

class YouTubeAnalyzer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        self.channel_name = None
    
    def get_channel_id(self, channel_input: str) -> Optional[str]:
        """Extract channel ID from URL or username"""
        try:
            # Check if it's a channel ID already
            if channel_input.startswith('UC') and len(channel_input) == 24:
                return channel_input
            
            # Extract from URL patterns
            patterns = [
                r'youtube\.com/channel/(UC[\w-]+)',
                r'youtube\.com/@([\w-]+)',
                r'youtube\.com/c/([\w-]+)',
                r'youtube\.com/user/([\w-]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, channel_input)
                if match:
                    username = match.group(1)
                    if username.startswith('UC'):
                        return username
                    
                    # Search for channel by username
                    request = self.youtube.search().list(
                        part='snippet',
                        q=username,
                        type='channel',
                        maxResults=1
                    )
                    response = request.execute()
                    if response['items']:
                        return response['items'][0]['snippet']['channelId']
            
            # Try as direct username/handle
            request = self.youtube.search().list(
                part='snippet',
                q=channel_input,
                type='channel',
                maxResults=1
            )
            response = request.execute()
            if response['items']:
                return response['items'][0]['snippet']['channelId']
            
            return None
        except HttpError as e:
            raise Exception(f"API Error: {str(e)}")
    
    def get_channel_videos(self, channel_id: str, date_from: datetime, date_to: datetime) -> List[str]:
        """Fetch all video IDs from channel within date range"""
        video_ids = []
        
        request = self.youtube.channels().list(
            part='contentDetails,snippet',
            id=channel_id
        )
        response = request.execute()
        
        if not response['items']:
            return video_ids
        
        # Store channel name
        self.channel_name = response['items'][0]['snippet']['title']
        
        playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        
        next_page_token = None
        while True:
            request = self.youtube.playlistItems().list(
                part='contentDetails',
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()
            
            for item in response['items']:
                video_ids.append(item['contentDetails']['videoId'])
            
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
        
        return video_ids
    
    def get_video_details(self, video_ids: List[str], date_from: datetime, date_to: datetime) -> List[Dict]:
        """Fetch detailed information for videos"""
        videos_data = []
        
        # Process in batches of 50 (API limit)
        for i in range(0, len(video_ids), 50):
            batch = video_ids[i:i+50]
            
            request = self.youtube.videos().list(
                part='snippet,contentDetails,statistics',
                id=','.join(batch)
            )
            response = request.execute()
            
            for item in response['items']:
                publish_date = datetime.strptime(
                    item['snippet']['publishedAt'], 
                    '%Y-%m-%dT%H:%M:%SZ'
                )
                
                # Filter by date range
                if date_from <= publish_date <= date_to:
                    video_data = self.parse_video_data(item, publish_date)
                    videos_data.append(video_data)
        
        return videos_data
    
    def parse_video_data(self, item: Dict, publish_date: datetime) -> Dict:
        """Parse video data into structured format"""
        stats = item['statistics']
        snippet = item['snippet']
        content = item['contentDetails']
        
        video_id = item['id']
        title = snippet['title']
        description = snippet['description']
        category_id = snippet['categoryId']
        tags = snippet.get('tags', [])
        thumbnail_url = snippet['thumbnails']['high']['url']
        
        view_count = int(stats.get('viewCount', 0))
        like_count = int(stats.get('likeCount', 0))
        comment_count = int(stats.get('commentCount', 0))
        
        duration = self.parse_duration(content['duration'])
        
        # Calculate engagement metrics
        days_since_upload = max((datetime.now() - publish_date).days, 1)
        avg_views_per_day = view_count / days_since_upload
        like_to_view_ratio = (like_count / view_count * 100) if view_count > 0 else 0
        comment_to_view_ratio = (comment_count / view_count * 100) if view_count > 0 else 0
        
        return {
            'Video ID': video_id,
            'Title': title,
            'Description': description,
            'View Count': view_count,
            'Like Count': like_count,
            'Comment Count': comment_count,
            'Upload Date': publish_date.strftime('%Y-%m-%d'),
            'Upload Time': publish_date.strftime('%H:%M:%S'),
            'Days Since Upload': days_since_upload,
            'Avg Views/Day': round(avg_views_per_day, 2),
            'Like-to-View Ratio (%)': round(like_to_view_ratio, 4),
            'Comment-to-View Ratio (%)': round(comment_to_view_ratio, 4),
            'Duration (seconds)': duration,
            'Duration (formatted)': self.format_duration(duration),
            'Category ID': category_id,
            'Tags': ', '.join(tags) if tags else 'No tags',
            'Thumbnail URL': thumbnail_url,
            'Video URL': f'https://www.youtube.com/watch?v={video_id}',
        }
    
    def parse_duration(self, duration: str) -> int:
        """Convert ISO 8601 duration to seconds"""
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
        if not match:
            return 0
        
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        
        return hours * 3600 + minutes * 60 + seconds
    
    def format_duration(self, seconds: int) -> str:
        """Format seconds to HH:MM:SS"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"


class YouTubeAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Channel Analyzer - EdTech Research Tool")
        self.root.geometry("900x700")
        self.analyzer = None
        
        self.create_widgets()
    
    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # API Key Section
        ttk.Label(main_frame, text="YouTube API Key:", font=('Arial', 10, 'bold')).grid(
            row=0, column=0, sticky=tk.W, pady=5
        )
        self.api_key_entry = ttk.Entry(main_frame, width=60, show="*")
        self.api_key_entry.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Channel Input Section
        ttk.Label(main_frame, text="Channel URL/ID/Username:", font=('Arial', 10, 'bold')).grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        self.channel_entry = ttk.Entry(main_frame, width=60)
        self.channel_entry.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Date Range Section
        date_frame = ttk.LabelFrame(main_frame, text="Analysis Period", padding="10")
        date_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        self.date_range_var = tk.StringVar(value="1_month")
        
        ttk.Radiobutton(date_frame, text="Last 1 Month", variable=self.date_range_var, 
                       value="1_month", command=self.toggle_custom_dates).grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Radiobutton(date_frame, text="Last 2 Months", variable=self.date_range_var, 
                       value="2_months", command=self.toggle_custom_dates).grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Radiobutton(date_frame, text="Last 5 Months", variable=self.date_range_var, 
                       value="5_months", command=self.toggle_custom_dates).grid(row=0, column=2, sticky=tk.W, padx=5)
        ttk.Radiobutton(date_frame, text="Custom Range", variable=self.date_range_var, 
                       value="custom", command=self.toggle_custom_dates).grid(row=0, column=3, sticky=tk.W, padx=5)
        
        # Custom Date Range
        custom_frame = ttk.Frame(date_frame)
        custom_frame.grid(row=1, column=0, columnspan=4, pady=10)
        
        ttk.Label(custom_frame, text="From:").grid(row=0, column=0, padx=5)
        self.from_date_entry = ttk.Entry(custom_frame, width=12, state='disabled')
        self.from_date_entry.insert(0, (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        self.from_date_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(custom_frame, text="To:").grid(row=0, column=2, padx=5)
        self.to_date_entry = ttk.Entry(custom_frame, width=12, state='disabled')
        self.to_date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self.to_date_entry.grid(row=0, column=3, padx=5)
        
        ttk.Label(custom_frame, text="(Format: YYYY-MM-DD)", font=('Arial', 8)).grid(
            row=0, column=4, padx=5
        )
        
        # Action Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=10)
        
        self.analyze_btn = ttk.Button(button_frame, text="Analyze Channel", 
                                      command=self.analyze_channel)
        self.analyze_btn.grid(row=0, column=0, padx=5)
        
        self.export_btn = ttk.Button(button_frame, text="Export to CSV", 
                                     command=self.export_data, state='disabled')
        self.export_btn.grid(row=0, column=1, padx=5)
        
        # Progress Bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Status Label
        self.status_label = ttk.Label(main_frame, text="Ready to analyze", foreground="blue")
        self.status_label.grid(row=5, column=0, columnspan=3, pady=5)
        
        # Results Section
        results_frame = ttk.LabelFrame(main_frame, text="Analysis Results", padding="10")
        results_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # Treeview with scrollbars
        tree_scroll_y = ttk.Scrollbar(results_frame, orient=tk.VERTICAL)
        tree_scroll_x = ttk.Scrollbar(results_frame, orient=tk.HORIZONTAL)
        
        self.tree = ttk.Treeview(results_frame, 
                                 yscrollcommand=tree_scroll_y.set,
                                 xscrollcommand=tree_scroll_x.set,
                                 height=15)
        
        tree_scroll_y.config(command=self.tree.yview)
        tree_scroll_x.config(command=self.tree.xview)
        
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(6, weight=1)
        
        self.videos_data = []
    
    def toggle_custom_dates(self):
        """Enable/disable custom date entries based on radio selection"""
        if self.date_range_var.get() == "custom":
            self.from_date_entry.config(state='normal')
            self.to_date_entry.config(state='normal')
        else:
            self.from_date_entry.config(state='disabled')
            self.to_date_entry.config(state='disabled')
    
    def get_date_range(self):
        """Calculate date range based on selection"""
        today = datetime.now()
        
        range_type = self.date_range_var.get()
        
        if range_type == "custom":
            try:
                date_from = datetime.strptime(self.from_date_entry.get(), '%Y-%m-%d')
                date_to = datetime.strptime(self.to_date_entry.get(), '%Y-%m-%d')
                return date_from, date_to
            except ValueError:
                raise ValueError("Invalid date format. Use YYYY-MM-DD")
        else:
            months = int(range_type.split('_')[0])
            date_from = today - timedelta(days=months * 30)
            date_to = today
            return date_from, date_to
    
    def analyze_channel(self):
        """Start channel analysis in separate thread"""
        api_key = self.api_key_entry.get().strip()
        channel_input = self.channel_entry.get().strip()
        
        if not api_key:
            messagebox.showerror("Error", "Please enter your YouTube API Key")
            return
        
        if not channel_input:
            messagebox.showerror("Error", "Please enter a channel URL, ID, or username")
            return
        
        try:
            date_from, date_to = self.get_date_range()
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return
        
        # Run analysis in thread to prevent GUI freeze
        thread = threading.Thread(target=self.run_analysis, 
                                 args=(api_key, channel_input, date_from, date_to))
        thread.daemon = True
        thread.start()
    
    def run_analysis(self, api_key, channel_input, date_from, date_to):
        """Execute the analysis"""
        self.update_status("Initializing...", "blue")
        self.progress.start()
        self.analyze_btn.config(state='disabled')
        
        try:
            # Initialize analyzer
            self.analyzer = YouTubeAnalyzer(api_key)
            
            # Get channel ID
            self.update_status("Finding channel...", "blue")
            channel_id = self.analyzer.get_channel_id(channel_input)
            
            if not channel_id:
                self.update_status("Channel not found", "red")
                messagebox.showerror("Error", "Could not find channel. Check your input.")
                return
            
            # Get videos
            self.update_status("Fetching videos...", "blue")
            video_ids = self.analyzer.get_channel_videos(channel_id, date_from, date_to)
            
            if not video_ids:
                self.update_status("No videos found in date range", "orange")
                messagebox.showwarning("Warning", "No videos found in the specified date range.")
                return
            
            # Get video details
            self.update_status(f"Analyzing {len(video_ids)} videos...", "blue")
            self.videos_data = self.analyzer.get_video_details(video_ids, date_from, date_to)
            
            if not self.videos_data:
                self.update_status("No videos in date range", "orange")
                messagebox.showwarning("Warning", "No videos found in the specified date range.")
                return
            
            # Display results
            self.display_results()
            self.update_status(f"Analysis complete! Found {len(self.videos_data)} videos", "green")
            self.export_btn.config(state='normal')
            
        except Exception as e:
            self.update_status(f"Error: {str(e)}", "red")
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")
        
        finally:
            self.progress.stop()
            self.analyze_btn.config(state='normal')
    
    def display_results(self):
        """Display analysis results in treeview"""
        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if not self.videos_data:
            return
        
        # Configure columns
        columns = list(self.videos_data[0].keys())
        self.tree['columns'] = columns
        self.tree['show'] = 'headings'
        
        # Set column headings and widths
        for col in columns:
            self.tree.heading(col, text=col)
            
            # Set appropriate column widths
            if col in ['Video ID', 'Upload Date', 'Upload Time', 'Category ID']:
                width = 100
            elif col in ['Duration (seconds)', 'Duration (formatted)', 'Days Since Upload']:
                width = 120
            elif col in ['View Count', 'Like Count', 'Comment Count']:
                width = 100
            elif col in ['Avg Views/Day', 'Like-to-View Ratio (%)', 'Comment-to-View Ratio (%)']:
                width = 130
            elif col in ['Title', 'Description']:
                width = 250
            elif col in ['Tags']:
                width = 200
            else:
                width = 150
            
            self.tree.column(col, width=width, minwidth=80)
        
        # Insert data
        for video in self.videos_data:
            values = [video[col] for col in columns]
            self.tree.insert('', tk.END, values=values)
    
    def export_data(self):
        """Export data to CSV"""
        if not self.videos_data:
            messagebox.showwarning("Warning", "No data to export")
            return

        # Determine a safe initial filename using the channel name if available
        if self.analyzer and getattr(self.analyzer, 'channel_name', None):
            raw_name = self.analyzer.channel_name
        else:
            raw_name = f"youtube_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Sanitize filename: remove or replace characters not allowed in filenames
        safe_name = re.sub(r'[\\/:*?"<>|]', '_', raw_name).strip()
        initial_filename = f"{safe_name}.csv"

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=initial_filename
        )
        
        if filename:
            try:
                df = pd.DataFrame(self.videos_data)
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                messagebox.showinfo("Success", f"Data exported successfully to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export data:\n{str(e)}")
    
    def update_status(self, message, color):
        """Update status label (thread-safe)"""
        self.root.after(0, lambda: self.status_label.config(text=message, foreground=color))


if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeAnalyzerGUI(root)
    root.mainloop()