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


class App:
    def __init__(self, root):
        self.root = root
        root.title('YouTube Channel Analyzer - Extended Metrics')
        # Make the window responsive
        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)
        # Reasonable minimum window size
        try:
            root.minsize(900, 600)
        except Exception:
            pass
        self.youtube = None
        self.analyses = []
        self.period_options = ['All time', 'Last 7 days', 'Last 30 days', 'Last 90 days', 'Last year']

        frm = ttk.Frame(root, padding=10)
        frm.grid(row=0, column=0, sticky='nsew')
        # Configure grid weights within the main frame
        for c in range(4):
            frm.columnconfigure(c, weight=1)
        # rows: inputs + text area + controls + log label + log area
        frm.rowconfigure(2, weight=2)   # channel input text grows more
        frm.rowconfigure(7, weight=3)   # log text grows most

        ttk.Label(frm, text='YouTube API Key').grid(row=0, column=0, sticky='w')
        self.api_key_var = tk.StringVar(value=load_api_key())
        ttk.Entry(frm, textvariable=self.api_key_var, width=70).grid(row=0, column=1, columnspan=3, sticky='we')

        ttk.Label(frm, text='Paste channel URLs / IDs (one per line):').grid(row=1, column=0, columnspan=4, sticky='w', pady=(8,0))
        # Scrollable input area
        input_container = ttk.Frame(frm)
        input_container.grid(row=2, column=0, columnspan=4, pady=(0,8), sticky='nsew')
        input_container.rowconfigure(0, weight=1)
        input_container.columnconfigure(0, weight=1)
        self.text = tk.Text(input_container, width=100, height=12, wrap='word')
        self.text.grid(row=0, column=0, sticky='nsew')
        input_scroll = ttk.Scrollbar(input_container, orient='vertical', command=self.text.yview)
        input_scroll.grid(row=0, column=1, sticky='ns')
        self.text.configure(yscrollcommand=input_scroll.set)

        # Sample size and period controls
        ttk.Label(frm, text='Sample size (videos/channel)').grid(row=3, column=0, sticky='w')
        self.sample_size_var = tk.IntVar(value=MAX_VIDEOS_PER_CHANNEL)
        self.sample_size_spin = ttk.Spinbox(frm, from_=10, to=1000, increment=10, textvariable=self.sample_size_var, width=10)
        self.sample_size_spin.grid(row=3, column=1, sticky='we')
        ttk.Label(frm, text='Period').grid(row=3, column=2, sticky='e')
        self.period_var = tk.StringVar(value=self.period_options[0])
        ttk.Combobox(frm, values=self.period_options, textvariable=self.period_var, state='readonly', width=18).grid(row=3, column=3, sticky='we')

        # Custom date range option
        self.use_custom_date_var = tk.BooleanVar(value=False)
        def on_toggle_custom_date():
            try:
                custom_enabled = self.use_custom_date_var.get()
                state = 'normal' if custom_enabled else 'disabled'
                self.from_date_entry.configure(state=state)
                self.to_date_entry.configure(state=state)
                # Disable period dropdown when custom dates are enabled
                period_state = 'disabled' if custom_enabled else 'readonly'
                for widget in frm.grid_slaves(row=3, column=3):
                    if isinstance(widget, ttk.Combobox):
                        widget.configure(state=period_state)
                # Disable sample size and "All videos" checkbox when custom dates are enabled
                # (custom date range automatically fetches all videos in the range)
                self.sample_size_spin.configure(state='disabled' if custom_enabled else 'normal')
                # Disable/enable the "All videos" checkbox
                if hasattr(self, 'all_videos_checkbox'):
                    self.all_videos_checkbox.configure(state='disabled' if custom_enabled else 'normal')
                # If custom date is disabled, restore sample size state based on "All videos" checkbox
                if not custom_enabled and hasattr(self, 'all_videos_var'):
                    self.sample_size_spin.configure(state='disabled' if self.all_videos_var.get() else 'normal')
            except Exception:
                pass
        ttk.Checkbutton(frm, text='Use custom date range', variable=self.use_custom_date_var, command=on_toggle_custom_date).grid(row=4, column=0, sticky='w')
        
        # Custom date range fields
        date_frame = ttk.Frame(frm)
        date_frame.grid(row=4, column=1, columnspan=3, sticky='w')
        ttk.Label(date_frame, text='From Date (YYYY-MM-DD):').grid(row=0, column=0, sticky='e', padx=(10,5))
        self.from_date_var = tk.StringVar()
        self.from_date_entry = ttk.Entry(date_frame, textvariable=self.from_date_var, width=12, state='disabled')
        self.from_date_entry.grid(row=0, column=1, sticky='w', padx=(0,20))
        ttk.Label(date_frame, text='To Date (YYYY-MM-DD):').grid(row=0, column=2, sticky='e', padx=(10,5))
        self.to_date_var = tk.StringVar()
        self.to_date_entry = ttk.Entry(date_frame, textvariable=self.to_date_var, width=12, state='disabled')
        self.to_date_entry.grid(row=0, column=3, sticky='w')

        # Fetch all videos option
        self.all_videos_var = tk.BooleanVar(value=False)
        def on_toggle_all():
            try:
                # Only allow toggling if custom date range is not enabled
                if not self.use_custom_date_var.get():
                    self.sample_size_spin.configure(state='disabled' if self.all_videos_var.get() else 'normal')
            except Exception:
                pass
        self.all_videos_checkbox = ttk.Checkbutton(frm, text='All videos', variable=self.all_videos_var, command=on_toggle_all)
        self.all_videos_checkbox.grid(row=5, column=0, sticky='w')

        # Controls row adjusted to row 6 since row 5 now has the All videos checkbox
        self.btn_load = ttk.Button(frm, text='Load from file', command=self.load_file)
        self.btn_load.grid(row=6, column=0, sticky='w')
        self.btn_fetch = ttk.Button(frm, text='Fetch & Analyze', command=self.fetch_and_analyze)
        self.btn_fetch.grid(row=6, column=1, sticky='w')
        self.btn_export = ttk.Button(frm, text='Export CSV', command=self.export_csv)
        self.btn_export.grid(row=6, column=2, sticky='w')
        # Add a sizegrip to indicate resizable window
        sizegrip = ttk.Sizegrip(frm)
        sizegrip.grid(row=9, column=3, sticky='se')

        # Progress bar and status (row 9: columns 0-2; sizegrip at col 3)
        ttk.Label(frm, text='Progress').grid(row=9, column=0, sticky='w')
        self.progress = ttk.Progressbar(frm, orient='horizontal', mode='determinate', maximum=100, value=0)
        self.progress.grid(row=9, column=1, columnspan=2, sticky='we', padx=(6, 0))
        

        ttk.Label(frm, text='Log / Summary:').grid(row=7, column=0, columnspan=4, sticky='w', pady=(12,0))
        # Scrollable log area
        log_container = ttk.Frame(frm)
        log_container.grid(row=8, column=0, columnspan=4, sticky='nsew')
        log_container.rowconfigure(0, weight=1)
        log_container.columnconfigure(0, weight=1)
        self.log = tk.Text(log_container, width=100, height=14, state='disabled', wrap='word')
        self.log.grid(row=0, column=0, sticky='nsew')
        log_scroll = ttk.Scrollbar(log_container, orient='vertical', command=self.log.yview)
        log_scroll.grid(row=0, column=1, sticky='ns')
        self.log.configure(yscrollcommand=log_scroll.set)

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
                # Determine how many videos to fetch
                # If custom date range is enabled, fetch all videos (will be filtered by date range)
                if getattr(self, 'use_custom_date_var', None) and self.use_custom_date_var.get():
                    max_videos = None
                    self.log_msg(f'  -> Custom date range enabled: fetching all videos for date filtering')
                elif getattr(self, 'all_videos_var', None) and self.all_videos_var.get():
                    max_videos = None
                else:
                    try:
                        max_videos = int(self.sample_size_var.get())
                    except Exception:
                        max_videos = MAX_VIDEOS_PER_CHANNEL
                try:
                    video_ids = self.youtube.get_videos_from_uploads(uploads, max_videos=max_videos)
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
                self.log_msg(f'  -> fetched {len(video_ids)} video ids; fetching details...')
                try:
                    video_items = self.youtube.get_videos_details(video_ids)
                except ValueError as e:
                    self.log_msg(f'  -> Error fetching video details for {title}: {e}')
                    self.progress['value'] = idx
                    self.root.update_idletasks()
                    continue
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
                                        if pub_dt.tzinfo is not None:
                                            pub_dt = pub_dt.astimezone(tz=None).replace(tzinfo=None)
                                        # Check if date is within range
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
                                if pub_dt.tzinfo is not None:
                                    pub_dt = pub_dt.astimezone(tz=None).replace(tzinfo=None)
                                if pub_dt >= cutoff_dt:
                                    filtered.append(v)
                        video_items = filtered
                        filter_applied = True
                        filter_description = period
                
                if filter_applied:
                    self.log_msg(f'  -> {len(video_items)} videos within selected {filter_description}')
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
        fn = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV','*.csv')])
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
