import os
import re
import datetime
import feedparser
from groq import Groq
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
    return f"""당신은 AI 전문 보고서 작성 전문가입니다.
아래 수집된 AI 관련 최신 뉴스들을 심층 분석하여 전문적인 보고서를 작성해주세요.

[작성 규칙]
- 번호 체계는 반드시 1. → 가. → 1) 3단계만 사용
- 각 항목은 단순 요약이 아닌 의미·배경·영향을 포함하여 2~4문장으로 상세히 서술
- 모든 항목 끝에 반드시 출처 명시: ※ 출처: 매체명, YYYY.MM.DD
- 뉴스가 없는 섹션은 "해당 동향 없음"으로 표기
- 전문 보고서 문체로 한국어 작성 (구어체 금지)
- 시사점은 단순 사실 나열이 아닌 전략적 관점의 인사이트 제시
- 반드시 각 소제목(가. 나. 다.) 앞뒤로 빈 줄을 삽입할 것
- 반드시 각 대제목(1. 2. 3. 4.) 앞뒤로 빈 줄을 삽입할 것
- ▪ 항목은 각각 별도 줄에 작성할 것

[보고서 형식 - 빈 줄 포함하여 아래 형식을 정확히 따를 것]

생성형 AI 동향 보고서
정보기획팀(이종구): {today}

【 이번 주 핵심 요약 】
▪ (글로벌 핵심 이슈 — 어떤 기업/기술이 왜 중요한지 한 문장으로)
▪ (국내 핵심 이슈 — 정책·산업 동향 중 가장 중요한 사항)
▪ (대학/교육 핵심 이슈 — AI 교육·도입 관련 주요 사항)


1. 글로벌 AI 동향

  가. OpenAI 주요 업데이트
    1) (업데이트 내용과 그 의미, 산업에 미치는 영향 상세 서술)
    2) (추가 동향이 있을 경우)
    ※ 출처: 매체명, YYYY.MM.DD

  나. Google / Gemini 동향
    1) (신규 모델·서비스 발표 내용과 기술적 의미 상세 서술)
    2) (추가 동향이 있을 경우)
    ※ 출처: 매체명, YYYY.MM.DD

  다. Anthropic / Claude 동향
    1) (신규 기능·정책 내용과 시장 영향 상세 서술)
    ※ 출처: 매체명, YYYY.MM.DD

  라. 기타 글로벌 동향
    1) (Meta, Microsoft, xAI 등 주요 글로벌 AI 기업 동향)
    ※ 출처: 매체명, YYYY.MM.DD


2. 국내 AI 동향

  가. 정부 정책
    1) (정책명, 지원 규모, 추진 배경, 기대 효과 상세 서술)
    2) (추가 정책이 있을 경우)
    ※ 출처: 매체명, YYYY.MM.DD

  나. 산업 동향
    1) (국내 주요 기업의 AI 도입·개발 현황과 시장 의미 상세 서술)
    2) (추가 동향이 있을 경우)
    ※ 출처: 매체명, YYYY.MM.DD


3. 대학 AI 동향

  가. 플랫폼 도입 현황
    1) (도입 대학명, 플랫폼명, 주요 기능, 도입 배경 상세 서술)
    2) (추가 사례가 있을 경우)
    ※ 출처: 매체명, YYYY.MM.DD

  나. 정책·가이드라인 현황
    1) (가이드라인 내용, 적용 범위, 의의 상세 서술)
    ※ 출처: 매체명, YYYY.MM.DD


4. 시사점

  가. (글로벌 동향에서 도출한 전략적 인사이트 — 우리 기관이 주목해야 할 점)

  나. (국내 정책·산업 동향에서 도출한 대응 방향)

  다. (대학 AI 도입 트렌드에서 도출한 시사점)

[수집된 뉴스]
{news_text}
"""


def generate_report(news_text: str, today: str) -> str:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY 환경변수가 설정되지 않았습니다.")

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{
            "role": "user",
            "content": build_prompt(news_text, today)
        }],
        max_tokens=4096,
    )
    return response.choices[0].message.content


def fix_line_breaks(report: str) -> str:
    """대제목·소제목·항목 앞뒤 빈 줄 보정"""
    lines = report.splitlines()
    result = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        # 대제목 (1. 2. 3. 4.) 앞에 빈 줄 추가
        if stripped and stripped[0].isdigit() and len(stripped) > 1 and stripped[1] == '.':
            if result and result[-1] != '':
                result.append('')
        # 소제목 (가. 나. 다. 라.) 앞에 빈 줄 추가
        if stripped and stripped[0] in '가나다라마바사' and len(stripped) > 1 and stripped[1] == '.':
            if result and result[-1] != '':
                result.append('')
        result.append(line)
        # 대제목·소제목 뒤에 빈 줄 추가
        if stripped and stripped[0].isdigit() and len(stripped) > 1 and stripped[1] == '.':
            result.append('')
    # 연속된 빈 줄 2개 이상 → 1개로
    cleaned = []
    prev_blank = False
    for line in result:
        if line.strip() == '':
            if not prev_blank:
                cleaned.append(line)
            prev_blank = True
        else:
            cleaned.append(line)
            prev_blank = False
    return '\n'.join(cleaned)


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

    print("2) Groq API로 보고서 생성 중...")
    report = generate_report(news_text, today)

    print("3) 줄바꿈 보정 및 파일 저장 중...")
    report = fix_line_breaks(report)
    path = save_report(report, today_s)

    print(f"\n완료! 저장 위치: {path}")
    print("-" * 50)
    print(report[:500] + "...")


if __name__ == "__main__":
    main()
