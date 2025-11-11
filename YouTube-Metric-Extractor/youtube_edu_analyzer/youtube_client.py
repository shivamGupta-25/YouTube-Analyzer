from googleapiclient.discovery import build


class YouTubeClient:
	def __init__(self, api_key: str):
		if not api_key:
			raise ValueError('You must provide a YouTube API key')
		self.client = build('youtube', 'v3', developerKey=api_key)

	def get_channel(self, identifier: str):
		try:
			res = self.client.channels().list(part='snippet,statistics,contentDetails', id=identifier).execute()
			if res.get('items'):
				return res['items'][0]
		except Exception:
			pass
		try:
			res = self.client.search().list(part='snippet', q=identifier, type='channel', maxResults=1).execute()
			if res.get('items'):
				cid = res['items'][0]['snippet']['channelId']
				res2 = self.client.channels().list(part='snippet,statistics,contentDetails', id=cid).execute()
				if res2.get('items'):
					return res2['items'][0]
		except Exception:
			pass
		return None

	def get_videos_from_uploads(self, uploads_playlist_id: str, max_videos: int | None):
		vids = []
		nextPage = None
		fetched = 0
		while True:
			resp = self.client.playlistItems().list(part='contentDetails', playlistId=uploads_playlist_id, maxResults=50, pageToken=nextPage).execute()
			for it in resp.get('items', []):
				vids.append(it['contentDetails']['videoId'])
				fetched += 1
				if isinstance(max_videos, int) and max_videos > 0 and fetched >= max_videos:
					return vids
			nextPage = resp.get('nextPageToken')
			if not nextPage:
				break
		return vids

	def get_videos_details(self, video_ids: list[str]):
		out = []
		for i in range(0, len(video_ids), 50):
			batch = video_ids[i:i+50]
			resp = self.client.videos().list(part='snippet,contentDetails,statistics', id=','.join(batch), maxResults=50).execute()
			out.extend(resp.get('items', []))
		return out


