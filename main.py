"""
YouTube 좋아요 영상 요약 프로젝트 - 메인 실행 파일 (Whisper 통합)
"""
import os
import yaml
import json
from datetime import datetime
from tqdm import tqdm

from src.youtube_collector import YouTubeCollector
from src.transcript_extractor import TranscriptExtractor
from src.summarizer import VideoSummarizer
from src.categorizer import VideoCategorizer
from src.reporter import ReportGenerator


class YouTubeLikesSummarizer:
    def __init__(self, config_path='config/config.yaml'):
        """초기화"""
        # 설정 로드
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # 모듈 초기화
        self.collector = YouTubeCollector(self.config)
        
        # Whisper 설정 확인
        whisper_config = self.config.get('whisper', {})
        use_whisper = whisper_config.get('enabled', False)
        whisper_model = whisper_config.get('model', 'base')
        
        # TranscriptExtractor 초기화 (Whisper 설정 포함)
        self.extractor = TranscriptExtractor(
            use_whisper=use_whisper,
            whisper_model=whisper_model
        )
        
        self.summarizer = VideoSummarizer(self.config)
        self.categorizer = VideoCategorizer(self.config)
        self.reporter = ReportGenerator()
        
        print("✅ YouTube 좋아요 요약 시스템 초기화 완료")
        if use_whisper:
            print(f"🎤 Whisper 음성 인식 활성화됨 (모델: {whisper_model})")
    
    def run_full_pipeline(self, max_videos=50, force_refresh=False):
        """
        전체 파이프라인 실행
        
        Args:
            max_videos: 수집할 최대 영상 수
            force_refresh: True면 기존 데이터 무시하고 새로 수집
        """
        print("\n" + "="*60)
        print("🎬 YouTube 좋아요 영상 요약 시스템 시작")
        print("="*60 + "\n")
        
        # 1단계: YouTube 좋아요 영상 수집
        print("\n[1/5] 📥 YouTube 좋아요 영상 수집 중...")
        videos = self._collect_videos(max_videos, force_refresh)
        
        if not videos:
            print("❌ 수집된 영상이 없습니다.")
            return
        
        # 2단계: 자막 추출 (Whisper 포함)
        print("\n[2/5] 📝 영상 자막 추출 중...")
        transcripts = self._extract_transcripts(videos)
        
        # 3단계: AI 요약 생성
        print("\n[3/5] 🤖 AI 요약 생성 중...")
        summaries = self._generate_summaries(transcripts)
        
        # 4단계: 카테고리 분류
        print("\n[4/5] 📂 카테고리 분류 중...")
        categorized = self._categorize_videos(videos, transcripts)
        
        # 5단계: 리포트 생성
        print("\n[5/5] 📊 리포트 생성 중...")
        self._generate_reports(summaries, categorized)
        
        print("\n" + "="*60)
        print("✅ 모든 작업 완료!")
        print("="*60)
        
        self._print_summary(summaries, categorized)
    
    def _collect_videos(self, max_videos, force_refresh):
        """영상 수집"""
        if not force_refresh:
            # 기존 데이터 확인
            existing = self.collector.load_from_json()
            if existing:
                print(f"  ℹ️  기존 데이터 발견: {len(existing)}개")
            if os.getenv('CI'):
                print("  ℹ️  CI 환경 감지: 기존 데이터 자동 사용")
                return existing
                use_existing = input("  기존 데이터를 사용하시겠습니까? (y/n): ").lower()
                if use_existing == 'y':
                    return existing
        
        # 새로 수집
        self.collector.authenticate()
        videos = self.collector.get_liked_videos(max_results=max_videos)
        self.collector.save_to_json(videos)
        
        return videos
    
    def _extract_transcripts(self, videos):
        """자막 추출 (Whisper 포함)"""
        transcripts = []
        
        whisper_config = self.config.get('whisper', {})
        fallback_only = whisper_config.get('fallback_only', True)
        
        print(f"  총 {len(videos)}개 영상의 자막을 추출합니다...")
        if self.extractor.use_whisper:
            if fallback_only:
                print("  ℹ️  Whisper: 자막 없는 영상만 음성 인식 사용")
            else:
                print("  ℹ️  Whisper: 모든 영상에 음성 인식 사용")
        
        with tqdm(total=len(videos), desc="  자막 추출") as pbar:
            for video in videos:
                # 이미 추출된 자막이 있는지 확인
                existing = self.extractor.load_transcript(video['video_id'])
                
                if existing:
                    transcripts.append(existing)
                else:
                    transcript = self.extractor.extract_transcript(
                        video['video_id'],
                        url=video['url']
                    )
                    transcript['video_title'] = video['title']
                    transcript['video_url'] = video['url']
                    transcript['channel'] = video['channel']
                    transcripts.append(transcript)
                
                pbar.update(1)
        
        # 저장
        self.extractor.save_transcripts(transcripts)
        
        success_count = len([t for t in transcripts if t['status'] == 'success'])
        whisper_count = len([t for t in transcripts if t.get('method') == 'whisper'])
        
        print(f"  ✅ {success_count}/{len(videos)}개 자막 추출 성공")
        if whisper_count > 0:
            print(f"  🎤 Whisper로 인식: {whisper_count}개")
        
        return transcripts
    
    def _generate_summaries(self, transcripts):
        """요약 생성"""
        # 자막이 있는 것만 요약
        valid_transcripts = [t for t in transcripts if t.get('status') == 'success']
        
        if not valid_transcripts:
            print("  ⚠️  요약할 자막이 없습니다.")
            return []
        
        print(f"  총 {len(valid_transcripts)}개 영상을 요약합니다...")
        
        summaries = []
        
        with tqdm(total=len(valid_transcripts), desc="  요약 생성") as pbar:
            for transcript in valid_transcripts:
                # 이미 요약이 있는지 확인
                existing = self.summarizer.load_summary(transcript['video_id'])
                
                if existing:
                    summaries.append(existing)
                else:
                    # 영어 학습 콘텐츠 판단
                    if self.extractor.is_english_content(transcript):
                        summary = self.summarizer.summarize_english_learning(transcript)
                    else:
                        summary = self.summarizer.summarize_general(transcript)
                    
                    summaries.append(summary)
                
                pbar.update(1)
        
        # 저장
        self.summarizer.save_summaries(summaries)
        
        success_count = len([s for s in summaries if s['status'] == 'success'])
        print(f"  ✅ {success_count}/{len(valid_transcripts)}개 요약 생성 완료")
        
        return summaries
    
    def _categorize_videos(self, videos, transcripts):
        """카테고리 분류"""
        categorized = self.categorizer.categorize_batch(videos, transcripts)
        return categorized
    
    def _generate_reports(self, summaries, categorized):
        """리포트 생성"""
        # Markdown 리포트
        if self.config['output']['markdown_format']:
            self.reporter.generate_markdown_report(summaries, categorized)
        
        # Excel 리포트
        if self.config['output']['excel_export']:
            self.reporter.generate_excel_report(summaries, categorized)
        
        # HTML 리포트 생성 (새로 추가!)
        self.reporter.generate_html_report(summaries, categorized)
        
        # 복습 일정
        english_summaries = [s for s in summaries if s.get('type') == 'english_learning']
        if english_summaries:
            self.reporter.generate_review_schedule(summaries)
        
        # 통계
        self.reporter.generate_statistics(summaries, categorized)
    
    def _print_summary(self, summaries, categorized):
        """결과 요약 출력"""
        print("\n📈 실행 결과:")
        print(f"  - 총 요약 생성: {len([s for s in summaries if s['status'] == 'success'])}개")
        print(f"  - 영어 학습 콘텐츠: {len([s for s in summaries if s.get('type') == 'english_learning'])}개")
        
        whisper_count = len([s for s in summaries if s.get('method') == 'whisper'])
        if whisper_count > 0:
            print(f"  - Whisper 음성 인식: {whisper_count}개")
        
        print("\n📊 카테고리별 분포:")
        for category, videos in sorted(categorized.items()):
            print(f"  - {category}: {len(videos)}개")
        print(f"\n📁 출력 파일: outputs/ 폴더를 확인하세요")


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YouTube 좋아요 영상 요약 시스템 (Whisper 통합)')
    parser.add_argument('--max-videos', type=int, default=50, help='수집할 최대 영상 수')
    parser.add_argument('--force-refresh', action='store_true', help='기존 데이터 무시하고 새로 수집')
    parser.add_argument('--config', default='config/config.yaml', help='설정 파일 경로')
    
    args = parser.parse_args()
    
    # 시스템 실행
    system = YouTubeLikesSummarizer(config_path=args.config)
    system.run_full_pipeline(
        max_videos=args.max_videos,
        force_refresh=args.force_refresh
    )


if __name__ == "__main__":
    main()