# 🎬 YouTube 좋아요 영상 자동 요약 시스템

> AI(Claude)와 Whisper로 YouTube 좋아요 영상을 자동 요약하고 복습 일정을 생성하는 시스템

[![GitHub Pages](https://img.shields.io/badge/Demo-GitHub%20Pages-blue)](https://hdkim-hub.github.io/youtube-likes-summary/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## ✨ 주요 기능

- 🤖 **AI 자동 요약**: Claude AI가 영상 내용을 자동으로 요약
- 🎤 **음성 인식**: Whisper로 자막 없는 영상도 처리
- 📊 **카테고리 분류**: 영어학습, 기술, 일반 등 자동 분류
- 📅 **복습 일정**: 에빙하우스 망각곡선 기반 복습 일정 자동 생성
- 🌐 **웹 대시보드**: GitHub Pages로 언제든지 확인 가능
- ⏰ **완전 자동화**: 매일 자동 실행, 배포까지 자동

---

## 🚀 빠른 시작 (3단계)

### 1️⃣ 이 Template 사용하기

1. 이 페이지 오른쪽 위 **"Use this template"** 버튼 클릭
2. **"Create a new repository"** 선택
3. Repository 이름 입력 (예: `my-youtube-summary`)
4. **"Create repository"** 클릭

### 2️⃣ API 키 발급

#### Anthropic API 키
1. https://console.anthropic.com/ 접속
2. 회원가입 (무료 크레딧 제공)
3. **API Keys** → **Create Key** → 키 복사

#### YouTube OAuth 인증
1. https://console.cloud.google.com/ 접속
2. 새 프로젝트 생성
3. **YouTube Data API v3** 활성화
4. **OAuth 2.0 Client ID** 생성 (Desktop app)
5. `client_secret.json` 다운로드

### 3️⃣ GitHub Secrets 설정

**Settings → Secrets and variables → Actions → New repository secret**

필요한 3개 Secret:

| Secret 이름 | 설명 | 값 얻는 방법 |
|------------|------|-------------|
| `ANTHROPIC_API_KEY` | Claude AI API 키 | Anthropic 콘솔에서 복사 |
| `CLIENT_SECRET_BASE64` | YouTube OAuth | [가이드 참고](#youtube-oauth-설정) |
| `TOKEN_PICKLE_BASE64` | YouTube 인증 토큰 | [가이드 참고](#youtube-oauth-설정) |

---

## 📖 상세 설정 가이드

### YouTube OAuth 설정

#### 1) 로컬에서 OAuth 인증
```bash
# 프로젝트 클론
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME

# 의존성 설치
pip install -r requirements.txt

# client_secret.json 파일을 프로젝트 폴더에 복사

# 첫 실행 (OAuth 인증)
python main.py --max-videos 5
```

브라우저가 열리면 Google 계정으로 로그인하고 권한 승인
→ `token.pickle` 파일 생성됨

#### 2) Secret으로 변환

**Windows PowerShell:**
```powershell
# CLIENT_SECRET_BASE64 생성
$content = [System.IO.File]::ReadAllBytes("client_secret.json")
$base64 = [Convert]::ToBase64String($content)
$base64 | Set-Clipboard

# TOKEN_PICKLE_BASE64 생성
$tokenContent = [System.IO.File]::ReadAllBytes("token.pickle")
$tokenBase64 = [Convert]::ToBase64String($tokenContent)
$tokenBase64 | Set-Clipboard
```

**Mac/Linux:**
```bash
# CLIENT_SECRET_BASE64 생성
base64 -i client_secret.json | pbcopy

# TOKEN_PICKLE_BASE64 생성
base64 -i token.pickle | pbcopy
```

복사된 값을 GitHub Secrets에 각각 저장

---

## ⚙️ GitHub Actions 설정

### 1) Workflow 권한 부여

**Settings → Actions → General → Workflow permissions**
- ✅ "Read and write permissions" 선택
- ✅ "Allow GitHub Actions to create and approve pull requests" 체크
- **Save**

### 2) GitHub Pages 활성화

**Settings → Pages**
- **Source**: Deploy from a branch
- **Branch**: `gh-pages`, `/ (root)`
- **Save**

---

## 🎯 사용 방법

### 자동 실행 (권장)
- **매일 UTC 0시 (한국시간 오전 9시)** 자동 실행
- 결과는 `https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/` 에서 확인

### 수동 실행
1. GitHub 저장소 → **Actions** 탭
2. **"Daily YouTube Summary"** 클릭
3. **"Run workflow"** 클릭

### 로컬 실행
```bash
python main.py --max-videos 10
```

---

## 🛠️ 커스터마이징

### 실행 시간 변경

`.github/workflows/daily-summary.yml` 파일:
```yaml
on:
  schedule:
    - cron: '0 0 * * *'  # UTC 0시 = 한국 오전 9시
```

| 한국 시간 | cron 설정 |
|---------|-----------|
| 오전 6시 | `'0 21 * * *'` |
| 오전 9시 | `'0 0 * * *'` |
| 정오 12시 | `'0 3 * * *'` |
| 오후 6시 | `'0 9 * * *'` |

### 영상 수 변경

`.github/workflows/daily-summary.yml`:
```yaml
- name: Run YouTube summary
  run: |
    python main.py --max-videos 50  # 원하는 수로 변경
```

---

## 📁 프로젝트 구조
```
youtube-likes-summary/
├── main.py                    # 메인 실행 파일
├── requirements.txt           # Python 의존성
├── config/config.yaml         # 설정 파일
├── src/
│   ├── youtube_collector.py  # YouTube 데이터 수집
│   ├── transcript_extractor.py # 자막/음성 추출
│   ├── summarizer.py          # AI 요약 생성
│   ├── categorizer.py         # 카테고리 분류
│   └── reporter.py            # 리포트 생성
├── .github/workflows/
│   └── daily-summary.yml      # GitHub Actions
├── SETUP_GUIDE.md            # 상세 설정 가이드
└── README.md                 # 이 파일
```

---

## 🔍 문제 해결

자세한 문제 해결 방법은 [`SETUP_GUIDE.md`](SETUP_GUIDE.md)를 참고하세요.

### 자주 발생하는 문제

**Q: GitHub Actions에서 "Permission denied" 에러**
→ Settings → Actions → General → Workflow permissions → "Read and write" 선택

**Q: 404 에러 (GitHub Pages)**
→ Settings → Pages에서 gh-pages 브랜치 선택 확인

**Q: "base64: invalid input" 에러**
→ Secret 값 재생성 (줄바꿈 제거)

---

## 🤝 기여하기

개선 사항이나 버그 리포트는 Issues에 등록해주세요!

---

## 📄 라이선스

MIT License - 자유롭게 사용, 수정, 배포 가능

---

## 🙏 감사의 말

- **Claude AI** (Anthropic) - 강력한 요약 생성
- **Whisper** (OpenAI) - 정확한 음성 인식
- **GitHub Actions** - 완전 자동화

---

## 📞 도움이 필요하신가요?

- 📖 상세 가이드: [`SETUP_GUIDE.md`](SETUP_GUIDE.md)
- 🐛 버그 리포트: [Issues](https://github.com/hdkim-hub/youtube-likes-summary/issues)

---

**⭐ 이 프로젝트가 유용하다면 Star를 눌러주세요!**