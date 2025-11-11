from collections import Counter

import numpy as np
import pandas as pd


def aggregate_insights(analyses: list[dict]) -> dict:
	df = pd.DataFrame(analyses)
	insights: dict = {}
	if df.empty:
		return insights

	insights['channels_analyzed'] = int(len(df))
	# Shorts ratio median with safe denom and clipping to [0,1]
	denom = df['avg_uploads_per_week'].replace(0, np.nan)
	shorts_ratio_series = (df['avg_uploads_shorts_per_week'] / denom).clip(lower=0, upper=1)
	insights['median_shorts_ratio'] = float(round(shorts_ratio_series.median(skipna=True), 2))
	insights['top_overall_topics'] = Counter([t for sub in df['top_topics'].dropna() for t in sub]).most_common(20)

	suggestions: list[str] = []
	df['shorts_ratio'] = (df['avg_uploads_shorts_per_week'] / df['avg_uploads_per_week'].replace(0, np.nan)).clip(lower=0, upper=1)
	high_shorts = df[df['shorts_ratio']>0.5]
	low_shorts = df[df['shorts_ratio']<=0.5]
	if not high_shorts.empty and not low_shorts.empty:
		if high_shorts['avg_views_sample'].mean() > low_shorts['avg_views_sample'].mean() * 1.3:
			suggestions.append('Shorts-heavy channels tend to get higher avg views — consider a shorts-first strategy for reach.')
		else:
			suggestions.append('Maintain a healthy mix of shorts and long-form; long-form drives depth and conversions.')

	# Correlation only if sufficient non-NaN data
	valid_corr = df[['avg_uploads_per_week','avg_views_sample']].replace([np.inf, -np.inf], np.nan).dropna()
	if len(valid_corr) >= 3:
		corr = valid_corr['avg_uploads_per_week'].corr(valid_corr['avg_views_sample'])
		if pd.notna(corr) and corr > 0.2:
			suggestions.append('Increasing upload frequency correlates with higher avg views; aim for consistent cadence (e.g., 2-4/week).')
		else:
			suggestions.append('Upload frequency has unclear correlation; prioritize content quality and targeted topics.')
	else:
		suggestions.append('Insufficient data to assess upload frequency vs. views correlation; emphasize content quality.')

	insights['suggestions'] = suggestions
	return insights


