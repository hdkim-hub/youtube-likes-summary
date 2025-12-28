"""
Claude API를 사용한 영상 요약 모듈
"""
import os
import json
from anthropic import Anthropic

class VideoSummarizer:
    def __init__(self, config):
        self.config = config
        self.client = Anthropic(api_key=config['anthropic']['api_key'])
        self.model = config['anthropic']['model']
        self.summaries_dir = 'data/summaries'
        os.makedirs(self.summaries_dir, exist_ok=True)
    
    def summarize_general(self, transcript):
        """일반 영상 요약"""
        if transcript.get('status') != 'success':
            return {
                'video_id': transcript['video_id'],
                'status': 'skipped',
                'reason': '자막 없음'
            }
        
        prompt = f"""다음은 YouTube 영상의 자막입니다.

제목: {transcript['video_title']}
채널: {transcript['channel']}

자막:
{transcript['text'][:4000]}  # 토큰 제한을 위해 앞부분만 사용

위 영상의 핵심 내용을 3-5줄로 요약해주세요. 주요 포인트와 핵심 메시지를 중심으로 간결하게 작성해주세요."""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            summary = message.content[0].text
            
            return {
                'video_id': transcript['video_id'],
                'video_title': transcript['video_title'],
                'video_url': transcript['video_url'],
                'channel': transcript['channel'],
                'type': 'general',
                'summary': summary,
                'status': 'success'
            }
            
        except Exception as e:
            print(f"❌ 요약 실패: {transcript['video_id']} - {str(e)}")
            return {
                'video_id': transcript['video_id'],
                'status': 'error',
                'error': str(e)
            }
    
    def summarize_english_learning(self, transcript):
        """영어 학습 영상 요약 (상세)"""
        if transcript.get('status') != 'success':
            return {
                'video_id': transcript['video_id'],
                'status': 'skipped',
                'reason': '자막 없음'
            }
        
        prompt = f"""다음은 영어 학습 YouTube 영상의 자막입니다.

제목: {transcript['video_title']}
채널: {transcript['channel']}

자막:
{transcript['text'][:4000]}

위 영상을 분석하여 다음 형식으로 정리해주세요:

1. **핵심 주제** (1-2줄)
2. **주요 영어 표현** (5개, 각각 예문 포함)
3. **문법 포인트** (있다면)
4. **학습 팁** (실용적인 조언)

학습자가 나중에 복습할 때 유용하도록 구체적으로 작성해주세요."""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            summary = message.content[0].text
            
            return {
                'video_id': transcript['video_id'],
                'video_title': transcript['video_title'],
                'video_url': transcript['video_url'],
                'channel': transcript['channel'],
                'type': 'english_learning',
                'summary': summary,
                'status': 'success'
            }
            
        except Exception as e:
            print(f"❌ 영어 학습 요약 실패: {transcript['video_id']} - {str(e)}")
            return {
                'video_id': transcript['video_id'],
                'status': 'error',
                'error': str(e)
            }
    
    def summarize_batch(self, transcripts, is_english_learning_func):
        """
        여러 영상 일괄 요약
        
        Args:
            transcripts: 자막 리스트
            is_english_learning_func: 영어 학습 콘텐츠 판단 함수
        
        Returns:
            list: 요약 결과 리스트
        """
        summaries = []
        
        for i, transcript in enumerate(transcripts, 1):
            print(f"\n[{i}/{len(transcripts)}] 요약 생성 중: {transcript.get('video_title', 'Unknown')[:50]}...")
            
            # 영어 학습 콘텐츠 판단
            if is_english_learning_func(transcript):
                print("  → 영어 학습 콘텐츠로 분류")
                summary = self.summarize_english_learning(transcript)
            else:
                print("  → 일반 콘텐츠로 분류")
                summary = self.summarize_general(transcript)
            
            summaries.append(summary)
            
            if summary['status'] == 'success':
                print(f"  ✅ 요약 완료")
        
        print(f"\n✅ 총 {len([s for s in summaries if s['status'] == 'success'])}개 요약 생성 완료")
        return summaries
    
    def save_summaries(self, summaries):
        """요약 결과 저장"""
        for summary in summaries:
            if summary['status'] == 'success':
                video_id = summary['video_id']
                filepath = os.path.join(self.summaries_dir, f"{video_id}_summary.json")
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 요약 파일 저장 완료: {self.summaries_dir}")
    
    def load_summary(self, video_id):
        """저장된 요약 로드"""
        filepath = os.path.join(self.summaries_dir, f"{video_id}_summary.json")
        
        if not os.path.exists(filepath):
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)


if __name__ == "__main__":
    import yaml
    from transcript_extractor import TranscriptExtractor
    
    # 설정 로드
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 자막 로드
    with open('data/likes_raw.json', 'r', encoding='utf-8') as f:
        videos = json.load(f)
    
    extractor = TranscriptExtractor()
    transcripts = extractor.extract_multiple(videos[:3])  # 테스트용 3개
    
    # 요약 생성
    summarizer = VideoSummarizer(config)
    summaries = summarizer.summarize_batch(transcripts, extractor.is_english_content)
    summarizer.save_summaries(summaries)