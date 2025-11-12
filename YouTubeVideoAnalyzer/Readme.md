```
YouTube Channel Analysis Tool (Tkinter)

Features:
- Enter API key and channel ID / URL
- Choose time window (last 1/2/5 months or custom date range)
- Fetch videos from channel in the chosen date range
- Retrieve metadata: title, description, views, likes, comments, publish date/time,
  duration, category, video ID, tags, thumbnail URL, video URL
- Compute metrics: avg views/day, like-to-view ratio, comment-to-view ratio
- Display results in a Treeview and allow export to CSV
- Open selected video in browser

Limitations:
- dislikeCount is no longer available via YouTube Data API and is not provided
  by this tool.
```