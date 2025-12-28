"""
요약 리포트 생성 모듈 (Markdown, Excel, HTML)
"""
import os
import json
from datetime import datetime, timezone, timedelta
import pandas as pd

class ReportGenerator:
    def __init__(self):
        self.output_dir = 'outputs'
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_markdown_report(self, summaries, categorized_videos, filename=None):
        """Markdown 형식 일일 요약 리포트 생성"""
        if not filename:
            filename = f"{datetime.now(timezone(timedelta(hours=9))).strftime('%Y%m%d')}_summary.md"
        
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            # 헤더
            f.write(f"# YouTube 좋아요 영상 요약\n\n")
            f.write(f"**생성일시**: {datetime.now(timezone(timedelta(hours=9))).strftime('%Y년 %m월 %d일 %H:%M')}\n\n")
            f.write(f"**총 영상 수**: {len(summaries)}개\n\n")
            
            # 카테고리별 통계
            f.write("## 📊 카테고리별 분포\n\n")
            for category, videos in sorted(categorized_videos.items()):
                f.write(f"- **{category}**: {len(videos)}개\n")
            f.write("\n---\n\n")
            
            # 성공한 요약이 없으면 메시지 출력
            success_summaries = [s for s in summaries if s.get('status') == 'success']
            
            if not success_summaries:
                f.write("## ⚠️ 알림\n\n")
                f.write("자막을 추출할 수 있는 영상이 없었습니다.\n")
                f.write("- 일부 영상은 자막이 비활성화되어 있거나 자막이 제공되지 않습니다.\n")
                f.write("- 자막이 있는 영상을 좋아요에 추가하시면 다음 실행 시 요약됩니다.\n\n")
            else:
                # 카테고리별 요약
                for category in sorted(categorized_videos.keys()):
                    f.write(f"## 📁 {category}\n\n")
                    
                    category_summaries = [
                        s for s in summaries 
                        if s['status'] == 'success' and 
                        any(v['video_id'] == s['video_id'] for v in categorized_videos[category])
                    ]
                    
                    for i, summary in enumerate(category_summaries, 1):
                        f.write(f"### {i}. {summary['video_title']}\n\n")
                        f.write(f"**채널**: {summary['channel']}  \n")
                        f.write(f"**링크**: [{summary['video_url']}]({summary['video_url']})  \n")
                        f.write(f"**유형**: {'영어학습' if summary['type'] == 'english_learning' else '일반'}\n\n")
                        f.write(f"{summary['summary']}\n\n")
                        f.write("---\n\n")
                
                # 영어 학습 영상 별도 섹션
                english_summaries = [s for s in summaries if s.get('type') == 'english_learning' and s['status'] == 'success']
                
                if english_summaries:
                    f.write("## 📚 영어 학습 콘텐츠 (복습용)\n\n")
                    f.write("*반복 학습을 위해 영어 학습 콘텐츠를 별도로 정리했습니다.*\n\n")
                    
                    for i, summary in enumerate(english_summaries, 1):
                        f.write(f"### {i}. {summary['video_title']}\n\n")
                        f.write(f"[영상 보기]({summary['video_url']})\n\n")
                        f.write(f"{summary['summary']}\n\n")
                        f.write("---\n\n")
        
        print(f"✅ Markdown 리포트 생성 완료: {filepath}")
        return filepath
    
    def generate_excel_report(self, summaries, categorized_videos, filename=None):
        """Excel 형식 학습 데이터베이스 생성"""
        if not filename:
            filename = f"{datetime.now(timezone(timedelta(hours=9))).strftime('%Y%m%d')}_youtube_summaries.xlsx"
        
        filepath = os.path.join(self.output_dir, filename)
        
        # 성공한 요약만 필터링
        success_summaries = [s for s in summaries if s.get('status') == 'success']
        
        if not success_summaries:
            print("⚠️  요약된 영상이 없어 Excel 파일을 생성하지 않습니다.")
            return None
        
        # 데이터 준비
        data = []
        
        # 카테고리 정보 매핑
        video_categories = {}
        for category, videos in categorized_videos.items():
            for video in videos:
                video_categories[video['video_id']] = category
        
        for summary in success_summaries:
            data.append({
                '카테고리': video_categories.get(summary['video_id'], '기타'),
                '제목': summary['video_title'],
                '채널': summary['channel'],
                'URL': summary['video_url'],
                '유형': '영어학습' if summary['type'] == 'english_learning' else '일반',
                '요약': summary['summary'],
                '수집일시': datetime.now(timezone(timedelta(hours=9))).strftime('%Y-%m-%d %H:%M')
            })
        
        # DataFrame 생성
        df = pd.DataFrame(data)
        
        # Excel 저장
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # 전체 시트
            df.to_excel(writer, sheet_name='전체', index=False)
            
            # 카테고리별 시트
            for category in df['카테고리'].unique():
                category_df = df[df['카테고리'] == category]
                sheet_name = category[:31]  # Excel 시트명 길이 제한
                category_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # 영어 학습 전용 시트
            english_df = df[df['유형'] == '영어학습']
            if not english_df.empty:
                english_df.to_excel(writer, sheet_name='영어학습_복습용', index=False)
        
        print(f"✅ Excel 리포트 생성 완료: {filepath}")
        return filepath
    
    def generate_html_report(self, summaries, categorized_videos, filename=None):
        """HTML 웹페이지 리포트 생성"""
        if not filename:
            filename = f"{datetime.now(timezone(timedelta(hours=9))).strftime('%Y%m%d')}_summary.html"
        
        filepath = os.path.join(self.output_dir, filename)
        
        # 성공한 요약만 필터링
        success_summaries = [s for s in summaries if s.get('status') == 'success']
        
        # 통계 계산
        total_videos = len(success_summaries)
        english_count = len([s for s in success_summaries if s.get('type') == 'english_learning'])
        whisper_count = len([s for s in success_summaries if s.get('method') == 'whisper'])
        
        # 카테고리별 영상 매핑
        video_categories = {}
        for category, videos in categorized_videos.items():
            for video in videos:
                video_categories[video['video_id']] = category
        
        # HTML 생성
        html_content = self._generate_html_template(
            success_summaries, 
            categorized_videos,
            total_videos,
            english_count,
            whisper_count
        )
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ HTML 리포트 생성 완료: {filepath}")
        print(f"   웹브라우저로 열기: {filepath}")
        return filepath
    
    def _generate_html_template(self, summaries, categorized_videos, total, english, whisper):
        """HTML 템플릿 생성"""
        html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube 좋아요 요약 - {datetime.now(timezone(timedelta(hours=9))).strftime('%Y.%m.%d')}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Malgun Gothic', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        h1 {{
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
            text-align: center;
        }}
        .date {{
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 1.1em;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }}
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        .category-section {{
            margin-bottom: 40px;
        }}
        .category-header {{
            background: #f8f9fa;
            padding: 15px 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .category-title {{
            font-size: 1.5em;
            color: #333;
            font-weight: bold;
        }}
        .category-count {{
            background: #667eea;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
        }}
        .video-card {{
            background: white;
            border: 2px solid #e9ecef;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 20px;
            transition: all 0.3s;
        }}
        .video-card:hover {{
            border-color: #667eea;
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.2);
            transform: translateY(-2px);
        }}
        .video-header {{
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 15px;
        }}
        .video-title {{
            font-size: 1.3em;
            color: #333;
            font-weight: bold;
            flex: 1;
            margin-right: 15px;
        }}
        .video-title a {{
            color: #667eea;
            text-decoration: none;
            transition: color 0.3s;
        }}
        .video-title a:hover {{
            color: #764ba2;
        }}
        .badge {{
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 0.8em;
            font-weight: bold;
            white-space: nowrap;
        }}
        .badge-english {{
            background: #d4edda;
            color: #155724;
        }}
        .badge-general {{
            background: #cce5ff;
            color: #004085;
        }}
        .badge-whisper {{
            background: #fff3cd;
            color: #856404;
            margin-left: 5px;
        }}
        .video-meta {{
            color: #666;
            font-size: 0.9em;
            margin-bottom: 15px;
        }}
        .video-summary {{
            color: #444;
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            white-space: pre-wrap;
            line-height: 1.8;
        }}
        .filter-buttons {{
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }}
        .filter-btn {{
            padding: 10px 20px;
            border: 2px solid #667eea;
            background: white;
            color: #667eea;
            border-radius: 25px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s;
        }}
        .filter-btn:hover {{
            background: #667eea;
            color: white;
        }}
        .filter-btn.active {{
            background: #667eea;
            color: white;
        }}
        footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #e9ecef;
            color: #666;
        }}
        @media (max-width: 768px) {{
            .container {{ padding: 20px; }}
            h1 {{ font-size: 1.8em; }}
            .stats {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 YouTube 좋아요 요약</h1>
        <div class="date">생성일시: {datetime.now(timezone(timedelta(hours=9))).strftime('%Y년 %m월 %d일 %H:%M')}</div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{total}</div>
                <div class="stat-label">총 요약 영상</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{english}</div>
                <div class="stat-label">영어 학습 콘텐츠</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{whisper}</div>
                <div class="stat-label">Whisper 음성 인식</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(categorized_videos)}</div>
                <div class="stat-label">카테고리</div>
            </div>
        </div>
        
        <div class="filter-buttons">
            <button class="filter-btn active" onclick="filterVideos('all')">전체</button>
            <button class="filter-btn" onclick="filterVideos('english')">영어학습</button>
            <button class="filter-btn" onclick="filterVideos('general')">일반</button>
            <button class="filter-btn" onclick="filterVideos('whisper')">Whisper 인식</button>
        </div>
"""
        
        # 카테고리별 영상
        for category in sorted(categorized_videos.keys()):
            category_summaries = [
                s for s in summaries 
                if any(v['video_id'] == s['video_id'] for v in categorized_videos[category])
            ]
            
            if not category_summaries:
                continue
            
            html += f"""
        <div class="category-section">
            <div class="category-header">
                <div class="category-title">📁 {category}</div>
                <div class="category-count">{len(category_summaries)}개</div>
            </div>
"""
            
            for summary in category_summaries:
                video_type = summary.get('type', 'general')
                method = summary.get('method', 'youtube_api')
                
                type_badge = '<span class="badge badge-english">영어학습</span>' if video_type == 'english_learning' else '<span class="badge badge-general">일반</span>'
                whisper_badge = '<span class="badge badge-whisper">🎤 Whisper</span>' if method == 'whisper' else ''
                
                html += f"""
            <div class="video-card" data-type="{video_type}" data-method="{method}">
                <div class="video-header">
                    <h3 class="video-title">
                        <a href="{summary['video_url']}" target="_blank">{summary['video_title']}</a>
                    </h3>
                    <div>
                        {type_badge}
                        {whisper_badge}
                    </div>
                </div>
                <div class="video-meta">
                    📺 {summary['channel']} | 🔗 <a href="{summary['video_url']}" target="_blank">영상 보기</a>
                </div>
                <div class="video-summary">{summary['summary']}</div>
            </div>
"""
            
            html += """
        </div>
"""
        
        html += f"""
        <footer>
            <p>Powered by Claude AI & Whisper | 생성: {datetime.now(timezone(timedelta(hours=9))).strftime('%Y-%m-%d %H:%M:%S')}</p>
        </footer>
    </div>
    
    <script>
        function filterVideos(type) {{
            document.querySelectorAll('.filter-btn').forEach(btn => {{
                btn.classList.remove('active');
            }});
            event.target.classList.add('active');
            
            const cards = document.querySelectorAll('.video-card');
            cards.forEach(card => {{
                if (type === 'all') {{
                    card.style.display = 'block';
                }} else if (type === 'english') {{
                    card.style.display = card.dataset.type === 'english_learning' ? 'block' : 'none';
                }} else if (type === 'general') {{
                    card.style.display = card.dataset.type === 'general' ? 'block' : 'none';
                }} else if (type === 'whisper') {{
                    card.style.display = card.dataset.method === 'whisper' ? 'block' : 'none';
                }}
            }});
        }}
    </script>
</body>
</html>
"""
        
        return html
    
    def generate_review_schedule(self, summaries, days=[1, 3, 7, 14, 30]):
        """복습 일정 생성"""
        schedule = {}
        today = datetime.now(timezone(timedelta(hours=9)))
        
        english_summaries = [s for s in summaries if s.get('type') == 'english_learning' and s['status'] == 'success']
        
        if not english_summaries:
            return {}
        
        for day in days:
            review_date = (today + timedelta(days=day)).strftime('%Y-%m-%d')
            schedule[review_date] = [
                {
                    'title': s['video_title'],
                    'url': s['video_url'],
                    'day': f"D+{day}"
                }
                for s in english_summaries
            ]
        
        schedule_file = os.path.join(self.output_dir, 'review_schedule.md')
        
        with open(schedule_file, 'w', encoding='utf-8') as f:
            f.write("# 📅 영어 학습 복습 일정\n\n")
            f.write("*간격 반복 학습을 위한 복습 스케줄입니다.*\n\n")
            
            for date in sorted(schedule.keys()):
                videos = schedule[date]
                f.write(f"## {date} ({videos[0]['day']})\n\n")
                
                for video in videos:
                    f.write(f"- [ ] [{video['title']}]({video['url']})\n")
                
                f.write("\n")
        
        print(f"✅ 복습 일정 생성 완료: {schedule_file}")
        return schedule
    
    def generate_statistics(self, summaries, categorized_videos):
        """통계 정보 생성"""
        stats = {
            '총_영상_수': len(summaries),
            '성공_요약_수': len([s for s in summaries if s.get('status') == 'success']),
            '영어학습_콘텐츠': len([s for s in summaries if s.get('type') == 'english_learning']),
            '카테고리별_분포': {cat: len(vids) for cat, vids in categorized_videos.items()},
            '생성일시': datetime.now(timezone(timedelta(hours=9))).isoformat()
        }
        
        stats_file = os.path.join(self.output_dir, 'statistics.json')
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 통계 정보 저장: {stats_file}")
        return stats