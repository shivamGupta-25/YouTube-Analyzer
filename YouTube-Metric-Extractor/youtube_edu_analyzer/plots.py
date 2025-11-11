from collections import Counter

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def create_plots_and_save(analyses: list[dict]) -> None:
	df = pd.DataFrame(analyses)
	if df.empty:
		return
	# Scatter with NaN/Inf guarding
	xy = df[['avg_uploads_per_week','avg_views_sample']].replace([np.inf,-np.inf], np.nan).dropna()
	if not xy.empty:
		plt.figure()
		plt.scatter(xy['avg_uploads_per_week'], xy['avg_views_sample'])
		plt.xlabel('Uploads per week')
		plt.ylabel('Average views (sample)')
		plt.title('Avg Views vs Upload Frequency')
		plt.tight_layout()
		plt.savefig('avg_views_vs_uploads.png')
		plt.close()

	shorts_ratio = (df['avg_uploads_shorts_per_week'] / df['avg_uploads_per_week'].replace(0, np.nan)).clip(lower=0, upper=1).fillna(0)
	if len(shorts_ratio) > 0:
		plt.figure()
		plt.hist(shorts_ratio, bins=10)
		plt.xlabel('Shorts ratio (0-1)')
		plt.title('Distribution of Shorts Ratio across Channels')
		plt.tight_layout()
		plt.savefig('shorts_ratio_dist.png')
		plt.close()

	all_topics = Counter()
	for sub in df['top_topics'].dropna():
		for t in sub:
			all_topics[t]+=1
	top = all_topics.most_common(15)
	if top:
		labels, counts = zip(*top)
		plt.figure(figsize=(10,5))
		plt.bar(labels, counts)
		plt.xticks(rotation=45, ha='right')
		plt.title('Top topics across channels (titles)')
		plt.tight_layout()
		plt.savefig('top_topics_bar.png')
		plt.close()


