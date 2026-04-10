# AI 동향 보고서 자동화

매일 오전 12시, AI 관련 최신 뉴스를 자동 수집하여 보고서(MD + PDF)를 생성하는 자동화 시스템

---

## 전체 동작 흐름

```
[GitHub Actions - 매일 KST 12:00 자동 실행]
          │
          ▼
┌─────────────────────────────┐
│  1. 뉴스 수집 (RSS)          │
│                             │
│  국내: AI타임스, ZDNet Korea  │
│       전자신문, 디지털투데이   │
│       한국대학신문            │
│  해외: TechCrunch AI        │
│       VentureBeat AI        │
│       The Verge AI          │
│                             │
│  소스당 최신 5개 기사 수집     │
│  → 총 최대 40개 기사          │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  2. 프롬프트 구성             │
│                             │
│  수집된 뉴스 텍스트 +         │
│  보고서 형식 템플릿 결합       │
│                             │
│  [보고서 형식]                │
│  - 이번 주 핵심 요약          │
│  - 1. 글로벌 AI 동향         │
│  - 2. 국내 AI 동향           │
│  - 3. 대학 AI 동향           │
│  - 4. 시사점                 │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  3. Groq API 호출            │
│                             │
│  모델: llama-3.3-70b         │
│  (완전 무료)                  │
│                             │
│  → 보고서 텍스트 생성          │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  4. 후처리                   │
│                             │
│  - 줄바꿈 자동 보정           │
│    (1) 2) 항목 앞 빈 줄)      │
│  - 한자 자동 제거             │
│  - 출처 하이퍼링크 형식 유지   │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  5. MD 파일 저장             │
│                             │
│  reports/AI동향보고서_        │
│          YYYYMMDD.md        │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  6. PDF 변환                 │
│                             │
│  MD → HTML → PDF            │
│  (WeasyPrint + 나눔고딕)      │
│                             │
│  reports/AI동향보고서_        │
│          YYYYMMDD.pdf       │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  7. GitHub 자동 커밋 & 푸시  │
│                             │
│  reports/ 폴더에             │
│  날짜별 MD + PDF 누적 저장    │
└─────────────────────────────┘
```

---

## 파일 구조

```
ai-reporter/
├── .github/
│   └── workflows/
│       └── daily_report.yml   # GitHub Actions 스케줄 설정
├── reports/                   # 생성된 보고서 저장 폴더
│   ├── AI동향보고서_20260409.md
│   ├── AI동향보고서_20260409.pdf
│   └── ...
├── ai_report_generator.py     # 메인 실행 파일
├── requirements.txt           # Python 패키지 목록
└── README.md                  # 이 문서
```

---

## 주요 함수 설명

| 함수 | 역할 |
|------|------|
| `fetch_news()` | RSS 피드에서 최신 기사 수집 |
| `format_for_prompt()` | 수집 기사를 프롬프트용 텍스트로 변환 |
| `build_prompt()` | 보고서 형식 템플릿 + 뉴스 결합 |
| `generate_report()` | Groq API 호출하여 보고서 생성 |
| `fix_line_breaks()` | 줄바꿈 보정 + 한자 제거 후처리 |
| `save_report()` | MD 파일로 저장 |
| `convert_to_pdf()` | MD → PDF 변환 |

---

## 환경 설정

### 필요한 GitHub Secret

| Secret 이름 | 설명 |
|------------|------|
| `GROQ_API_KEY` | Groq API 키 ([console.groq.com](https://console.groq.com)) |

### 로컬 실행

```bash
pip install -r requirements.txt
export GROQ_API_KEY=your_key_here
python ai_report_generator.py
```

---

## 뉴스 소스

| 구분 | 매체 |
|------|------|
| 국내 | AI타임스, ZDNet Korea, 전자신문, 디지털투데이, 한국대학신문 |
| 해외 | TechCrunch AI, VentureBeat AI, The Verge AI |

---

## 보고서 형식

```
생성형 AI 동향 보고서
정보기획팀(이종구): YYYY.MM.DD

【 이번 주 핵심 요약 】
▪ 글로벌 핵심 이슈
▪ 국내 핵심 이슈
▪ 대학/교육 핵심 이슈

1. 글로벌 AI 동향
  가. OpenAI 주요 업데이트
    1) 내용
  나. Google / Gemini 동향
  다. Anthropic / Claude 동향
  라. 기타 글로벌 동향

2. 국내 AI 동향
  가. 정부 정책
  나. 산업 동향

3. 대학 AI 동향
  가. 플랫폼 도입 현황
  나. 정책·가이드라인 현황
```
