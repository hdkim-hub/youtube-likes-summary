"""
영상 카테고리 자동 분류 모듈
"""
import yaml

class VideoCategorizer:
    def __init__(self, config):
        self.categories = config.get('categories', {})
        
    def categorize_video(self, video, transcript=None):
        """
        영상을 카테고리별로 분류
        
        Args:
            video: 영상 메타데이터
            transcript: 자막 데이터 (선택)
        
        Returns:
            str: 카테고리명
        """
        # 검색할 텍스트 준비
        search_text = f"{video['title']} {video['description']}".lower()
        
        # 자막이 있으면 추가
        if transcript and transcript.get('status') == 'success':
            search_text += f" {transcript['text'][:500].lower()}"
        
        # 카테고리별 키워드 매칭
        category_scores = {}
        
        for category, keywords in self.categories.items():
            score = sum(1 for keyword in keywords if keyword.lower() in search_text)
            if score > 0:
                category_scores[category] = score
        
        # 가장 높은 점수의 카테고리 반환
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            return best_category
        
        # 매칭되는 카테고리가 없으면 '기타'
        return '기타'
    
    def categorize_batch(self, videos, transcripts=None):
        """
        여러 영상 일괄 분류
        
        Args:
            videos: 영상 리스트
            transcripts: 자막 리스트 (선택)
        
        Returns:
            dict: 카테고리별 영상 그룹
        """
        categorized = {}
        
        # 자막을 video_id로 매핑
        transcript_map = {}
        if transcripts:
            transcript_map = {t['video_id']: t for t in transcripts}
        
        for video in videos:
            video_id = video['video_id']
            transcript = transcript_map.get(video_id)
            
            category = self.categorize_video(video, transcript)
            
            if category not in categorized:
                categorized[category] = []
            
            video_with_category = video.copy()
            video_with_category['category'] = category
            categorized[category].append(video_with_category)
        
        # 카테고리별 통계
        print("\n📊 카테고리별 분류 결과:")
        for category, items in sorted(categorized.items()):
            print(f"  - {category}: {len(items)}개")
        
        return categorized
    
    def get_category_summary(self, categorized_videos):
        """카테고리별 요약 통계"""
        summary = {}
        
        for category, videos in categorized_videos.items():
            summary[category] = {
                'count': len(videos),
                'videos': [
                    {
                        'title': v['title'],
                        'url': v['url'],
                        'channel': v['channel']
                    }
                    for v in videos
                ]
            }
        
        return summary
    
    def filter_by_category(self, categorized_videos, category):
        """특정 카테고리의 영상만 필터링"""
        return categorized_videos.get(category, [])
    
    def get_priority_categories(self, categorized_videos):
        """
        우선순위가 높은 카테고리 반환
        (영어학습, 업무 등)
        """
        priority = ['영어학습', '업무', '교육']
        result = {}
        
        for cat in priority:
            if cat in categorized_videos:
                result[cat] = categorized_videos[cat]
        
        return result


if __name__ == "__main__":
    import json
    import yaml
    
    # 설정 및 데이터 로드
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    with open('data/likes_raw.json', 'r', encoding='utf-8') as f:
        videos = json.load(f)
    
    # 분류 실행
    categorizer = VideoCategorizer(config)
    categorized = categorizer.categorize_batch(videos)
    
    # 우선순위 카테고리 확인
    priority = categorizer.get_priority_categories(categorized)
    print("\n🎯 우선순위 카테고리:")
    for cat, items in priority.items():
        print(f"\n[{cat}]")
        for item in items[:3]:  # 각 카테고리 상위 3개만
            print(f"  - {item['title'][:50]}...")