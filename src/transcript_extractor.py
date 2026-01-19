"""
YouTube 영상 자막 추출 모듈 (Whisper 음성 인식 통합)
"""
import os
import json
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

# Whisper 관련 import (선택사항)
try:
    import yt_dlp
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

class TranscriptExtractor:
    def __init__(self, use_whisper=False, whisper_model='base'):
        """
        초기화
        
        Args:
            use_whisper: True면 자막 없을 때 Whisper 사용
            whisper_model: tiny, base, small, medium, large
        """
        self.transcript_dir = 'data/transcripts'
        self.audio_dir = 'data/audio'
        os.makedirs(self.transcript_dir, exist_ok=True)
        os.makedirs(self.audio_dir, exist_ok=True)
        
        self.use_whisper = use_whisper and WHISPER_AVAILABLE
        
        if self.use_whisper:
            print("🎤 Whisper 음성 인식 모드 활성화")
            self.whisper_model = whisper.load_model(whisper_model)
        elif use_whisper and not WHISPER_AVAILABLE:
            print("⚠️  Whisper 패키지가 설치되지 않았습니다.")
            print("   설치: pip install openai-whisper yt-dlp")
    
    def extract_transcript(self, video_id, url=None, languages=['ko', 'en']):
        """
        영상의 자막 추출 (자막 없으면 Whisper 사용)
        
        Args:
            video_id: YouTube 영상 ID
            url: YouTube 영상 URL (Whisper 사용 시 필요)
            languages: 선호 언어 리스트
        
        Returns:
            dict: 자막 텍스트와 메타데이터
        """
        # 1단계: YouTube 자막 시도
        transcript = self._extract_youtube_transcript(video_id, languages)
        
        if transcript['status'] == 'success':
            return transcript
        
        # 2단계: 자막 없으면 Whisper 시도
        if self.use_whisper and url:
            print(f"  ℹ️  자막 없음 → Whisper 음성 인식 시도")
            return self._extract_with_whisper(video_id, url)
        
        return transcript
    
    def _extract_youtube_transcript(self, video_id, languages):
        """YouTube 자막 API로 추출"""
        try:
            transcript_data = None
            language_used = None
            
            for lang in languages:
                try:
                    transcript_data = YouTubeTranscriptApi.get_transcript(
                        video_id, 
                        languages=[lang]
                    )
                    language_used = lang
                    break
                except (NoTranscriptFound, Exception):
                    continue
            
            if not transcript_data:
                try:
                    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                    for transcript in transcript_list:
                        transcript_data = transcript.fetch()
                        language_used = transcript.language_code
                        break
                except Exception:
                    pass
            
            if transcript_data:
                full_text = ' '.join([entry['text'] for entry in transcript_data])
                
                result = {
                    'video_id': video_id,
                    'language': language_used,
                    'is_generated': False,
                    'method': 'youtube_api',
                    'text': full_text,
                    'entries': transcript_data,
                    'status': 'success'
                }
                
                print(f"✅ 자막 추출 성공: {video_id} (언어: {language_used})")
                return result
            else:
                return {
                    'video_id': video_id,
                    'status': 'no_transcript',
                    'error': '사용 가능한 자막이 없습니다'
                }
            
        except TranscriptsDisabled:
            return {
                'video_id': video_id,
                'status': 'disabled',
                'error': '자막이 비활성화되어 있습니다'
            }
        except Exception as e:
            return {
                'video_id': video_id,
                'status': 'error',
                'error': str(e)
            }
    
    def _extract_with_whisper(self, video_id, url):
        """Whisper로 음성 인식"""
        try:
            # 1. 오디오 다운로드
            audio_path = self._download_audio(video_id, url)
            if not audio_path:
                return {
                    'video_id': video_id,
                    'status': 'error',
                    'error': '오디오 다운로드 실패'
                }
            
            # 2. 음성 인식
            print(f"  🎤 Whisper 음성 인식 중... (시간 소요)")
            result = self.whisper_model.transcribe(audio_path, verbose=False)
            
            # 3. 세그먼트 변환
            segments = []
            for segment in result['segments']:
                segments.append({
                    'text': segment['text'].strip(),
                    'start': segment['start'],
                    'duration': segment['end'] - segment['start']
                })
            
            # 4. 오디오 파일 삭제
            try:
                os.remove(audio_path)
            except:
                pass
            
            transcript = {
                'video_id': video_id,
                'language': result.get('language', 'unknown'),
                'is_generated': True,
                'method': 'whisper',
                'text': result['text'].strip(),
                'entries': segments,
                'status': 'success'
            }
            
            print(f"✅ Whisper 인식 완료: {video_id} (언어: {result.get('language')})")
            return transcript
            
        except Exception as e:
            print(f"❌ Whisper 인식 실패: {video_id} - {str(e)}")
            return {
                'video_id': video_id,
                'status': 'error',
                'error': str(e)
            }
    
    def _download_audio(self, video_id, url):
        """YouTube 오디오 다운로드"""
        output_path = os.path.join(self.audio_dir, f"{video_id}.mp3")
        
        if os.path.exists(output_path):
            return output_path
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(self.audio_dir, f"{video_id}.%(ext)s"),
            'quiet': True,
            'no_warnings': True,
            'cookiefile': 'youtube.com_cookies.txt'
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            return output_path
        except Exception as e:
            print(f"  ❌ 오디오 다운로드 실패: {str(e)}")
            return None
    
    def extract_multiple(self, videos, use_whisper_fallback=None):
        """
        여러 영상의 자막 일괄 추출
        
        Args:
            videos: 영상 정보 리스트
            use_whisper_fallback: Whisper 사용 여부 (None이면 초기화 설정 따름)
        """
        if use_whisper_fallback is not None:
            original_setting = self.use_whisper
            self.use_whisper = use_whisper_fallback and WHISPER_AVAILABLE
        
        results = []
        
        for i, video in enumerate(videos, 1):
            video_id = video['video_id']
            url = video.get('url', f"https://www.youtube.com/watch?v={video_id}")
            
            print(f"[{i}/{len(videos)}] 자막 추출 중: {video['title'][:50]}...")
            
            transcript = self.extract_transcript(video_id, url)
            
            transcript['video_title'] = video['title']
            transcript['video_url'] = url
            transcript['channel'] = video['channel']
            
            results.append(transcript)
        
        if use_whisper_fallback is not None:
            self.use_whisper = original_setting
        
        success_count = len([r for r in results if r['status'] == 'success'])
        print(f"\n✅ 총 {success_count}/{len(results)}개 영상 자막 추출 완료")
        return results
    
    def save_transcripts(self, transcripts):
        """추출한 자막들을 개별 파일로 저장"""
        for transcript in transcripts:
            if transcript['status'] == 'success':
                video_id = transcript['video_id']
                method = transcript.get('method', 'youtube')
                filepath = os.path.join(
                    self.transcript_dir,
                    f"{video_id}_{method}.json"
                )
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(transcript, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 자막 파일 저장 완료: {self.transcript_dir}")
    
    def load_transcript(self, video_id):
        """저장된 자막 로드"""
        # YouTube API 자막 우선
        filepath = os.path.join(self.transcript_dir, f"{video_id}_youtube_api.json")
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Whisper 자막
        filepath = os.path.join(self.transcript_dir, f"{video_id}_whisper.json")
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return None
    
    def is_english_content(self, transcript):
        """영어 학습 콘텐츠인지 판단"""
        if not transcript or transcript.get('status') != 'success':
            return False
        
        if transcript.get('language') in ['en', 'en-US', 'en-GB']:
            return True
        
        title = transcript.get('video_title', '').lower()
        english_keywords = ['english', '영어', 'toeic', 'speaking', 'grammar', 'vocabulary']
        
        return any(keyword in title for keyword in english_keywords)
