# YouTube Channel Analyzer

A comprehensive tool for analyzing YouTube channels and extracting detailed metrics to help understand channel performance, content strategy, and growth potential.

## Features

- **Comprehensive Channel Analysis**: Analyze multiple YouTube channels simultaneously
- **Robust Metrics**: Extract 22+ detailed metrics including engagement rates, upload frequency, content analysis, and growth predictions
- **Flexible Time Periods**: Filter analysis by time periods (Last 7 days, 30 days, 90 days, 1 year, or All time)
- **Customizable Sample Size**: Choose how many videos to analyze per channel (10-1000) or analyze all videos
- **CSV Export**: Export all metrics to CSV for further analysis
- **GUI Interface**: User-friendly graphical interface built with Tkinter
- **Batch Processing**: Analyze multiple channels from a file or paste directly

## Requirements

- Python 3.9 or higher
- YouTube Data API v3 key ([Get one here](https://console.cloud.google.com/apis/credentials))

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up your YouTube API key (see API Key Setup below)

### Note for Linux Users

If you encounter issues with the GUI, you may need to install tkinter separately:
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Arch Linux
sudo pacman -S tk
```

## API Key Setup

### Option 1: Configuration File (Recommended)

1. Create a `config` directory in the project root
2. Create `config/api_key.json` with the following format:
   ```json
   {
     "api_key": "YOUR_YOUTUBE_API_KEY_HERE"
   }
   ```
3. The application will automatically load the key on startup

### Option 2: Environment Variable

Set the environment variable:
```bash
# Windows (PowerShell)
$env:YT_API_KEY="YOUR_YOUTUBE_API_KEY_HERE"

# Linux/Mac
export YT_API_KEY="YOUR_YOUTUBE_API_KEY_HERE"
```

### Option 3: GUI Input

You can also enter your API key directly in the GUI field, which will override the config file.

## Usage

1. Run the application:
   ```bash
   python main.py
   ```

2. **Enter Channel Information**:
   - Paste channel URLs or IDs (one per line) in the text area
   - Supported formats:
     - Channel ID: `UCxxxxxxxxxxxxxxxxxxxxxxxxxx`
     - Channel URL: `https://www.youtube.com/channel/UCxxxxxxxxxxxxxxxxxxxxxxxxxx`
     - Custom URL: `https://www.youtube.com/c/ChannelName`
     - Handle: `@ChannelName`
   - Or click "Load from file" to load from a text file

3. **Configure Analysis**:
   - **Sample Size**: Number of videos to analyze per channel (10-1000)
   - **All Videos**: Check to analyze all videos (ignores sample size)
   - **Period**: Filter videos by time period (All time, Last 7/30/90 days, Last year)

4. **Run Analysis**:
   - Click "Fetch & Analyze" to start
   - Progress is shown in the progress bar and log area
   - Results appear in the log area with insights and suggestions

5. **Export Results**:
   - Click "Export CSV" to save all metrics to a CSV file
   - The CSV includes all 22 metrics for each analyzed channel

## Metrics Explained

The tool exports the following metrics to CSV:

### Basic Channel Information
- **channel_id**: YouTube channel ID
- **channel_title**: Channel name
- **subscribers**: Current subscriber count
- **channel_total_views**: Total lifetime views for the channel
- **sample_videos_analyzed**: Number of videos analyzed in this sample

### Upload Metrics
- **avg_uploads_per_week**: Average number of videos uploaded per week
- **avg_uploads_long_per_week**: Average long-form videos (>60 seconds) per week
- **avg_uploads_shorts_per_week**: Average YouTube Shorts (≤60 seconds) per week

### Content Duration
- **avg_runtime_long_seconds**: Average duration of long-form videos in seconds
- **avg_runtime_shorts_seconds**: Average duration of Shorts in seconds

### Engagement Metrics
- **engagement_pct_popular_videos**: Average engagement rate (likes + comments / views) for top 10% most viewed videos
- **engagement_rate_overall_pct**: Overall engagement rate across all analyzed videos
- **avg_views_sample**: Average views per video in the analyzed sample

### Content Analysis
- **top_5_long_titles**: Titles of top 5 most-viewed long-form videos
- **top_5_shorts_titles**: Titles of top 5 most-viewed Shorts
- **top_topics**: Most common topics/keywords found in video titles
- **cta_counts**: Count of call-to-action keywords found in descriptions (subscribe, download, etc.)

### Predictions
- **est_views_next_6_months**: Estimated total views for next 6 months (based on trend analysis)
- **est_subs_next_6_months**: Estimated new subscribers in next 6 months (based on view-to-sub conversion)

### Quality Scores
- **quality_score_0_10**: Overall content quality score (0-10) based on:
  - Average video length (40%)
  - Engagement rate (40%)
  - Topic diversity (20%)
- **community_score_0_10**: Community engagement score (0-10) based on:
  - Average comments per video (60%)
  - Community presence indicators in descriptions (40%)

### Monetization
- **monetization_inference**: Detected monetization strategies (sponsorships, affiliates, etc.) or "None Detected"

## Metric Calculation Methodology

This section explains how each metric is calculated to ensure transparency and accuracy.

### Basic Channel Information

- **channel_id**: Retrieved directly from YouTube Data API v3 (`channels().list()`)
- **channel_title**: Retrieved from API response (`snippet.title`)
- **subscribers**: Retrieved from API statistics (`statistics.subscriberCount`). Returns `None` if subscriber count is hidden by the channel.
- **channel_total_views**: Retrieved from API statistics (`statistics.viewCount`), represents lifetime channel views
- **sample_videos_analyzed**: Count of videos in the analyzed dataset (after applying date filters if specified)

### Upload Metrics

All upload frequency metrics use only videos with valid publication dates to ensure accurate time-based calculations.

- **avg_uploads_per_week**: 
  - Formula: `(Number of videos with valid dates) / (Time span in weeks)`
  - Time span: Calculated as `(Last video date - First video date) / 7`
  - Minimum time span: 1 day (0.143 weeks) to avoid division by zero
  - Videos without dates are excluded from this calculation

- **avg_uploads_long_per_week**: 
  - Same calculation as above, but only includes videos with duration > 60 seconds
  - Shorts threshold: 60 seconds (videos ≤60s are considered Shorts)

- **avg_uploads_shorts_per_week**: 
  - Same calculation as above, but only includes videos with duration ≤ 60 seconds

### Content Duration

- **avg_runtime_long_seconds**: 
  - Calculated as mean duration (in seconds) of all videos with duration > 60 seconds
  - Returns 0.0 if no long-form videos exist
  - Duration is parsed from ISO 8601 format (e.g., "PT5M30S" = 330 seconds)

- **avg_runtime_shorts_seconds**: 
  - Calculated as mean duration (in seconds) of all videos with duration ≤ 60 seconds
  - Returns 0.0 if no Shorts exist

### Engagement Metrics

- **engagement_pct_popular_videos**: 
  - Selects top 10% of videos by views (minimum 1 video)
  - Formula: `Mean((Likes + Comments) / Views) × 100` for selected videos
  - Videos with zero views are excluded to avoid division by zero
  - Returns 0 if no videos have views > 0

- **engagement_rate_overall_pct**: 
  - Formula: `(Sum of all Likes + Sum of all Comments) / Sum of all Views × 100`
  - Calculated across all analyzed videos
  - Returns 0.0 if total views is zero

- **avg_views_sample**: 
  - Simple arithmetic mean of views across all analyzed videos
  - Formula: `Sum(Views) / Number of videos`

### Content Analysis

- **top_5_long_titles**: 
  - Selects 5 videos with highest views from long-form videos (>60s)
  - Returns list of titles, empty list if no long-form videos exist

- **top_5_shorts_titles**: 
  - Selects 5 videos with highest views from Shorts (≤60s)
  - Returns list of titles, empty list if no Shorts exist

- **top_topics**: 
  - Extracts tokens from video titles using regex pattern `[A-Za-z0-9+#]+`
  - Filters out common stopwords: 'the', 'and', 'for', 'with', 'to', 'a', 'in', 'of', 'is', 'how', 'what', 'learn', 'tutorial', 'lesson', 'video', 'introduction', 'session'
  - Filters out tokens with length ≤ 2 characters
  - Returns top 20 most common keywords

- **cta_counts**: 
  - Scans video descriptions (case-insensitive) for CTA keywords
  - Keywords: 'subscribe', 'join', 'enroll', 'download', 'signup', 'sign up', 'visit', 'buy', 'purchase', 'link in description', 'link in bio', 'course', 'free course', 'patreon', 'donate', 'sponsor', 'sponsored', 'affiliate', 'discount'
  - Returns dictionary with keyword counts (top 10 most common)

### Predictions

- **est_views_next_6_months**: 
  - Groups videos by week (using publication date)
  - Calculates weekly view totals
  - Uses linear regression (numpy.polyfit) on weekly view data to project trend
  - Projects forward 26 weeks (6 months)
  - Fallback methods:
    - If regression fails or produces negative values: Uses average of recent 8 weeks × 26
    - If only 1 week of data: Uses that week's views × 26
    - If no valid data: Returns 0
  - All negative predictions are clipped to 0

- **est_subs_next_6_months**: 
  - Formula: `est_views_next_6_months × 0.001` (0.1% view-to-subscriber conversion rate)
  - This is a conservative estimate based on typical YouTube conversion rates
  - Returns integer value

### Quality Scores

- **quality_score_0_10**: 
  - Weighted composite score with three components:
    1. **Runtime Score (40%)**: 
       - For channels with long videos: `min(1.0, avg_runtime_long / 1200)` (normalized to 20 minutes)
       - For shorts-only channels: `min(1.0, avg_runtime_shorts / 30)` (normalized to 30 seconds)
    2. **Engagement Score (40%)**: `min(1.0, engagement_rate_overall × 10)`
    3. **Topic Diversity Score (20%)**: `min(1.0, (unique_tokens / total_tokens) × 2)`
  - Final score: `(Runtime × 0.4 + Engagement × 0.4 + Diversity × 0.2) × 10`
  - Rounded to 2 decimal places

- **community_score_0_10**: 
  - Weighted composite score with two components:
    1. **Comments Score (60%)**: `min(1.0, avg_comments_per_video / 10)` (normalized to 10 comments)
    2. **Community Presence (40%)**: `Proportion of videos with community keywords`
     - Community keywords: 'discord', 'telegram', 'community', 'facebook group', 'paid community', 'newsletter', 'live session', 'q&a', 'ask your doubt', 'join us'
     - Calculated as: `Videos with at least one community keyword / Total videos`
  - Final score: `(Comments × 0.6 + Presence × 0.4) × 10`
  - Rounded to 2 decimal places

### Monetization

- **monetization_inference**: 
  - Scans video descriptions (case-insensitive) for monetization keywords
  - Monetization keywords: 'sponsor', 'sponsored', 'affiliate', 'udemy', 'coursera', 'patreon', 'merch', 'adsense', 'brand'
  - Returns "Detected: [top 5 keywords]" if monetization keywords found
  - Returns "Sponsorship Mentions" if 'sponsor' found in CTA keywords
  - Returns "None Detected" if no monetization indicators found

### Edge Cases and Data Handling

- **Missing Data**: All metrics handle missing or invalid data gracefully:
  - Missing subscriber counts return `None` (distinguishes from 0)
  - Videos without publication dates are excluded from time-based calculations
  - Division by zero is prevented with `max(1, denominator)` guards
  - NaN and infinite values are filtered using `_safe_float()` and `_safe_int()` helpers

- **Date Handling**: 
  - Publication dates are parsed from ISO 8601 format
  - Timezone-aware dates are converted to naive datetimes for consistency
  - Invalid dates are coerced to NaT and excluded from date-based calculations

- **Duration Parsing**: 
  - ISO 8601 duration format (e.g., "PT1H30M45S") is parsed to total seconds
  - Handles days, hours, minutes, and seconds components
  - Returns 0 for invalid or missing durations

## Troubleshooting

### API Quota Exceeded
- YouTube API has daily quota limits (default: 10,000 units/day)
- Each channel analysis uses multiple API calls
- Solution: Wait for quota reset or request quota increase from Google Cloud Console

### Channel Not Found
- Verify the channel URL/ID is correct
- Some channels may be private or deleted
- Try using the channel ID instead of custom URL

### No Videos Found
- Channel may have no public videos
- Videos may be outside the selected time period
- Try selecting "All time" period

### Permission Errors (CSV Export)
- Close the CSV file if it's open in Excel or another program
- Choose a different save location
- Check file/folder permissions

### GUI Not Appearing
- Ensure Python 3.9+ is installed
- On Linux, install tkinter (see Installation section)
- Try running from command line to see error messages

## API Quota Information

Each analysis operation consumes YouTube API quota:
- Channel lookup: ~1 unit
- Video list fetch: ~1 unit per 50 videos
- Video details: ~1 unit per 50 videos

**Example**: Analyzing 200 videos from one channel uses approximately:
- 1 unit (channel) + 4 units (video list) + 4 units (video details) = **9 units**

Plan your analysis accordingly to stay within your daily quota.

## License

This project is provided as-is for educational and analytical purposes.

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.
