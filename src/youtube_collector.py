"""
YouTube 좋아요 영상 목록 수집 모듈
"""
import json
import os
from datetime import datetime
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

class YouTubeCollector:
    def __init__(self, config):
        self.config = config
        self.youtube = None
        self.credentials = None
        
    def authenticate(self):
        """OAuth 2.0 인증"""
        SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']
        creds = None
        
        # token.pickle 파일이 있으면 로드
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        # 유효한 credentials가 없으면 로그인
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'client_secret.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            # 다음 실행을 위해 저장
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        self.credentials = creds
        self.youtube = build('youtube', 'v3', credentials=creds)
        print("✅ YouTube API 인증 완료")
        
    def get_liked_videos(self, max_results=50):
        """좋아요 누른 영상 목록 가져오기"""
        if not self.youtube:
            self.authenticate()
        
        liked_videos = []
        request = self.youtube.videos().list(
            part='snippet,contentDetails,statistics',
            myRating='like',
            maxResults=max_results
        )
        
        while request and len(liked_videos) < max_results:
            response = request.execute()
            
            for item in response.get('items', []):
                video_data = {
                    'video_id': item['id'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'channel': item['snippet']['channelTitle'],
                    'published_at': item['snippet']['publishedAt'],
                    'duration': item['contentDetails']['duration'],
                    'view_count': item['statistics'].get('viewCount', 0),
                    'like_count': item['statistics'].get('likeCount', 0),
                    'url': f"https://www.youtube.com/watch?v={item['id']}",
                    'collected_at': datetime.now().isoformat()
                }
                liked_videos.append(video_data)
            
            request = self.youtube.videos().list_next(request, response)
        
        print(f"✅ 총 {len(liked_videos)}개의 좋아요 영상 수집 완료")
        return liked_videos
    
    def save_to_json(self, videos, filepath='data/likes_raw.json'):
        """수집한 데이터를 JSON으로 저장"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(videos, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 데이터 저장 완료: {filepath}")
        
    def load_from_json(self, filepath='data/likes_raw.json'):
        """저장된 JSON 데이터 로드"""
        if not os.path.exists(filepath):
            return []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
        
    def filter_new_videos(self, current_videos, previous_videos):
        """새로운 영상만 필터링"""
        previous_ids = {v['video_id'] for v in previous_videos}
        new_videos = [v for v in current_videos if v['video_id'] not in previous_ids]
        
        print(f"✅ 새로운 영상: {len(new_videos)}개")
        return new_videos


if __name__ == "__main__":
    import yaml
    
    # 설정 로드
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 수집 실행
    collector = YouTubeCollector(config)
    collector.authenticate()
    videos = collector.get_liked_videos(max_results=50)
    collector.save_to_json(videos)