import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime, timezone

import pandas as pd

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

        # Fetch all videos option
        self.all_videos_var = tk.BooleanVar(value=False)
        def on_toggle_all():
            try:
                self.sample_size_spin.configure(state='disabled' if self.all_videos_var.get() else 'normal')
            except Exception:
                pass
        ttk.Checkbutton(frm, text='All videos', variable=self.all_videos_var, command=on_toggle_all).grid(row=4, column=0, sticky='w')

        # Controls row adjusted to row 5 since row 4 now has the All videos checkbox
        self.btn_load = ttk.Button(frm, text='Load from file', command=self.load_file)
        self.btn_load.grid(row=5, column=0, sticky='w')
        self.btn_fetch = ttk.Button(frm, text='Fetch & Analyze', command=self.fetch_and_analyze)
        self.btn_fetch.grid(row=5, column=1, sticky='w')
        self.btn_export = ttk.Button(frm, text='Export CSV', command=self.export_csv)
        self.btn_export.grid(row=5, column=2, sticky='w')
        # Add a sizegrip to indicate resizable window
        sizegrip = ttk.Sizegrip(frm)
        sizegrip.grid(row=8, column=3, sticky='se')

        # Progress bar and status (row 8: columns 0-2; sizegrip at col 3)
        ttk.Label(frm, text='Progress').grid(row=8, column=0, sticky='w')
        self.progress = ttk.Progressbar(frm, orient='horizontal', mode='determinate', maximum=100, value=0)
        self.progress.grid(row=8, column=1, columnspan=2, sticky='we', padx=(6, 0))
        

        ttk.Label(frm, text='Log / Summary:').grid(row=6, column=0, columnspan=4, sticky='w', pady=(12,0))
        # Scrollable log area
        log_container = ttk.Frame(frm)
        log_container.grid(row=7, column=0, columnspan=4, sticky='nsew')
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
                ch = self.youtube.get_channel(ident)
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
                if getattr(self, 'all_videos_var', None) and self.all_videos_var.get():
                    max_videos = None
                else:
                    try:
                        max_videos = int(self.sample_size_var.get())
                    except Exception:
                        max_videos = MAX_VIDEOS_PER_CHANNEL
                video_ids = self.youtube.get_videos_from_uploads(uploads, max_videos=max_videos)
                if not video_ids:
                    self.log_msg(f'  -> No videos: {title}')
                    self.progress['value'] = idx
                    self.root.update_idletasks()
                    continue
                self.log_msg(f'  -> fetched {len(video_ids)} video ids; fetching details...')
                video_items = self.youtube.get_videos_details(video_ids)
                # Apply period filter if selected
                period = self.period_var.get()
                from datetime import timedelta
                cutoff_dt = None
                now = datetime.now(timezone.utc).replace(tzinfo=None)
                if period == 'Last 7 days':
                    cutoff_dt = now - timedelta(days=7)
                elif period == 'Last 30 days':
                    cutoff_dt = now - timedelta(days=30)
                elif period == 'Last 90 days':
                    cutoff_dt = now - timedelta(days=90)
                elif period == 'Last year':
                    cutoff_dt = now - timedelta(days=365)
                if cutoff_dt is not None:
                    from dateutil import parser as dateparse
                    filtered = []
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
                    self.log_msg(f'  -> {len(video_items)} videos within selected period ({period})')
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
        df['top_5_long_titles'] = df['top_5_long_titles'].apply(lambda x: json.dumps(x))
        df['top_5_shorts_titles'] = df['top_5_shorts_titles'].apply(lambda x: json.dumps(x))
        df['cta_counts'] = df['cta_counts'].apply(lambda x: json.dumps(x))
        df['top_topics'] = df['top_topics'].apply(lambda x: json.dumps(x))
        try:
            df.to_csv(fn, index=False)
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
