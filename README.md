# YouTube Analyzer & Scrapper

A collection of Python desktop tools built during my internship at **PrepRoute** to analyze and extract data from YouTube channels using the YouTube Data API v3.

---

## Projects

### 1. 📊 YouTube Metric Extractor (`YouTube-Metric-Extractor/`)

A desktop GUI app (built with `tkinter`) for performing **batch analysis** of multiple YouTube channels and exporting a comprehensive metrics report to CSV.

**Features:**
- Analyze multiple channels at once (paste one URL/ID per line, or load from a `.txt` file)
- Filter videos by preset time periods (Last 7/30/90 days, Last year) or a custom date range
- Extracts **20+ metrics** per channel including:
  - Subscribers, total views, upload frequency
  - Long video vs. Shorts breakdown (count, avg duration, top titles)
  - Engagement rate, call-to-action keyword counts, top topics
  - Estimated views & subscribers over the next 6 months
  - Monetization strategy inference, quality score (0–10)
- Export results to a timestamped CSV with human-readable column headers
- Real-time progress bar and analysis log

**Run:**
```bash
cd YouTube-Metric-Extractor
pip install -r requirements.txt
python main.py
```

**API Key Setup:** Place your YouTube Data API v3 key in `config/api_key.json`:
```json
{ "api_key": "YOUR_API_KEY_HERE" }
```

---

### 2. 🔍 YouTube Channel Video Scrapper (`YouTubeChannelAnalyzer/`)

A modern desktop GUI app (built with `customtkinter`) for scraping **detailed video-level data** from a single YouTube channel and exporting it to CSV.

**Features:**
- Accepts channel input as `@handle`, `UC...` ID, or full YouTube URL
- Date range selection: preset options (Last 1/2/5 Months) or a custom calendar picker
- Extracts per-video data: title, description, views, likes, comments, duration, tags, category, privacy status, thumbnail URL, live stream type
- Threaded fetching (non-blocking UI)
- Exports a timestamped CSV named after the channel

**Run:**
```bash
cd YouTubeChannelAnalyzer
pip install customtkinter tkcalendar google-api-python-client pandas isodate
python YouTube_ChannelVideoScrapper.py
```

**API Key Setup:** Place your key in `config/api_key.json`:
```json
{ "api_key": "YOUR_API_KEY_HERE" }
```

---

## Requirements

- Python 3.8+
- A valid [YouTube Data API v3](https://console.cloud.google.com/) key

---

## About

Built as part of my internship at **PrepRoute** to support competitive research and content analysis on YouTube channels.
