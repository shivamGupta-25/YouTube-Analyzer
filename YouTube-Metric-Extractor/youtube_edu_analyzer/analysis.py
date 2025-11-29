"""
YouTube Channel Analysis Module

This module provides functionality for analyzing YouTube channels and their videos.
It extracts metrics, calculates statistics, and generates insights from video data.

Key functions:
- extract_channel_identifier: Parse channel URLs/IDs
- analyze_channel: Compute comprehensive metrics for a channel
- parse_duration_to_seconds: Convert ISO8601 duration to seconds

Constants:
- CTA_WORDS: Call-to-action keywords for marketing analysis
- COMMUNITY_WORDS: Community-building keywords
- MONET_WORDS: Monetization-related keywords
- SHORTS_THRESHOLD_SECONDS: Duration threshold for YouTube Shorts (60s)
"""
import math
import re
from collections import Counter

def _safe_int(value, default: int = 0) -> int:
	try:
		if value is None:
			return default
		return int(value)
	except Exception:
		return default

def _safe_float(value, default: float = 0.0) -> float:
	"""Convert value to float, handling NaN and None."""
	try:
		if value is None:
			return default
		if isinstance(value, float) and math.isnan(value):
			return default
		return float(value)
	except Exception:
		return default
import numpy as np
import pandas as pd
from dateutil import parser as dateparse


URL_PATTERNS = [
	r"(?:https?://)?(?:www\.)?youtube\.com/channel/([A-Za-z0-9_-]+)",
	r"(?:https?://)?(?:www\.)?youtube\.com/c/([A-Za-z0-9_-]+)",
	r"(?:https?://)?(?:www\.)?youtube\.com/user/([A-Za-z0-9_-]+)",
	r"(?:https?://)?(?:www\.)?youtube\.com/(@[A-Za-z0-9_-]+)",
	r"^([A-Za-z0-9_-]{24,})$",
]

CTA_WORDS = [
	'subscribe', 'join', 'enroll', 'download', 'signup', 'sign up', 'visit', 'buy', 'purchase',
	'link in description', 'link in bio', 'course', 'free course', 'patreon', 'donate', 'sponsor', 'sponsored', 'affiliate', 'discount'
]

COMMUNITY_WORDS = ['discord','telegram','community','facebook group','paid community','newsletter','live session','q&a','ask your doubt','join us']
MONET_WORDS = ['sponsor','sponsored','affiliate','udemy','coursera','patreon','merch','adsense','brand']

SHORTS_THRESHOLD_SECONDS = 60  # YouTube's official threshold for Shorts
FUTURE_WEEKS = 26  # 6 months forecast period

# Improved ISO8601 duration regex to handle all valid formats
# Supports: years (Y), months (M), weeks (W), days (D), hours (H), minutes (M), seconds (S)
# Examples: PT1H30M, P1DT2H, P1W, P1Y2M3DT4H5M6S
ISO8601_DURATION_RE = re.compile(
	r'P(?:(\d+)Y)?(?:(\d+)M)?(?:(\d+)W)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?)?'
)


def parse_duration_to_seconds(dur: str) -> int:
	"""Parse ISO8601 duration string to total seconds.
	
	Supports all ISO8601 duration components:
	- Years (P1Y) - approximated as 365 days
	- Months (P1M) - approximated as 30 days
	- Weeks (P1W) - 7 days
	- Days (P1D)
	- Hours (T1H)
	- Minutes (T1M)
	- Seconds (T1S)
	
	Note: Month and year conversions are approximations since actual lengths vary.
	"""
	if not dur:
		return 0
	m = ISO8601_DURATION_RE.match(dur)
	if not m:
		return 0
	
	years = int(m.group(1)) if m.group(1) else 0
	months = int(m.group(2)) if m.group(2) else 0
	weeks = int(m.group(3)) if m.group(3) else 0
	days = int(m.group(4)) if m.group(4) else 0
	hours = int(m.group(5)) if m.group(5) else 0
	minutes = int(m.group(6)) if m.group(6) else 0
	seconds = float(m.group(7)) if m.group(7) else 0.0
	
	# Convert all components to seconds
	# Note: Using 365 days/year and 30 days/month as approximations
	total_seconds = (
		years * 365 * 86400 +
		months * 30 * 86400 +
		weeks * 7 * 86400 +
		days * 86400 +
		hours * 3600 +
		minutes * 60 +
		seconds
	)
	return int(total_seconds)


def extract_channel_identifier(url_or_id: str) -> str:
	url_or_id = url_or_id.strip()
	for pat in URL_PATTERNS:
		m = re.search(pat, url_or_id)
		if m:
			return m.group(1)
	if url_or_id.startswith('@'):
		return url_or_id
	return url_or_id


def analyze_channel(channel_item, video_items):
	snippet = channel_item.get('snippet', {})
	stats = channel_item.get('statistics', {})
	title = snippet.get('title')
	cid = channel_item.get('id')

	subs_raw = stats.get('subscriberCount')
	subs = _safe_int(subs_raw, 0) if subs_raw not in (None, '') else None
	channel_total_views = _safe_int(stats.get('viewCount'), 0)

	videos = []
	for v in video_items:
		snip = v.get('snippet', {})
		cd = v.get('contentDetails', {})
		st = v.get('statistics', {})
		pub = dateparse.parse(snip.get('publishedAt')) if snip.get('publishedAt') else None
		duration = parse_duration_to_seconds(cd.get('duration','PT0S'))
		views = _safe_int(st.get('viewCount'), 0)
		likes = _safe_int(st.get('likeCount'), 0)
		comments = _safe_int(st.get('commentCount'), 0)
		videos.append({
			'id': v.get('id'),
			'title': snip.get('title',''),
			'description': snip.get('description','') or '',
			'publishedAt': pub,
			'duration_seconds': duration,
			'views': views,
			'likes': likes,
			'comments': comments,
		})

	if not videos:
		return None

	dfv = pd.DataFrame(videos)
	# Ensure datetime dtype for publishedAt and drop invalid dates for time-based calcs
	dfv['publishedAt'] = pd.to_datetime(dfv['publishedAt'], errors='coerce', utc=True)
	# Convert to naive datetimes (remove timezone info) for consistency in downstream ops
	# Since utc=True ensures timezone-aware datetimes, safely convert to naive
	try:
		if dfv['publishedAt'].dt.tz is not None:
			dfv['publishedAt'] = dfv['publishedAt'].dt.tz_convert(None)
	except (AttributeError, TypeError):
		# If already naive or empty, no conversion needed
		pass
	dfv = dfv.sort_values(by='publishedAt')
	total_videos = len(dfv)

	# Use only valid dates for span-based metrics; provide safe fallback if none
	dfv_dates = dfv.dropna(subset=['publishedAt'])
	if not dfv_dates.empty:
		first_date = dfv_dates['publishedAt'].iloc[0]
		last_date = dfv_dates['publishedAt'].iloc[-1]
		days_span = (last_date - first_date).days
		
		# Edge case handling for upload frequency calculations:
		# - Same-day uploads: use 1 day span
		# - Very new channels (< 7 days): use actual span to avoid inflated rates
		# - Single video: treat as 1 week minimum to show realistic weekly rate
		if days_span == 0:
			days_span = 1
		
		# For single-video channels, use minimum 1 week to avoid showing
		# unrealistic rates like "7 uploads/week" for a channel with 1 video
		if len(dfv_dates) == 1:
			weeks_span = 1.0  # Treat as 1 week minimum
		else:
			weeks_span = max(days_span / 7.0, 1.0 / 7.0)  # Minimum 1 day = 1/7 week
		
		# Count videos with valid dates for accurate per-week calculations
		dated_videos_count = len(dfv_dates)
		shorts_mask_dated = dfv_dates['duration_seconds'] <= SHORTS_THRESHOLD_SECONDS
		shorts_count_dated = shorts_mask_dated.sum()
		longs_count_dated = dated_videos_count - shorts_count_dated
	else:
		weeks_span = 1.0
		dated_videos_count = total_videos
		shorts_count_dated = 0
		longs_count_dated = 0

	# Calculate upload rates using only dated videos to ensure consistency
	uploads_per_week = dated_videos_count / weeks_span if weeks_span > 0 else 0.0
	
	# For overall counts, use all videos (including those without dates)
	shorts_mask = dfv['duration_seconds'] <= SHORTS_THRESHOLD_SECONDS
	shorts_count = shorts_mask.sum()
	longs_count = total_videos - shorts_count
	
	# Per-week rates should use dated videos only for accuracy
	shorts_per_week = shorts_count_dated / weeks_span if weeks_span > 0 else 0.0
	longs_per_week = longs_count_dated / weeks_span if weeks_span > 0 else 0.0

	avg_runtime_long = _safe_float(dfv.loc[~shorts_mask, 'duration_seconds'].mean() if longs_count>0 else 0.0)
	avg_runtime_shorts = _safe_float(dfv.loc[shorts_mask, 'duration_seconds'].mean() if shorts_count>0 else 0.0)
	avg_views = _safe_float(dfv['views'].mean())

	n_top = max(1, math.ceil(0.10 * total_videos))
	top_videos = dfv.nlargest(n_top, 'views')
	# Avoid divide-by-zero by excluding rows with zero views for per-video ratios
	_top_nonzero = top_videos[top_videos['views'] > 0]
	top_engagement_pct = (((_top_nonzero['likes'] + _top_nonzero['comments']) / _top_nonzero['views']).mean() * 100) if not _top_nonzero.empty else 0

	longs = dfv.loc[~shorts_mask]
	shorts = dfv.loc[shorts_mask]
	top5_longs = longs.nlargest(5, 'views')['title'].tolist() if not longs.empty else []
	top5_shorts = shorts.nlargest(5, 'views')['title'].tolist() if not shorts.empty else []

	cta_counter = Counter()
	monet_counter = Counter()
	community_counter = Counter()
	videos_with_community_keywords = 0
	for desc in dfv['description'].astype(str):
		d = desc.lower()
		has_community = False
		for kw in CTA_WORDS:
			if kw in d:
				cta_counter[kw]+=1
		for kw in MONET_WORDS:
			if kw in d:
				monet_counter[kw]+=1
		for kw in COMMUNITY_WORDS:
			if kw in d:
				community_counter[kw]+=1
				has_community = True
		if has_community:
			videos_with_community_keywords += 1

	# Extract topics from video titles
	tokens = []
	for t in dfv['title'].astype(str):
		toks = re.findall(r"[A-Za-z0-9+#]+", t.lower())
		tokens.extend(toks)
	
	# Comprehensive stopword list to filter out common filler words
	stopwords = set([
		# Articles, prepositions, conjunctions
		'the', 'and', 'for', 'with', 'to', 'a', 'an', 'in', 'of', 'is', 'at', 'by', 'on',
		# Common verbs
		'how', 'what', 'learn', 'get', 'make', 'use', 'do', 'can', 'will', 'should',
		# Tutorial/video-related words
		'tutorial', 'lesson', 'video', 'introduction', 'session', 'guide', 'course',
		'part', 'episode', 'series', 'chapter', 'lecture',
		# Common adjectives/qualifiers
		'new', 'best', 'top', 'this', 'that', 'your', 'from', 'all', 'about', 'into',
		'complete', 'full', 'easy', 'simple', 'quick', 'free', 'basic', 'advanced',
		# Time-related
		'2023', '2024', '2025', 'today', 'now',
		# Numbers (filter 1-20 as they're usually not meaningful topics)
		'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten'
	])
	filtered = [w for w in tokens if w not in stopwords and len(w) > 2]
	top_topics = [w for w, c in Counter(filtered).most_common(20)]

	# Build weekly aggregation only from rows with valid dates
	if not dfv_dates.empty:
		dfv_dates = dfv_dates.copy()
		dfv_dates['week'] = dfv_dates['publishedAt'].dt.to_period('W').apply(lambda r: r.start_time)
		weekly_views = dfv_dates.groupby('week')['views'].sum().reset_index()
		weekly_views['week_index'] = range(len(weekly_views))
	else:
		weekly_views = pd.DataFrame(columns=['week','views','week_index'])

	# Forecast total views over the next FUTURE_WEEKS using a simple linear trend,
	# clipping negative weekly predictions and providing sensible fallbacks.
	est_views_6m = None
	if len(weekly_views) >= 2:
		x = weekly_views['week_index'].values
		y = weekly_views['views'].values
		# Filter out any invalid values
		valid_mask = np.isfinite(y) & (y >= 0)
		if valid_mask.sum() >= 2:
			x_valid = x[valid_mask]
			y_valid = y[valid_mask]
			try:
				slope, intercept = np.polyfit(x_valid, y_valid, 1)
				# Use the last valid week index to project forward
				last_week_index = x_valid[-1]
				future_x = np.arange(last_week_index + 1, last_week_index + 1 + FUTURE_WEEKS)
				future_y = intercept + slope * future_x
				future_y = np.maximum(0, future_y)
				est_views_6m = float(future_y.sum())
				# If forecast is zero or negative, use recent average instead
				if est_views_6m <= 0:
					recent_weeks = min(8, len(y_valid))
					avg_recent_weekly = float(np.mean(y_valid[-recent_weeks:])) if len(y_valid) > 0 else 0.0
					est_views_6m = max(0.0, avg_recent_weekly * FUTURE_WEEKS)
			except (np.linalg.LinAlgError, ValueError, TypeError):
				# Fallback to mean if regression fails
				avg_weekly_views = float(np.mean(y_valid)) if len(y_valid) > 0 else 0.0
				est_views_6m = max(0.0, avg_weekly_views * FUTURE_WEEKS)
		else:
			# Not enough valid data points, use mean
			avg_weekly_views = float(np.mean(y[valid_mask])) if valid_mask.sum() > 0 else 0.0
			est_views_6m = max(0.0, avg_weekly_views * FUTURE_WEEKS)
	elif len(weekly_views) == 1:
		# Single week: use that week's views, but be conservative (don't assume it's typical)
		single_week_views = float(weekly_views['views'].iloc[0])
		if single_week_views > 0 and np.isfinite(single_week_views):
			est_views_6m = max(0.0, single_week_views * FUTURE_WEEKS)
		else:
			est_views_6m = 0.0
	else:
		est_views_6m = 0.0

	# Estimate subscriber growth based on view forecast
	# Note: Using industry average conversion rate of 0.1% (views to subscribers)
	# This is a rough estimate and actual conversion varies widely by channel type,
	# content quality, and audience engagement.
	est_subs_6m = None
	try:
		conversion_rate = 0.001  # 0.1% conversion rate (industry average)
		est_subs_6m = int(est_views_6m * conversion_rate) if est_views_6m else 0
	except Exception:
		est_subs_6m = 0

	# Calculate overall engagement rate with proper handling of edge cases
	total_views = dfv['views'].sum()
	if total_views > 0:
		engagement_rate_overall = _safe_float((dfv['likes'].sum() + dfv['comments'].sum()) / total_views, 0.0)
	else:
		engagement_rate_overall = 0.0
	
	topic_diversity = len(set(filtered)) / max(1, len(filtered))
	
	# Quality Score Calculation (0-10 scale)
	# Formula: (runtime*0.4 + engagement*0.4 + topic_diversity*0.2) * 10
	# 
	# Components:
	# 1. Runtime Score (40% weight):
	#    - Long videos: normalized to 20 minutes (1200s) as baseline for educational content
	#    - Shorts: normalized to 30 seconds as baseline (different content type)
	# 2. Engagement Score (40% weight):
	#    - Normalized assuming 10% engagement rate = perfect score
	#    - Engagement = (likes + comments) / views
	# 3. Topic Diversity Score (20% weight):
	#    - Normalized assuming 50% unique topics = perfect score
	#    - Measures variety in content topics
	#
	# Handle channels with only shorts or only long videos
	if longs_count > 0:
		# Normalize to 20 minutes (typical educational video length)
		score_runtime = min(1.0, max(0.0, (avg_runtime_long / (20*60))))
	else:
		# For shorts-only channels, normalize to 30 seconds
		# This prevents unfairly penalizing shorts-only channels
		score_runtime = min(1.0, max(0.0, (avg_runtime_shorts / 30.0))) if shorts_count > 0 else 0.0
	
	# Engagement: 10% rate = 1.0 score
	score_eng = min(1.0, max(0.0, engagement_rate_overall * 10))
	# Topic diversity: 50% unique = 1.0 score
	score_topic = min(1.0, max(0.0, topic_diversity * 2))
	# Weighted average scaled to 0-10
	quality_score = round((score_runtime*0.4 + score_eng*0.4 + score_topic*0.2) * 10, 2)

	# Community Score Calculation (0-10 scale)
	# Formula: (comments_score*0.6 + keyword_presence*0.4) * 10
	#
	# Components:
	# 1. Comments Score (60% weight):
	#    - Normalized to 10 comments per video = perfect score
	#    - Measures direct audience interaction
	# 2. Keyword Presence (40% weight):
	#    - Proportion of videos mentioning community-building keywords
	#    - Keywords: discord, telegram, community, facebook group, newsletter, etc.
	#    - Note: May have false positives (e.g., "discord bot tutorial")
	avg_comments = _safe_float(dfv['comments'].mean())
	# Community presence: proportion of videos with community-related keywords
	community_presence = min(1.0, max(0.0, videos_with_community_keywords / max(1, total_videos)))
	# Comments: 10 per video = 1.0 score
	comments_score = min(1.0, max(0.0, avg_comments / 10.0))
	# Weighted average scaled to 0-10
	score_community = round((comments_score * 0.6 + community_presence * 0.4) * 10, 2)

	monetization_type = 'None Detected'
	if monet_counter:
		monetization_type = 'Detected: ' + ', '.join([k for k,c in monet_counter.most_common(5)])
	elif any('sponsor' in k for k in cta_counter):
		monetization_type = 'Sponsorship Mentions'

	result = {
		'channel_id': cid,
		'channel_title': title,
		'subscribers': subs,
		'channel_total_views': channel_total_views,
		'sample_videos_analyzed': total_videos,
		'avg_uploads_per_week': round(uploads_per_week,2),
		'avg_uploads_long_per_week': round(longs_per_week,2),
		'avg_uploads_shorts_per_week': round(shorts_per_week,2),
		'avg_runtime_long_minutes': round(avg_runtime_long / 60, 2),
		'avg_runtime_shorts_minutes': round(avg_runtime_shorts / 60, 2),
		'engagement_pct_popular_videos': round(float(top_engagement_pct),2),
		'top_5_long_titles': top5_longs,
		'top_5_shorts_titles': top5_shorts,
		'cta_counts': dict(cta_counter.most_common(10)),
		'top_topics': top_topics,
		'est_views_next_6_months': int(est_views_6m) if est_views_6m is not None else None,
		'est_subs_next_6_months': int(est_subs_6m) if est_subs_6m is not None else None,
		'quality_score_0_10': quality_score,
		'monetization_inference': monetization_type,
		'avg_views_sample': round(float(avg_views),2),
		'engagement_rate_overall_pct': round(float(engagement_rate_overall*100),2)
	}

	return result


