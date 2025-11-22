"""
YouTube Channel Analyzer - Main Application

A desktop GUI application for analyzing YouTube channels and extracting
comprehensive metrics including engagement, upload frequency, content quality,
and growth predictions.

Features:
- Multi-channel batch analysis
- Date range filtering
- 24+ metrics per channel
- CSV export with human-readable headers
- Automatic default filename generation

Usage:
    python main.py
"""
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime, timezone, timedelta

import pandas as pd
from dateutil import parser as dateparse

from youtube_edu_analyzer.config import load_api_key
from youtube_edu_analyzer.youtube_client import YouTubeClient
from youtube_edu_analyzer.analysis import extract_channel_identifier, analyze_channel
from youtube_edu_analyzer.insights import aggregate_insights


MAX_VIDEOS_PER_CHANNEL = 200

# CSV Column Header Mapping: Technical name -> Human-readable name
CSV_COLUMN_HEADERS = {
    'channel_id': 'Channel ID',
    'channel_title': 'Channel Name',
    'subscribers': 'Subscribers',
    'channel_total_views': 'Total Channel Views',
    'sample_videos_analyzed': 'Videos Analyzed',
    'avg_uploads_per_week': 'Average Uploads Per Week',
    'avg_uploads_long_per_week': 'Long Videos Per Week',
    'avg_uploads_shorts_per_week': 'Shorts Per Week',
    'avg_runtime_long_seconds': 'Average Long Video Duration (seconds)',
    'avg_runtime_shorts_seconds': 'Average Shorts Duration (seconds)',
    'engagement_pct_popular_videos': 'Engagement % (Top Videos)',
    'top_5_long_titles': 'Top 5 Long Videos',
    'top_5_shorts_titles': 'Top 5 Shorts',
    'cta_counts': 'Call-to-Action Keywords',
    'top_topics': 'Top Topics',
    'est_views_next_6_months': 'Estimated Views (6 Months)',
    'est_subs_next_6_months': 'Estimated New Subscribers (6 Months)',
    'quality_score_0_10': 'Quality Score (0-10)',
    'community_score_0_10': 'Community Score (0-10)',
    'monetization_inference': 'Monetization Strategy',
    'avg_views_sample': 'Average Views Per Video',
    'engagement_rate_overall_pct': 'Overall Engagement Rate %'
}


class App:
    def __init__(self, root):
        self.root = root
        root.title('YouTube Channel Analyzer - Extended Metrics')
        # Make the window responsive
        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)
        # Reasonable minimum window size
        try:
            root.minsize(950, 650)
        except Exception:
            pass
        self.youtube = None
        self.analyses = []
        self.period_options = ['All time', 'Last 7 days', 'Last 30 days', 'Last 90 days', 'Last year']

        frm = ttk.Frame(root, padding=15)
        frm.grid(row=0, column=0, sticky='nsew')
        # Configure grid weights within the main frame
        frm.columnconfigure(0, weight=1)
        # rows: inputs + text area + controls + log label + log area
        frm.rowconfigure(2, weight=2)   # channel input text grows more
        frm.rowconfigure(9, weight=3)   # log text grows most
        
        current_row = 0

        # === API Key Section ===
        api_frame = ttk.LabelFrame(frm, text='API Configuration', padding=10)
        api_frame.grid(row=current_row, column=0, sticky='ew', pady=(0, 10))
        api_frame.columnconfigure(1, weight=1)
        
        ttk.Label(api_frame, text='YouTube API Key:').grid(row=0, column=0, sticky='w', padx=(0, 10))
        self.api_key_var = tk.StringVar(value=load_api_key())
        ttk.Entry(api_frame, textvariable=self.api_key_var, width=70, show='*').grid(row=0, column=1, sticky='we')
        current_row += 1

        # === Channel Input Section ===
        input_frame = ttk.LabelFrame(frm, text='Channel Input', padding=10)
        input_frame.grid(row=current_row, column=0, sticky='nsew', pady=(0, 10))
        input_frame.rowconfigure(0, weight=1)
        input_frame.columnconfigure(0, weight=1)
        
        input_container = ttk.Frame(input_frame)
        input_container.grid(row=0, column=0, sticky='nsew')
        input_container.rowconfigure(0, weight=1)
        input_container.columnconfigure(0, weight=1)
        
        self.text = tk.Text(input_container, width=100, height=10, wrap='word', font=('Consolas', 9))
        self.text.grid(row=0, column=0, sticky='nsew')
        input_scroll = ttk.Scrollbar(input_container, orient='vertical', command=self.text.yview)
        input_scroll.grid(row=0, column=1, sticky='ns')
        self.text.configure(yscrollcommand=input_scroll.set)
        
        ttk.Label(input_frame, text='Enter channel URLs or IDs (one per line)', 
                 font=('', 8), foreground='gray').grid(row=1, column=0, sticky='w', pady=(5, 0))
        current_row += 1

        # === Filter Options Section ===
        filter_frame = ttk.LabelFrame(frm, text='Filter Options', padding=10)
        filter_frame.grid(row=current_row, column=0, sticky='ew', pady=(0, 10))
        
        # Row 0: Time Period dropdown
        ttk.Label(filter_frame, text='Time Period:').grid(row=0, column=0, sticky='w', padx=(0, 5))
        self.period_var = tk.StringVar(value=self.period_options[0])
        self.period_combo = ttk.Combobox(filter_frame, values=self.period_options, textvariable=self.period_var, 
                                    state='readonly', width=18)
        self.period_combo.grid(row=0, column=1, sticky='w', padx=(0, 30))
        
        # Row 0: Custom date checkbox (beside period)
        self.use_custom_date_var = tk.BooleanVar(value=False)
        
        def on_toggle_custom_date():
            try:
                custom_enabled = self.use_custom_date_var.get()
                state = 'normal' if custom_enabled else 'disabled'
                self.from_date_entry.configure(state=state)
                self.to_date_entry.configure(state=state)
                # Disable period dropdown when custom dates are enabled
                self.period_combo.configure(state='disabled' if custom_enabled else 'readonly')
            except Exception:
                pass
        
        custom_check = ttk.Checkbutton(filter_frame, text='Custom Range:', 
                                       variable=self.use_custom_date_var, command=on_toggle_custom_date)
        custom_check.grid(row=0, column=2, sticky='w', padx=(0, 5))
        
        # Row 0: From date
        ttk.Label(filter_frame, text='From:').grid(row=0, column=3, sticky='w', padx=(0, 5))
        self.from_date_var = tk.StringVar()
        self.from_date_entry = ttk.Entry(filter_frame, textvariable=self.from_date_var, width=12, state='disabled')
        self.from_date_entry.grid(row=0, column=4, sticky='w', padx=(0, 10))
        
        # Row 0: To date
        ttk.Label(filter_frame, text='To:').grid(row=0, column=5, sticky='w', padx=(0, 5))
        self.to_date_var = tk.StringVar()
        self.to_date_entry = ttk.Entry(filter_frame, textvariable=self.to_date_var, width=12, state='disabled')
        self.to_date_entry.grid(row=0, column=6, sticky='w', padx=(0, 10))
        
        # Row 0: Format hint
        ttk.Label(filter_frame, text='(YYYY-MM-DD)', font=('', 8), foreground='gray').grid(row=0, column=7, sticky='w')
        
        current_row += 1

        # === Action Buttons ===
        button_frame = ttk.Frame(frm)
        button_frame.grid(row=current_row, column=0, sticky='ew', pady=(0, 10))
        
        self.btn_load = ttk.Button(button_frame, text='📁 Load from File', command=self.load_file, width=18)
        self.btn_load.grid(row=0, column=0, sticky='w', padx=(0, 5))
        
        self.btn_fetch = ttk.Button(button_frame, text='▶ Fetch & Analyze', command=self.fetch_and_analyze, width=18)
        self.btn_fetch.grid(row=0, column=1, sticky='w', padx=5)
        
        self.btn_export = ttk.Button(button_frame, text='💾 Export CSV', command=self.export_csv, width=18)
        self.btn_export.grid(row=0, column=2, sticky='w', padx=5)
        
        # Info label
        info_label = ttk.Label(button_frame, text='Note: Always fetches all videos from each channel', 
                              font=('', 8), foreground='gray')
        info_label.grid(row=0, column=3, sticky='w', padx=(20, 0))
        current_row += 1

        # === Progress Section ===
        progress_frame = ttk.LabelFrame(frm, text='Progress', padding=10)
        progress_frame.grid(row=current_row, column=0, sticky='ew', pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress = ttk.Progressbar(progress_frame, orient='horizontal', mode='determinate', maximum=100, value=0)
        self.progress.grid(row=0, column=0, sticky='we')
        current_row += 1
        
        # === Log Section ===
        log_frame = ttk.LabelFrame(frm, text='Analysis Log', padding=10)
        log_frame.grid(row=current_row, column=0, sticky='nsew')
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        
        log_container = ttk.Frame(log_frame)
        log_container.grid(row=0, column=0, sticky='nsew')
        log_container.rowconfigure(0, weight=1)
        log_container.columnconfigure(0, weight=1)
        
        self.log = tk.Text(log_container, width=100, height=12, state='disabled', wrap='word', 
                          font=('Consolas', 9), bg='#f5f5f5')
        self.log.grid(row=0, column=0, sticky='nsew')
        log_scroll = ttk.Scrollbar(log_container, orient='vertical', command=self.log.yview)
        log_scroll.grid(row=0, column=1, sticky='ns')
        self.log.configure(yscrollcommand=log_scroll.set)
        
        # Add a sizegrip to indicate resizable window
        sizegrip = ttk.Sizegrip(frm)
        sizegrip.grid(row=current_row, column=0, sticky='se')

    def log_msg(self, s):
        self.log.configure(state='normal')
        self.log.insert('end', f"{datetime.now().isoformat()} - {s}\n")
        self.log.see('end')
        self.log.configure(state='disabled')

    def load_file(self):
        fn = filedialog.askopenfilename(filetypes=[('Text files','*.txt'),('All','*.*')])
        if not fn:
            return
        with open(fn,'r',encoding='utf-8') as f:
            content = f.read()
        self.text.delete('1.0','end')
        self.text.insert('1.0', content)
        self.log_msg(f'Loaded {fn}')

    def fetch_and_analyze(self):
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror('Missing API key', 'API key not found in config.')
            return
        try:
            self.youtube = YouTubeClient(api_key)
        except Exception as e:
            messagebox.showerror('API Client error', str(e))
            return

        raw = self.text.get('1.0','end').strip()
        if not raw:
            messagebox.showerror('No channels', 'Paste at least one channel URL/ID')
            return
        lines = [l.strip() for l in raw.splitlines() if l.strip()]
        ids = [extract_channel_identifier(l) for l in lines]

        # Disable buttons during processing and initialize progress
        total = len(ids)
        self.analyses = []
        self.progress.configure(maximum=max(total, 1))
        self.progress['value'] = 0
        for btn in (self.btn_load, self.btn_fetch, self.btn_export):
            try:
                btn.configure(state='disabled')
            except Exception:
                pass
        self.log_msg(f'Starting fetch for {total} channels...')

        try:
            for idx, ident in enumerate(ids, start=1):
                # Update progress bar
                self.progress['value'] = idx - 1
                self.root.update_idletasks()

                self.log_msg(f'Processing: {ident}')
                try:
                    ch = self.youtube.get_channel(ident)
                except ValueError as e:
                    self.log_msg(f'  -> Error fetching channel {ident}: {e}')
                    self.progress['value'] = idx
                    self.root.update_idletasks()
                    continue
                if not ch:
                    self.log_msg(f'  -> Channel not found: {ident}')
                    # advance progress and continue
                    self.progress['value'] = idx
                    self.root.update_idletasks()
                    continue
                title = ch.get('snippet',{}).get('title')
                uploads = ch.get('contentDetails',{}).get('relatedPlaylists',{}).get('uploads')
                if not uploads:
                    self.log_msg(f'  -> No uploads playlist: {title}')
                    self.progress['value'] = idx
                    self.root.update_idletasks()
                    continue
                # Always fetch all videos (no limit)
                # Date filtering will be applied after fetching
                self.log_msg(f'  -> Fetching all videos from channel...')
                try:
                    video_ids = self.youtube.get_videos_from_uploads(uploads, max_videos=None)
                except ValueError as e:
                    self.log_msg(f'  -> Error fetching videos for {title}: {e}')
                    self.progress['value'] = idx
                    self.root.update_idletasks()
                    continue
                if not video_ids:
                    self.log_msg(f'  -> No videos: {title}')
                    self.progress['value'] = idx
                    self.root.update_idletasks()
                    continue
                self.log_msg(f'  -> Fetched {len(video_ids)} video IDs; fetching details...')
                try:
                    video_items = self.youtube.get_videos_details(video_ids)
                except ValueError as e:
                    self.log_msg(f'  -> Error fetching video details for {title}: {e}')
                    self.progress['value'] = idx
                    self.root.update_idletasks()
                    continue
                
                total_fetched = len(video_items)
                self.log_msg(f'  -> Retrieved {total_fetched} videos; applying date filter...')
                # Apply date filter if selected (custom date range takes precedence)
                filtered = []
                filter_applied = False
                filter_description = ''
                
                if self.use_custom_date_var.get():
                    # Use custom date range
                    from_date_str = self.from_date_var.get().strip()
                    to_date_str = self.to_date_var.get().strip()
                    
                    if not from_date_str and not to_date_str:
                        self.log_msg(f'  -> Warning: Custom date range enabled but no dates provided. Analyzing all videos.')
                    else:
                        try:
                            from_dt = None
                            to_dt = None
                            
                            # Parse custom date range
                            # Note: Input dates are assumed to be in local timezone
                            # Start date: set to 00:00:00 (beginning of day)
                            # End date: set to 23:59:59.999999 (end of day)
                            if from_date_str:
                                from_dt = datetime.strptime(from_date_str, '%Y-%m-%d')
                                from_dt = from_dt.replace(hour=0, minute=0, second=0, microsecond=0)
                            
                            if to_date_str:
                                to_dt = datetime.strptime(to_date_str, '%Y-%m-%d')
                                to_dt = to_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
                            
                            if from_dt and to_dt and from_dt > to_dt:
                                self.log_msg(f'  -> Warning: From date is after To date, skipping date filter')
                            else:
                                for v in video_items:
                                    pub_str = v.get('snippet',{}).get('publishedAt')
                                    try:
                                        pub_dt = dateparse.parse(pub_str) if pub_str else None
                                    except Exception:
                                        pub_dt = None
                                    if pub_dt is not None:
                                        # Convert timezone-aware datetime to naive (local time)
                                        # This ensures consistent comparison with user-provided dates
                                        # Note: Videos published near midnight in different timezones
                                        # may be included/excluded based on local time conversion
                                        if pub_dt.tzinfo is not None:
                                            pub_dt = pub_dt.astimezone(tz=None).replace(tzinfo=None)
                                        # Check if date is within range (inclusive)
                                        if from_dt and pub_dt < from_dt:
                                            continue
                                        if to_dt and pub_dt > to_dt:
                                            continue
                                        filtered.append(v)
                                video_items = filtered
                                filter_applied = True
                                range_desc = []
                                if from_date_str:
                                    range_desc.append(f'from {from_date_str}')
                                if to_date_str:
                                    range_desc.append(f'to {to_date_str}')
                                filter_description = f'custom range ({", ".join(range_desc)})'
                        except ValueError as e:
                            self.log_msg(f'  -> Warning: Invalid date format. Use YYYY-MM-DD. Error: {e}')
                
                if not filter_applied:
                    # Use period dropdown filter
                    period = self.period_var.get()
                    cutoff_dt = None
                    # Get current time in UTC, then convert to naive local time for consistency
                    now = datetime.now(timezone.utc).astimezone(tz=None).replace(tzinfo=None)
                    if period == 'Last 7 days':
                        cutoff_dt = now - timedelta(days=7)
                    elif period == 'Last 30 days':
                        cutoff_dt = now - timedelta(days=30)
                    elif period == 'Last 90 days':
                        cutoff_dt = now - timedelta(days=90)
                    elif period == 'Last year':
                        cutoff_dt = now - timedelta(days=365)
                    
                    if cutoff_dt is not None:
                        for v in video_items:
                            pub_str = v.get('snippet',{}).get('publishedAt')
                            try:
                                pub_dt = dateparse.parse(pub_str) if pub_str else None
                            except Exception:
                                pub_dt = None
                            if pub_dt is not None:
                                # Convert to naive datetime for comparison
                                if pub_dt.tzinfo is not None:
                                    pub_dt = pub_dt.astimezone(tz=None).replace(tzinfo=None)
                                # Include videos published on or after cutoff date (inclusive)
                                if pub_dt >= cutoff_dt:
                                    filtered.append(v)
                        video_items = filtered
                        filter_applied = True
                        filter_description = period
                
                if filter_applied:
                    self.log_msg(f'  -> Filtered to {len(video_items)} videos within {filter_description} (from {total_fetched} total)')
                else:
                    self.log_msg(f'  -> Using all {len(video_items)} videos (no date filter applied)')
                analysis = analyze_channel(ch, video_items)
                if analysis:
                    self.analyses.append(analysis)
                    self.log_msg(f'  -> Done: {analysis["channel_title"]} (subs: {analysis["subscribers"]})')

                # advance progress at end of iteration
                self.progress['value'] = idx
                self.root.update_idletasks()

            if self.analyses:
                self.log_msg('Aggregating insights...')
                insights = aggregate_insights(self.analyses)
                # Plot generation disabled by default
                self.log_msg('Top suggestions:')
                for s in insights.get('suggestions',[]):
                    self.log_msg(' - ' + s)
                top_topics = [t for t,c in insights.get('top_overall_topics',[])[:10]]
                self.log_msg('Top topics overall: ' + ', '.join(top_topics))
            else:
                self.log_msg('No analyses produced; check errors above.')
        finally:
            # Ensure buttons re-enable and progress completes
            for btn in (self.btn_load, self.btn_fetch, self.btn_export):
                try:
                    btn.configure(state='normal')
                except Exception:
                    pass
            self.progress['value'] = total
            self.root.update_idletasks()

    def export_csv(self):
        if not self.analyses:
            messagebox.showwarning('No data','Run analysis first')
            return
        
        # Generate default filename with timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
        default_filename = f'youtube_analysis_{timestamp}.csv'
        
        fn = filedialog.asksaveasfilename(
            defaultextension='.csv', 
            filetypes=[('CSV','*.csv')],
            initialfile=default_filename
        )
        if not fn:
            return
        
        df = pd.DataFrame(self.analyses)
        
        # Expand lists/dicts into JSON strings for CSV friendliness
        # Use ensure_ascii=False to preserve Unicode characters (emojis, etc.)
        def safe_json_dumps(x):
            try:
                return json.dumps(x, ensure_ascii=False) if x is not None else ''
            except (TypeError, ValueError):
                return str(x) if x is not None else ''
        
        if 'top_5_long_titles' in df.columns:
            df['top_5_long_titles'] = df['top_5_long_titles'].apply(safe_json_dumps)
        if 'top_5_shorts_titles' in df.columns:
            df['top_5_shorts_titles'] = df['top_5_shorts_titles'].apply(safe_json_dumps)
        if 'cta_counts' in df.columns:
            df['cta_counts'] = df['cta_counts'].apply(safe_json_dumps)
        if 'top_topics' in df.columns:
            df['top_topics'] = df['top_topics'].apply(safe_json_dumps)
        
        # Rename columns to human-readable headers
        df = df.rename(columns=CSV_COLUMN_HEADERS)
        
        try:
            # Use UTF-8 encoding to properly handle Unicode characters
            df.to_csv(fn, index=False, encoding='utf-8-sig')
        except PermissionError:
            messagebox.showerror('Permission denied', 'Close the file if it\'s open and choose another location.')
            self.log_msg(f'Failed to export CSV due to permission error: {fn}')
            return
        except Exception as e:
            messagebox.showerror('Export error', str(e))
            self.log_msg(f'Failed to export CSV: {e}')
            return
        self.log_msg(f'Exported CSV to {fn}')
        messagebox.showinfo('Exported', f'CSV exported to {fn}')



# ----------------------- Run -----------------------
if __name__ == '__main__':
    root = tk.Tk()
    app = App(root)
    root.mainloop()
