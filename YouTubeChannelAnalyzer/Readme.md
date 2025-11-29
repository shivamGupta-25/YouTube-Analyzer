# 📊 YouTube Channel Analyzer

A powerful desktop application to analyze YouTube channel performance with detailed metrics and insights. Perfect for content creators, marketers, and researchers who want to understand video performance trends.

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 🌟 Features

- ✅ **Flexible Channel Input**: Enter channel ID, full URL, username, or custom URL
- 📅 **Customizable Date Ranges**: Analyze videos from last 1/2/5 months or custom date range
- 📈 **Comprehensive Metrics**: Views, likes, comments, engagement ratios, and more
- 💾 **CSV Export**: Export all data for further analysis in Excel or Google Sheets
- 🎬 **Quick Video Access**: Open any video directly in your browser
- 🔍 **Sortable Columns**: Click any column header to sort data
- 🌐 **Unicode Support**: Works with channels in any language

---

## 📋 Table of Contents

- [Installation Guide](#-installation-guide)
- [Getting Your YouTube API Key](#-getting-your-youtube-api-key)
- [How to Use](#-how-to-use)
- [Understanding the Metrics](#-understanding-the-metrics)
- [Troubleshooting](#-troubleshooting)
- [FAQ](#-faq)

---

## 🚀 Installation Guide

### Step 1: Install Python

**Windows:**
1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run the installer
3. ✅ **IMPORTANT**: Check "Add Python to PATH" during installation
4. Click "Install Now"

**macOS:**
```bash
# Using Homebrew (recommended)
brew install python
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-tk
```

### Step 2: Verify Python Installation

Open Command Prompt (Windows) or Terminal (macOS/Linux) and type:

```bash
python --version
```

You should see something like `Python 3.8.0` or higher.

### Step 3: Download the Application

1. Download or clone this repository to your computer
2. Extract the files to a folder (e.g., `C:\YouTubeAnalyzer` or `~/YouTubeAnalyzer`)

### Step 4: Install Dependencies

Open Command Prompt/Terminal in the application folder and run:

```bash
pip install -r requirements.txt
```

This will install:
- `pandas` - For data processing
- `requests` - For API communication

**Note**: `tkinter` (the GUI library) comes pre-installed with Python.

---

## 🔑 Getting Your YouTube API Key

To use this application, you need a **free** YouTube Data API key from Google.

### Step-by-Step Guide:

#### 1. Go to Google Cloud Console
Visit: [https://console.cloud.google.com/](https://console.cloud.google.com/)

#### 2. Create a New Project
- Click "Select a project" at the top
- Click "New Project"
- Enter a project name (e.g., "YouTube Analyzer")
- Click "Create"

#### 3. Enable YouTube Data API v3
- In the search bar, type "YouTube Data API v3"
- Click on "YouTube Data API v3"
- Click "Enable"

#### 4. Create API Credentials
- Click "Create Credentials" button
- Select "API Key"
- Your API key will be generated (looks like: `AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`)
- **IMPORTANT**: Copy this key and keep it safe!

#### 5. (Optional) Restrict Your API Key
For security, you can restrict the key to only YouTube Data API:
- Click on your API key
- Under "API restrictions", select "Restrict key"
- Choose "YouTube Data API v3"
- Click "Save"

### API Quota Information

- **Free Tier**: 10,000 units per day
- **Cost per request**:
  - Search: 100 units
  - Video details: 1 unit
- **Example**: Analyzing a channel with 50 videos ≈ 150 units

This is usually sufficient for personal use. If you need more, you can request a quota increase.

---

## 📖 How to Use

### Step 1: Launch the Application

Open Command Prompt/Terminal in the application folder and run:

```bash
python YouTubeChannelAnalyzer.py
```

The application window will open.

### Step 2: Enter Your API Key

1. Paste your YouTube API key in the "YouTube API Key" field
2. The key is saved automatically in `config/api_key.json` for future use

### Step 3: Enter Channel Information

You can enter any of the following formats:

- **Channel ID**: `UCXuqSBlHAE6Xw-yeJA0Tunw` (starts with UC)
- **Channel URL**: `https://www.youtube.com/channel/UCXuqSBlHAE6Xw-yeJA0Tunw`
- **Custom URL**: `https://www.youtube.com/c/LinusTechTips`
- **User URL**: `https://www.youtube.com/user/LinusTechTips`
- **Username**: `LinusTechTips`

### Step 4: Select Date Range

Choose one of the preset ranges or use custom dates:

- **Last 1 Month**: Videos from the past 30 days
- **Last 2 Months**: Videos from the past 60 days
- **Last 5 Months**: Videos from the past 150 days
- **Custom Range**: Enter specific dates in YYYY-MM-DD format
  - Example: From `2024-01-01` To `2024-12-31`

### Step 5: Fetch Videos

Click the **🔍 Fetch Videos** button.

The application will:
1. Resolve the channel ID
2. Fetch all videos in the date range
3. Retrieve detailed statistics for each video
4. Calculate engagement metrics
5. Display results in the table

### Step 6: Analyze Results

- **Sort**: Click any column header to sort
- **View Video**: Select a row and click **🎬 Open Selected Video**
- **Export**: Click **💾 Export to CSV** to save data

---

## 📊 Understanding the Metrics

### Direct Metrics (from YouTube API)

These values come directly from YouTube's database:

#### 1. **Views** (`viewCount`)
- **What it is**: Total number of times the video has been watched
- **Significance**: Primary indicator of reach and popularity
- **Good benchmark**: Varies by niche; compare to your channel average

#### 2. **Likes** (`likeCount`)
- **What it is**: Total number of likes on the video
- **Significance**: Indicates positive audience sentiment
- **Note**: Dislikes are no longer public (YouTube removed them in 2021)

#### 3. **Comments** (`commentCount`)
- **What it is**: Total number of comments on the video
- **Significance**: Shows audience engagement and discussion level
- **Higher is better**: More comments = more engaged audience

#### 4. **Published Date** (`publishedAt`)
- **What it is**: When the video was uploaded
- **Significance**: Used to calculate time-based metrics
- **Format**: ISO 8601 (e.g., 2024-01-15T10:30:00Z)

#### 5. **Duration** (`durationSeconds`)
- **What it is**: Length of the video in seconds
- **Significance**: Longer videos may have different engagement patterns
- **Example**: 600 seconds = 10 minutes

---

### Calculated Metrics (computed by this app)

These metrics are calculated using formulas to provide deeper insights:

#### 1. **Average Views Per Day** (`avgViewsPerDay`)

**Formula:**
```
avgViewsPerDay = viewCount / daysSincePublish
```

**Example:**
- Video has 10,000 views
- Published 20 days ago
- avgViewsPerDay = 10,000 / 20 = **500 views/day**

**Significance:**
- Measures **velocity** of view accumulation
- Higher = faster growth
- Helps identify trending videos
- Useful for comparing videos of different ages

**What's Good:**
- Compare to your channel average
- Newer videos with high values are "trending"
- Declining values may indicate saturation

**Calculation Details:**
- Uses fractional days for accuracy (e.g., 20.5 days)
- Minimum 0.1 days (2.4 hours) to avoid division by zero for very new videos

---

#### 2. **Like-to-View Ratio** (`likeToViewRatio`)

**Formula:**
```
likeToViewRatio = likeCount / viewCount
```

**Example:**
- Video has 500 likes
- Video has 10,000 views
- likeToViewRatio = 500 / 10,000 = **0.05 (5%)**

**Significance:**
- Measures **positive engagement quality**
- Shows what percentage of viewers liked the video
- Independent of video age or total views

**What's Good:**
- **Excellent**: > 0.08 (8%+)
- **Good**: 0.04 - 0.08 (4-8%)
- **Average**: 0.02 - 0.04 (2-4%)
- **Low**: < 0.02 (< 2%)

**Interpretation:**
- Higher ratio = content resonates well with audience
- Low ratio may indicate clickbait or disappointing content
- Compare across your videos to find what works

---

#### 3. **Comment-to-View Ratio** (`commentToViewRatio`)

**Formula:**
```
commentToViewRatio = commentCount / viewCount
```

**Example:**
- Video has 150 comments
- Video has 10,000 views
- commentToViewRatio = 150 / 10,000 = **0.015 (1.5%)**

**Significance:**
- Measures **discussion engagement**
- Shows what percentage of viewers commented
- Indicates controversial or thought-provoking content

**What's Good:**
- **Excellent**: > 0.03 (3%+)
- **Good**: 0.01 - 0.03 (1-3%)
- **Average**: 0.005 - 0.01 (0.5-1%)
- **Low**: < 0.005 (< 0.5%)

**Interpretation:**
- Higher ratio = more engaged, vocal audience
- Tutorial/educational content often has higher ratios (questions)
- Entertainment content may have lower ratios
- Very high ratios may indicate controversy

---

#### 4. **Overall Engagement Rate** (`engagementRate`)

**Formula:**
```
engagementRate = ((likeCount + commentCount) / viewCount) × 100
```

**Example:**
- Video has 500 likes
- Video has 150 comments
- Video has 10,000 views
- engagementRate = ((500 + 150) / 10,000) × 100 = **6.5%**

**Significance:**
- Measures **total interaction percentage**
- Combines all engagement actions into one metric
- Shows what percentage of viewers actively engaged
- Higher percentage = more engaging content

**What's Good:**
- **Excellent**: > 10% (highly engaging)
- **Very Good**: 6-10% (strong engagement)
- **Good**: 3-6% (above average)
- **Average**: 1-3% (typical)
- **Low**: < 1% (needs improvement)

**Interpretation:**
- Simple, easy-to-understand engagement metric
- Useful for quick comparison across videos
- Combines likes and comments into total interaction count
- Higher rates indicate content that motivates viewers to act

---

#### 5. **Engagement Score** (`engagementScore`)

**Formula:**
```
engagementScore = (
    (likeToViewRatio × 50) +
    (commentToViewRatio × 30) +
    (min(avgViewsPerDay/1000, 1.0) × 20)
) × 100 ÷ 10
```

**Scale:** 1.0 to 10.0

**Example:**
- likeToViewRatio = 0.05 (5%)
- commentToViewRatio = 0.015 (1.5%)
- avgViewsPerDay = 500
- Calculation:
  - Like component: 0.05 × 50 = 2.5
  - Comment component: 0.015 × 30 = 0.45
  - Velocity component: (500/1000) × 20 = 10
  - Raw score: 2.5 + 0.45 + 10 = 12.95
  - Final score: 12.95 × 100 ÷ 10 = **12.95** → capped at **10.0**

**Significance:**
- **Composite metric** combining multiple engagement signals
- Weighted formula emphasizing different engagement types
- Normalized 1-10 scale for easy interpretation
- Accounts for both quality (ratios) and velocity (growth)

**Component Weights:**
- **50% - Likes**: Primary engagement indicator
- **30% - Comments**: Deeper engagement signal
- **20% - Velocity**: Trending/growth bonus (capped at 1000 views/day)

**What's Good:**
- **9-10**: Exceptional (viral/highly engaging content)
- **7-8**: Very Good (strong performer)
- **5-6**: Good (above average)
- **3-4**: Moderate (average performance)
- **1-2**: Low (needs improvement)

**Interpretation:**
- Single number to compare video performance
- Balances engagement quality with growth velocity
- Higher scores indicate content that resonates well AND gains traction
- Useful for quickly identifying top-performing videos
- Sort by this column to find your best content

---

#### 6. **Days Since Publish** (`daysSincePublish`)

**Formula:**
```
daysSincePublish = (currentTime - publishedAt) / 86400 seconds
```

**Significance:**
- Used in calculating avgViewsPerDay
- Helps contextualize performance
- Fractional days for precision (e.g., 5.3 days)

---

### 📈 How to Use These Metrics Together

#### Finding Your Best Content
1. Sort by **engagementScore** (descending) to instantly see top performers
2. Look for videos with scores 7+ for exceptional content
3. Analyze patterns in titles, topics, or formats of high-scoring videos
4. Create more content like your top performers

#### Quick Performance Overview
1. Sort by **engagementRate** (descending) for overall engagement snapshot
2. Videos with 6%+ engagement rate are strong performers
3. Compare engagement rate across different content types
4. Identify which topics drive the most interaction

#### Identifying Trending Videos
1. Sort by **avgViewsPerDay** (descending)
2. Videos with high values are gaining traction
3. Consider promoting these on social media
4. High velocity + high engagement score = viral potential

#### Understanding Engagement Quality
1. Compare **likeToViewRatio** and **commentToViewRatio**
2. High likes + low comments = entertaining but not discussion-worthy
3. High comments + moderate likes = thought-provoking or controversial
4. Both high = exceptional content that resonates deeply

#### Benchmarking Performance
1. Export data to CSV
2. Calculate average metrics for your channel
3. Compare individual videos to channel average
4. Identify outliers (both good and bad)
5. Use **engagementScore** as your primary benchmark metric

---

## 🔧 Troubleshooting

### "Missing API Key" Error
- Make sure you've entered your API key in the field
- Check that the key doesn't have extra spaces
- Verify the key is valid in Google Cloud Console

### "Could not resolve channel ID" Error
- Double-check the channel URL or ID
- Try using the direct channel ID (starts with UC)
- Make sure the channel exists and is public

### "API Error" or "Quota Exceeded"
- You've hit the daily quota limit (10,000 units)
- Wait until the next day (resets at midnight Pacific Time)
- Or request a quota increase in Google Cloud Console

### "No videos found"
- The channel may not have videos in the selected date range
- Try expanding the date range
- Check if the channel has any public videos

### Application Won't Start
- Verify Python is installed: `python --version`
- Check dependencies are installed: `pip install -r requirements.txt`
- On Linux, ensure tkinter is installed: `sudo apt-get install python3-tk`

### CSV Export Issues
- Make sure you have write permissions in the save location
- Try saving to a different folder (e.g., Desktop)
- Close the CSV file if it's already open in Excel

---

## ❓ FAQ

### Is this free to use?
Yes! The application is free. You only need a free YouTube API key from Google.

### Will I be charged for the API?
No, the free tier (10,000 units/day) is sufficient for most personal use. You won't be charged unless you manually enable billing.

### Can I analyze any YouTube channel?
Yes, as long as the channel is public. Private or unlisted videos won't be included.

### Why can't I see dislikes?
YouTube removed public dislike counts in December 2021. The API no longer provides this data.

### How accurate are the metrics?
100% accurate! All data comes directly from YouTube's official API, and calculations use industry-standard formulas.

### Can I analyze multiple channels?
Yes, but one at a time. Simply enter a different channel ID and click Fetch Videos again.

### How do I update my API key?
Just paste the new key in the API Key field. It will be saved automatically.

### Can I analyze videos older than 5 months?
Yes! Use the "Custom Range" option and enter any date range you want.

### What file format is the export?
CSV (Comma-Separated Values), which opens in Excel, Google Sheets, and most data analysis tools.

### Is my API key stored securely?
The key is stored locally on your computer in `config/api_key.json`. It's never sent anywhere except to YouTube's official API.

---

## 📝 Technical Details

### System Requirements
- **Python**: 3.8 or higher
- **Operating System**: Windows, macOS, or Linux
- **RAM**: 512 MB minimum
- **Disk Space**: 50 MB

### Dependencies
- `pandas` - Data manipulation and analysis
- `requests` - HTTP library for API calls
- `tkinter` - GUI framework (included with Python)

### API Endpoints Used
- `search.list` - Fetch video IDs for a channel
- `videos.list` - Fetch detailed video statistics
- `channels.list` - Resolve channel IDs and get channel info

### Data Privacy
- All data is processed locally on your computer
- No data is sent to any third-party servers
- API key is stored locally in `config/api_key.json`

---

## 📄 License

This project is open source and available under the MIT License.

---

## 🤝 Support

If you encounter issues:
1. Check the [Troubleshooting](#-troubleshooting) section
2. Review the [FAQ](#-faq)
3. Verify your API key is valid and has quota remaining

---

## 🎯 Tips for Best Results

1. **Start Small**: Test with a 1-month range first
2. **Monitor Quota**: Large channels can use significant quota
3. **Export Regularly**: Save your data for historical comparison
4. **Compare Metrics**: Look for patterns across multiple videos
5. **Use Custom Ranges**: Analyze specific campaigns or time periods

---

**Happy Analyzing! 📊🚀**
