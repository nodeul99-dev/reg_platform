"""
키워드 검색 결과 처리 및 하이라이트 모듈.
"""
import re
import html

from db import search_articles

CATEGORIES = ["법령", "모범규준", "사규", "감독규정"]

# 모노톤: 분류별 회색 음영 구분
CATEGORY_COLORS = {
    "법령":    "#15803d",
    "모범규준": "#047857",
    "사규":    "#0f766e",
    "감독규정": "#4d7c0f",
}


def run_search(keyword: str, selected_categories: list[str]) -> list[dict]:
    cats = selected_categories if selected_categories else None
    return search_articles(keyword, cats)


_MARK_STYLE = (
    'background:#a3e635;color:#14532d;'
    'padding:0 2px;border-radius:2px;font-weight:600;'
)


def _apply_highlight(escaped_text: str, keyword: str) -> str:
    """이미 html.escape 된 텍스트에 키워드 하이라이트 적용."""
    if not keyword or not keyword.strip():
        return escaped_text
    pattern = re.compile(re.escape(html.escape(keyword)), re.IGNORECASE)
    return pattern.sub(
        lambda m: f'<mark style="{_MARK_STYLE}">{m.group()}</mark>',
        escaped_text,
    )


def highlight_snippet(text: str, keyword: str) -> str:
    """
    평문 스니펫에서 키워드를 라임 그린으로 하이라이트 (HTML 반환).
    카드 미리보기 전용.
    """
    return _apply_highlight(html.escape(text), keyword)


def highlight_text(text: str, keyword: str, max_chars: int = 400) -> str:
    """
    텍스트에서 키워드를 하이라이트(HTML <mark>)하여 반환.
    키워드 주변 max_chars 글자만 표시.
    """
    if not keyword.strip():
        escaped = html.escape(text[:max_chars])
        return escaped + ("..." if len(text) > max_chars else "")

    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    match = pattern.search(text)

    if match:
        start = max(0, match.start() - 100)
        end = min(len(text), match.end() + 300)
        snippet = text[start:end]
        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(text) else ""
    else:
        snippet = text[:max_chars]
        prefix = ""
        suffix = "..." if len(text) > max_chars else ""

    return prefix + _apply_highlight(html.escape(snippet), keyword) + suffix


_PARAGRAPH_START = re.compile(
    r"^[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮]|^\d+\.\s|^[가나다라마바사아자차카타파하]\.\s"
)


def normalize_article_text(text: str) -> str:
    """
    조문 텍스트 정규화.
    - PDF 레이아웃 행바꿈(의미 없는 줄바꿈)은 공백으로 연결
    - 항/호/목 번호(①②③, 1. 2., 가. 나.) 앞 줄바꿈만 유지
    - 연속 공백 제거
    """
    lines = text.splitlines()
    result = ""
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if result:
                result += "\n"  # 빈 줄은 단락 구분으로 유지
            continue
        if not result:
            result = stripped
        elif _PARAGRAPH_START.match(stripped):
            result += "\n" + stripped
        else:
            if result.endswith("-"):
                result = result[:-1] + stripped   # 하이픈 단어 분리 복원
            else:
                result += " " + stripped
    return re.sub(r"[ \t]{2,}", " ", result)


def highlight_full_text(text: str, keyword: str) -> str:
    """
    전체 텍스트에서 키워드를 모두 하이라이트. 의미 있는 줄바꿈만 보존.
    문서 뷰어 전용 — 내용을 잘라내지 않음.
    """
    normalized = normalize_article_text(text)
    escaped = _apply_highlight(html.escape(normalized), keyword)
    return escaped.replace("\n", "<br>")


def category_badge(category: str) -> str:
    color = CATEGORY_COLORS.get(category, "#555")
    return (
        f'<span style="background:{color};color:white;'
        f'padding:2px 8px;border-radius:3px;font-size:0.72rem;'
        f'font-weight:600;margin-left:6px;">{html.escape(category)}</span>'
    )
