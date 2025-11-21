# YouTube Metric Extractor - Complete Guide

## 📋 Table of Contents
- [What is This Tool?](#what-is-this-tool)
- [Initial Setup](#initial-setup)
- [How to Use](#how-to-use)
- [Understanding the Metrics](#understanding-the-metrics)
- [Technical Details](#technical-details)
- [Troubleshooting](#troubleshooting)

---

## 🎯 What is This Tool?

The **YouTube Metric Extractor** is a desktop application that analyzes YouTube channels and provides detailed insights through **22 different metrics**. Think of it as a comprehensive report card for YouTube channels that helps you understand:

- How often a channel uploads videos
- How engaged their audience is
- What topics they cover
- How their channel might grow in the future
- Whether they're building a community
- Signs of monetization strategies

**Who is this for?**
- Content creators analyzing their own channels
- Marketers researching competitor channels
- Researchers studying YouTube trends
- Anyone interested in YouTube channel analytics

---

## 🚀 Initial Setup

### Step 1: Install Python

**What is Python?** Python is a programming language that this tool is built with. You need it installed on your computer to run the application.

**How to install:**
1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Download Python 3.8 or newer
3. Run the installer
4. ✅ **IMPORTANT**: Check the box that says "Add Python to PATH" during installation

**How to verify it's installed:**
Open Command Prompt (Windows) or Terminal (Mac/Linux) and type:
```bash
python --version
```
You should see something like `Python 3.11.0`

### Step 2: Install Required Libraries

**What are libraries?** Libraries are pre-written code that this tool uses to work with YouTube's data and process information.

**How to install:**
1. Open Command Prompt/Terminal
2. Navigate to the tool's folder:
   ```bash
   cd "path\to\YouTube-Metric-Extractor"
   ```
3. Run this command:
   ```bash
   pip install -r requirements.txt
   ```

This will install:
- **google-api-python-client**: Connects to YouTube's servers
- **pandas**: Organizes and analyzes data
- **numpy**: Performs mathematical calculations
- **python-dateutil**: Handles dates and times

### Step 3: Get a YouTube API Key

**What is an API Key?** An API key is like a password that lets this tool access YouTube's data. It's free and provided by Google.

**How to get one:**

1. **Go to Google Cloud Console**
   - Visit: [console.cloud.google.com](https://console.cloud.google.com/)
   - Sign in with your Google account

2. **Create a New Project**
   - Click "Select a project" at the top
   - Click "New Project"
   - Name it (e.g., "YouTube Analyzer")
   - Click "Create"

3. **Enable YouTube Data API**
   - In the search bar, type "YouTube Data API v3"
   - Click on it
   - Click "Enable"

4. **Create API Key**
   - Click "Credentials" in the left sidebar
   - Click "Create Credentials" → "API Key"
   - Copy the key that appears (it looks like: `AIzaSyD...`)

5. **Save Your API Key**
   - When you first run the tool, it will create a file: `config/api_key.json`
   - Open this file and replace `YOUR_YOUTUBE_API_KEY_HERE` with your actual key
   - OR simply paste it in the application window when you run it

**Important Notes:**
- Keep your API key private (don't share it publicly)
- Free quota: 10,000 units per day (enough for ~100 channels)
- Each channel analysis uses about 100 units

---

## 💻 How to Use

### Starting the Application

1. Open Command Prompt/Terminal
2. Navigate to the tool's folder
3. Run:
   ```bash
   python main.py
   ```

A window will open with the application interface.

### Using the Interface

The interface is organized into sections:

#### 1. **API Configuration**
- Paste your YouTube API key here
- The tool remembers it for next time

#### 2. **Channel Input**
- Enter YouTube channel URLs or IDs (one per line)
- Accepted formats:
  - Full URL: `https://www.youtube.com/@channelname`
  - Channel ID: `UCxxxxxxxxxxxxxx`
  - Username: `@channelname`

**Example:**
```
https://www.youtube.com/@veritasium
https://www.youtube.com/@mkbhd
@3blue1brown
```

#### 3. **Filter Options**

**Time Period:** Choose which videos to analyze
- **All time**: Analyzes all videos ever uploaded
- **Last 7 days**: Only videos from the past week
- **Last 30 days**: Only videos from the past month
- **Last 90 days**: Only videos from the past 3 months
- **Last year**: Only videos from the past 365 days

**Custom Date Range:** For specific time periods
- Check "Use custom date range"
- Enter dates in format: YYYY-MM-DD (e.g., 2024-01-01)
- You can specify:
  - Only "From" date (all videos after that date)
  - Only "To" date (all videos before that date)
  - Both (videos within that range)

#### 4. **Action Buttons**

- **📁 Load from File**: Load channel URLs from a text file
- **▶ Fetch & Analyze**: Start analyzing the channels
- **💾 Export CSV**: Save results to a spreadsheet file

#### 5. **Progress**
Shows how many channels have been processed

#### 6. **Analysis Log**
Displays real-time information about what's happening:
- How many videos were found
- How many passed the date filter
- Any errors encountered

### Exporting Results

After analysis completes:
1. Click "💾 Export CSV"
2. A default filename will be suggested: `youtube_analysis_YYYY-MM-DD_HH-MM.csv`
3. You can keep the default name or change it
4. Choose where to save the file
5. Open it in Excel, Google Sheets, or any spreadsheet program

The CSV file contains one row per channel with all 22 metrics using **human-readable column headers** for easy understanding.

**Example Column Headers:**
- "Channel Name" (instead of technical "channel_title")
- "Average Uploads Per Week" (instead of "avg_uploads_per_week")
- "Quality Score (0-10)" (instead of "quality_score_0_10")
- "Estimated Views (6 Months)" (instead of "est_views_next_6_months")

---

## 📊 Understanding the Metrics

### Overview: 22 Metrics in 3 Categories

1. **Direct Metrics** (7): Fetched directly from YouTube
2. **Calculated Metrics** (13): Computed from video data
3. **Predictive Metrics** (2): Forecasts based on trends

---

### 📌 Direct API Metrics (From YouTube)

These are pulled directly from YouTube's database without any calculation.

#### 1. **Channel ID**
- **What it is**: Unique identifier for the channel
- **Example**: `UCxxxxxxxxxxxxxx`
- **Why it matters**: Used to uniquely identify channels in databases

#### 2. **Channel Title**
- **What it is**: The channel's display name
- **Example**: "Veritasium"
- **Why it matters**: Human-readable channel identification

#### 3. **Subscribers**
- **What it is**: Total number of subscribers
- **Example**: 1,500,000
- **Why it matters**: Indicates channel size and reach
- **Note**: May show as "hidden" if the creator chose to hide it

#### 4. **Channel Total Views**
- **What it is**: All-time views across all videos
- **Example**: 500,000,000
- **Why it matters**: Shows overall channel popularity and longevity

#### 5. **Video Views** (per video)
- **What it is**: Number of times each video was watched
- **How it's used**: To calculate averages and identify popular content

#### 6. **Video Likes** (per video)
- **What it is**: Number of likes each video received
- **How it's used**: To measure engagement

#### 7. **Video Comments** (per video)
- **What it is**: Number of comments on each video
- **How it's used**: To measure audience interaction

---

### 🧮 Calculated Metrics (Computed from Data)

These metrics are calculated by analyzing the video data.

#### 8. **Sample Videos Analyzed**
- **What it is**: How many videos were included in the analysis
- **How it's calculated**: Count of videos after applying date filters
- **Example**: 150 videos
- **Why it matters**: Shows the data size used for calculations

#### 9. **Average Uploads Per Week**
- **What it is**: How often the channel uploads (all video types)
- **How it's calculated**: 
  ```
  Total videos ÷ Number of weeks between first and last video
  ```
- **Example**: 2.5 uploads/week
- **Why it matters**: Shows upload consistency
- **Special handling**: Channels with only 1 video show 1 upload/week (not inflated)

#### 10. **Average Uploads Long Per Week**
- **What it is**: Upload frequency for long-form videos (over 60 seconds)
- **How it's calculated**: Same as above, but only counting long videos
- **Example**: 1.8 uploads/week
- **Why it matters**: Shows focus on traditional YouTube content

#### 11. **Average Uploads Shorts Per Week**
- **What it is**: Upload frequency for YouTube Shorts (60 seconds or less)
- **How it's calculated**: Same as above, but only counting shorts
- **Example**: 0.7 uploads/week
- **Why it matters**: Shows adoption of Shorts format
- **Note**: YouTube defines Shorts as ≤60 seconds

#### 12. **Average Runtime Long (seconds)**
- **What it is**: Average length of long-form videos
- **How it's calculated**: 
  ```
  Sum of all long video durations ÷ Number of long videos
  ```
- **Example**: 1,200 seconds (20 minutes)
- **Why it matters**: Indicates content depth and style

#### 13. **Average Runtime Shorts (seconds)**
- **What it is**: Average length of Shorts
- **How it's calculated**: Same as above, for shorts only
- **Example**: 45 seconds
- **Why it matters**: Shows how the creator uses the Shorts format

#### 14. **Engagement % Popular Videos**
- **What it is**: Engagement rate for the top 10% most-viewed videos
- **How it's calculated**: 
  ```
  For top 10% videos:
  ((Total Likes + Total Comments) ÷ Total Views) × 100
  ```
- **Example**: 5.2%
- **Why it matters**: Shows how engaged the audience is on hit videos
- **Good benchmark**: 3-6% is considered good engagement

#### 15. **Top 5 Long Titles**
- **What it is**: Titles of the 5 most-viewed long-form videos
- **How it's calculated**: Sorted by view count, top 5 selected
- **Why it matters**: Shows what content resonates most with the audience

#### 16. **Top 5 Shorts Titles**
- **What it is**: Titles of the 5 most-viewed Shorts
- **How it's calculated**: Same as above, for shorts only
- **Why it matters**: Identifies successful short-form content

#### 17. **CTA Counts**
- **What it is**: Frequency of call-to-action keywords in video descriptions
- **How it's calculated**: Counts occurrences of keywords like:
  - subscribe, join, enroll, download, signup
  - link in description, course, patreon, sponsor
  - buy, purchase, affiliate, discount
- **Example**: {"subscribe": 45, "patreon": 12, "course": 8}
- **Why it matters**: Shows marketing and monetization strategies

#### 18. **Top Topics**
- **What it is**: Most common meaningful words in video titles
- **How it's calculated**: 
  1. Extract all words from video titles
  2. Remove common words (stopwords): the, and, how, tutorial, etc.
  3. Count frequency of remaining words
  4. Return top 20
- **Example**: ["python", "machine", "learning", "data", "science"]
- **Why it matters**: Shows channel's content focus
- **Note**: Uses 40+ stopwords to filter out filler words

#### 19. **Average Views Sample**
- **What it is**: Average views across all analyzed videos
- **How it's calculated**: 
  ```
  Total views of all videos ÷ Number of videos
  ```
- **Example**: 125,000 views
- **Why it matters**: Shows typical video performance

#### 20. **Engagement Rate Overall %**
- **What it is**: Overall engagement across all videos in the analyzed sample
- **How it's calculated**: 
  ```
  ((Total Likes + Total Comments) ÷ Total Views) × 100
  ```
- **Example**: 3.8%
- **Why it matters**: Measures overall audience interaction and content resonance
- **Interpretation Guide**:
  - **5%+**: Exceptional engagement - highly interactive audience
  - **3-5%**: Good engagement - audience is actively participating
  - **2-3%**: Average engagement - typical for most channels
  - **1-2%**: Below average - may need to improve call-to-actions or content quality
  - **<1%**: Low engagement - content may not be resonating with audience
- **Factors that influence this metric**:
  - Content quality and relevance
  - Call-to-action effectiveness (asking viewers to like/comment)
  - Audience loyalty and community strength
  - Video topic controversy or discussion-worthiness
  - Channel size (smaller channels often have higher engagement rates)
- **How to improve**:
  - Ask engaging questions in videos
  - Respond to comments to encourage discussion
  - Create content that sparks conversation
  - Add clear calls-to-action for likes and comments
  - Build a community around your content

#### 21. **Quality Score (0-10)**
- **What it is**: A composite score that evaluates overall content quality based on multiple factors
- **How it's calculated**: Weighted average of 3 key components:
  
  **Component 1: Runtime Score (40% weight)**
  - For long-form videos: Normalized to 20 minutes (1200 seconds) as the baseline
    - Videos ≥20 minutes get maximum runtime score
    - Shorter videos get proportional scores (e.g., 10-minute video = 0.5 score)
  - For shorts-only channels: Normalized to 30 seconds as the baseline
    - This prevents unfairly penalizing channels that focus exclusively on Shorts
  - **Rationale**: Longer videos often indicate more in-depth, valuable content
  
  **Component 2: Engagement Score (40% weight)**
  - Based on overall engagement rate: (Likes + Comments) / Views
  - Normalized assuming 10% engagement = perfect score
    - 10% engagement = 1.0 score
    - 5% engagement = 0.5 score
    - Capped at 1.0 for channels exceeding 10%
  - **Rationale**: High engagement indicates content resonates with audience
  
  **Component 3: Topic Diversity Score (20% weight)**
  - Measures variety in content topics from video titles
  - Calculated as: (Unique meaningful words) / (Total meaningful words)
  - Normalized assuming 50% unique topics = perfect score
    - 50%+ unique = 1.0 score
    - 25% unique = 0.5 score
  - **Rationale**: Diverse topics show versatility and broader appeal
  
  **Final Formula:**
  ```
  Quality Score = (Runtime Score × 0.4 + Engagement Score × 0.4 + Diversity Score × 0.2) × 10
  ```

- **Example**: 7.2 out of 10
- **Why it matters**: 
  - Provides a quick, objective assessment of content quality
  - Helps compare channels across different niches
  - Identifies areas for improvement (runtime, engagement, or diversity)
  
- **Detailed Interpretation**:
  - **9-10**: Exceptional quality - Top-tier content with great engagement and depth
  - **8-9**: Excellent quality - High-quality content that performs well
  - **7-8**: Very good quality - Solid content with room for minor improvements
  - **6-7**: Good quality - Decent content, consider improving one weak area
  - **5-6**: Average quality - Meets basic standards but needs improvement
  - **4-5**: Below average - Multiple areas need attention
  - **0-4**: Needs significant improvement - Focus on content depth and engagement

- **How to improve your Quality Score**:
  - **Boost Runtime Score**: Create longer, more in-depth content (aim for 15-20+ minutes for educational content)
  - **Boost Engagement Score**: 
    - Ask viewers to like and comment
    - Create discussion-worthy content
    - Respond to comments to encourage interaction
  - **Boost Diversity Score**: 
    - Cover a wider range of topics within your niche
    - Avoid repetitive video titles
    - Experiment with different content angles

- **Limitations to consider**:
  - Shorts-focused channels may score lower on runtime (but algorithm adjusts for this)
  - Niche channels may have lower diversity scores (which is acceptable for specialized content)
  - New channels with few videos may have skewed scores

#### 22. **Community Score (0-10)**
- **What it is**: Measures how actively a creator builds and engages with their community
- **How it's calculated**: Weighted average of 2 key components:
  
  **Component 1: Comments Score (60% weight)**
  - Based on average number of comments per video
  - Normalized assuming 10 comments per video = perfect score
    - 10+ comments/video = 1.0 score
    - 5 comments/video = 0.5 score
    - 1 comment/video = 0.1 score
  - **Rationale**: Comments indicate active audience participation and discussion
  
  **Component 2: Community Keyword Presence (40% weight)**
  - Proportion of videos that mention community-building keywords in descriptions:
    - **Platform keywords**: discord, telegram, facebook group
    - **Engagement keywords**: community, newsletter, live session, Q&A
    - **Call-to-action keywords**: join us, ask your doubt, paid community
  - Calculated as: (Videos with community keywords) / (Total videos)
  - **Rationale**: Explicit community-building efforts show creator investment
  
  **Formula:**
  ```
  Community Score = (Comments Score × 0.6 + Keyword Presence × 0.4) × 10
  ```

- **Example**: 6.5 out of 10
- **Why it matters**: 
  - Strong communities lead to higher retention and loyalty
  - Community members are more likely to share content
  - Engaged communities provide valuable feedback
  - Community building is essential for long-term channel growth
  
- **Detailed Interpretation**:
  - **9-10**: Exceptional community - Very active, engaged audience with strong creator interaction
  - **8-9**: Strong community - Regular interaction, likely has external community platforms
  - **7-8**: Good community - Solid engagement, creator actively responds to audience
  - **6-7**: Moderate community - Some interaction, room to build stronger connections
  - **5-6**: Basic community - Minimal interaction, mostly passive viewership
  - **4-5**: Weak community - Limited engagement, few comments or community efforts
  - **0-4**: No community - Little to no audience interaction or community building

- **How to improve your Community Score**:
  - **Boost Comments Score**:
    - Ask questions at the end of videos
    - Create polls and discussion topics
    - Respond to comments (this encourages more comments)
    - Pin engaging comments to spark discussion
    - Create "comment of the week" features
  - **Boost Keyword Presence**:
    - Create a Discord server or Telegram group
    - Mention community platforms in video descriptions
    - Host live Q&A sessions
    - Start a newsletter for your audience
    - Use consistent calls-to-action to join your community

- **Important Notes**:
  - **False Positives**: The keyword detection may flag videos about community platforms (e.g., "How to build a Discord bot") even if they're not building a community. This is a known limitation.
  - **Channel Size**: Smaller channels often have higher comment rates per video, while larger channels may have lower rates but higher absolute numbers.
  - **Content Type**: Tutorial channels naturally get more questions/comments than entertainment channels.

- **What this score tells you**:
  - High score (8+): Creator is actively building a loyal community
  - Medium score (5-7): Some community engagement, but could be strengthened
  - Low score (0-4): Focus on passive content consumption rather than community building


#### 23. **Monetization Inference**
- **What it is**: Detected monetization strategies
- **How it's calculated**: Searches video descriptions for keywords:
  - sponsor, sponsored, affiliate
  - udemy, coursera, patreon
  - merch, adsense, brand
- **Example**: "Detected: sponsor, patreon, affiliate"
- **Why it matters**: Indicates revenue streams
- **Note**: This is inference, not confirmed monetization

---

### 🔮 Predictive Metrics (Forecasts)

These metrics predict future performance based on historical trends.

#### 24. **Estimated Views Next 6 Months**
- **What it is**: Predicted total views over the next 26 weeks
- **How it's calculated**:
  1. Group videos by week of upload
  2. Calculate weekly view totals
  3. Fit a linear trend line
  4. Project 26 weeks forward
  5. Sum the projected weekly views
- **Example**: 15,000,000 views
- **Why it matters**: Helps predict channel growth
- **Limitations**:
  - Assumes consistent upload pattern
  - Uses simple linear model (may not capture viral growth)
  - Best for established channels with regular uploads
- **Note**: This is an estimate, not a guarantee

#### 25. **Estimated Subscribers Next 6 Months**
- **What it is**: Predicted new subscribers over 6 months
- **How it's calculated**:
  ```
  Estimated Views × 0.001 (0.1% conversion rate)
  ```
- **Example**: 15,000 new subscribers
- **Why it matters**: Helps predict audience growth
- **Limitations**:
  - Uses industry average conversion rate (0.1%)
  - Actual conversion varies by:
    - Content type (educational vs entertainment)
    - Video quality
    - Call-to-action effectiveness
    - Current subscriber base
- **Note**: This is a rough estimate based on industry averages

---

## 🔧 Technical Details

### How the Tool Works

#### 1. **Connecting to YouTube**
- Uses YouTube Data API v3
- Requires authentication via API key
- Respects YouTube's rate limits (10,000 units/day)

#### 2. **Fetching Channel Data**
For each channel:
1. Get channel information (ID, title, subscribers, total views)
2. Find the "uploads" playlist (contains all videos)
3. Fetch all video IDs from the playlist
4. Get detailed information for each video (views, likes, comments, duration, publish date)

#### 3. **Applying Filters**
- If a time period is selected, filter videos by publish date
- Keep only videos within the specified range
- Log how many videos were filtered

#### 4. **Calculating Metrics**
- Process video data using pandas (data analysis library)
- Perform calculations for each metric
- Handle edge cases (e.g., channels with 1 video, no shorts, etc.)

#### 5. **Exporting Results**
- Organize metrics into a table (one row per channel)
- Convert complex data (lists, dictionaries) to JSON strings
- Save as CSV with UTF-8 encoding (supports emojis and special characters)

### Duration Parsing

YouTube stores video durations in ISO 8601 format (e.g., `PT1H30M45S`).

**Supported formats:**
- `PT45S` = 45 seconds
- `PT10M30S` = 10 minutes 30 seconds
- `PT1H15M` = 1 hour 15 minutes
- `P1D` = 1 day
- `P1W` = 1 week
- `P1M` = 1 month (approximated as 30 days)
- `P1Y` = 1 year (approximated as 365 days)
- `P1Y2M3DT4H5M6S` = Complex combinations

### Date Handling

**Timezone Conversion:**
- YouTube provides dates in UTC (Universal Time)
- Tool converts to local time for filtering
- Videos published near midnight may shift dates slightly

**Date Filtering:**
- "From" date: Includes videos from 00:00:00 on that day
- "To" date: Includes videos until 23:59:59 on that day
- Filtering is inclusive (includes boundary dates)

### Error Handling

The tool handles various errors gracefully:
- **Invalid API key**: Shows error message, prompts for valid key
- **Channel not found**: Logs error, continues with next channel
- **No videos**: Logs message, skips analysis
- **API quota exceeded**: Shows error message
- **Network errors**: Displays error, allows retry

---

## 🐛 Troubleshooting

### Common Issues

#### "API key not found"
**Solution**: 
1. Check `config/api_key.json` exists
2. Ensure the key is not `YOUR_YOUTUBE_API_KEY_HERE`
3. Verify the key is valid (no extra spaces)

#### "API quota exceeded"
**Solution**:
- You've hit the daily limit (10,000 units)
- Wait 24 hours for quota to reset
- Or create a new Google Cloud project with a new API key

#### "Channel not found"
**Solution**:
- Verify the channel URL/ID is correct
- Some channels may be private or deleted
- Try using the channel ID instead of username

#### "No videos found"
**Solution**:
- Channel may have no public videos
- Date filter may be too restrictive
- Try "All time" period

#### Application won't start
**Solution**:
1. Verify Python is installed: `python --version`
2. Verify libraries are installed: `pip list`
3. Reinstall requirements: `pip install -r requirements.txt`

#### CSV export fails
**Solution**:
- Close the CSV file if it's open in Excel
- Choose a different save location
- Check you have write permissions

---

## 📚 Additional Information

### Data Privacy
- This tool only accesses **public** YouTube data
- No private information is collected
- API key is stored locally on your computer
- No data is sent to third parties

### Limitations
- **API Quota**: 10,000 units/day (free tier)
- **Rate Limits**: YouTube may throttle requests if too fast
- **Public Data Only**: Cannot access private videos or hidden subscriber counts
- **Forecasts**: Estimates only, not guarantees

### Best Practices
1. **Start Small**: Test with 1-2 channels first
2. **Use Date Filters**: Analyze recent content for faster results
3. **Save Regularly**: Export CSV after each analysis session
4. **Monitor Quota**: Keep track of daily API usage
5. **Verify Results**: Cross-check metrics with YouTube Studio when possible

### File Structure
```
YouTube-Metric-Extractor/
├── main.py                          # Main application (GUI)
├── requirements.txt                 # Required Python libraries
├── README.md                        # This file
├── config/
│   └── api_key.json                # Your API key (created automatically)
└── youtube_edu_analyzer/
    ├── analysis.py                 # Metric calculation logic
    ├── youtube_client.py           # YouTube API communication
    ├── insights.py                 # Aggregated insights
    └── config.py                   # Configuration loader
```

### Getting Help
If you encounter issues:
1. Check this README's Troubleshooting section
2. Verify your setup (Python version, API key, internet connection)
3. Check the Analysis Log for specific error messages
4. Search for the error message online

---

## 📝 Summary

This tool helps you analyze YouTube channels by:
1. Connecting to YouTube's API with your key
2. Fetching all public video data
3. Calculating 22 different metrics
4. Exporting results to a spreadsheet

**Key Takeaways:**
- ✅ Free to use (with YouTube API quota limits)
- ✅ Analyzes public data only
- ✅ Provides comprehensive insights
- ✅ Exports to Excel-compatible format
- ✅ Handles edge cases and errors gracefully

**Remember**: Metrics are tools for understanding, not absolute truths. Use them to inform decisions, but always consider context and qualitative factors too.

---

**Last Updated**: 2025-11-21  
**Version**: 2.1  
**Built with accuracy in mind** 🎯
