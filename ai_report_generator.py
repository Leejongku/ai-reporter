import os
import re
import datetime
import feedparser
from google import genai
from pathlib import Path

# =============================================
# 뉴스 수집 RSS 소스 설정
# =============================================
RSS_FEEDS = {
    # 국내
    "AI타임스":       "https://www.aitimes.com/rss/allArticle.xml",
    "ZDNet Korea":   "https://zdnet.co.kr/rss/",
    "전자신문":       "https://www.etnews.com/rss/allArticle.xml",
    "디지털투데이":   "https://www.digitaltoday.co.kr/rss/allArticle.xml",
    "한국대학신문":   "https://news.unn.net/rss/allArticle.xml",
    # 해외
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "VentureBeat AI":"https://venturebeat.com/category/ai/feed/",
    "The Verge AI":  "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
}

REPORT_DIR = Path(__file__).parent / "reports"
REPORT_DIR.mkdir(exist_ok=True)

MAX_ARTICLES_PER_SOURCE = 5
MAX_SUMMARY_LENGTH      = 400


def fetch_news() -> list[dict]:
    articles = []
    for source_name, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url, request_headers={"User-Agent": "Mozilla/5.0"})
            for entry in feed.entries[:MAX_ARTICLES_PER_SOURCE]:
                summary = entry.get("summary", "")
                summary = re.sub(r"<[^>]+>", "", summary)[:MAX_SUMMARY_LENGTH]
                articles.append({
                    "source":  source_name,
                    "title":   entry.get("title", "").strip(),
                    "summary": summary.strip(),
                    "date":    entry.get("published", ""),
                    "link":    entry.get("link", ""),
                })
        except Exception as e:
            print(f"  [경고] {source_name} 수집 실패: {e}")

    print(f"  총 {len(articles)}개 기사 수집 완료")
    return articles


def format_for_prompt(articles: list[dict]) -> str:
    lines = []
    for a in articles:
        date_str = a["date"][:16] if a["date"] else "날짜 미상"
        lines.append(
            f"[{a['source']}] {a['title']}\n"
            f"{a['summary']}\n"
            f"※ 출처: {a['source']}, {date_str}\n"
        )
    return "\n".join(lines)


def build_prompt(news_text: str, today: str) -> str:
    return f"""아래 수집된 AI 관련 최신 뉴스들을 분석하여, 지정된 형식에 맞게 보고서를 작성해줘.

[작성 규칙]
- 번호 체계는 반드시 1. → 가. → 1) 3단계만 사용
- 모든 항목 끝에 ※ 출처 명시 (※ 출처: 매체명, YYYY.MM.DD)
- 뉴스가 없는 섹션은 "해당 동향 없음"으로 표기
- 표가 필요한 경우 마크다운 표 형식 사용
- 한국어로 작성

[보고서 형식]

생성형 AI 동향 보고서
정보기획팀(이종구): {today}

【 이번 주 핵심 요약 】
▪ (핵심 내용 1 — 가장 중요한 글로벌 이슈)
▪ (핵심 내용 2 — 국내 주요 이슈)
▪ (핵심 내용 3 — 대학/교육 이슈)

1. 글로벌 AI 동향
  가. OpenAI 주요 업데이트
    1) (내용)
  나. Google / Gemini 동향
    1) (내용)
  다. Anthropic / Claude 동향
    1) (내용)
  라. 기타 글로벌 동향
    1) (내용)

2. 국내 AI 동향
  가. 정부 정책
    1) (내용)
  나. 산업 동향
    1) (내용)

3. 대학 AI 동향
  가. 플랫폼 도입 현황
    1) (내용)
  나. 정책·가이드라인 현황
    1) (내용)

4. 시사점
  가. (시사점 1)
  나. (시사점 2)
  다. (시사점 3)

[수집된 뉴스]
{news_text}
"""


def generate_report(news_text: str, today: str) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.0-flash-lite",
        contents=build_prompt(news_text, today)
    )
    return response.text


def save_report(report: str, today_str: str) -> Path:
    filename = REPORT_DIR / f"AI동향보고서_{today_str}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report)
    return filename


def main():
    now     = datetime.datetime.now()
    today   = now.strftime("%Y.%m.%d")
    today_s = now.strftime("%Y%m%d")

    print(f"[{now.strftime('%H:%M:%S')}] AI 동향 보고서 생성 시작")

    print("1) 뉴스 수집 중...")
    articles = fetch_news()
    if not articles:
        print("  수집된 기사가 없습니다. 종료합니다.")
        return

    news_text = format_for_prompt(articles)

    print("2) Gemini API로 보고서 생성 중...")
    report = generate_report(news_text, today)

    print("3) 파일 저장 중...")
    path = save_report(report, today_s)

    print(f"\n완료! 저장 위치: {path}")
    print("-" * 50)
    print(report[:500] + "...")


if __name__ == "__main__":
    main()
