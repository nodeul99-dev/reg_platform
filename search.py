"""
키워드 검색 결과 처리 및 하이라이트 모듈.
"""
import re
import html

from db import search_articles

CATEGORIES = ["법령", "모범규준", "사규", "감독규정"]

# 모노톤: 분류별 회색 음영 구분
CATEGORY_COLORS = {
    "법령":    "#1e40af",
    "모범규준": "#0369a1",
    "사규":    "#0891b2",
    "감독규정": "#6366f1",
}


def run_search(keyword: str, selected_categories: list[str]) -> list[dict]:
    cats = selected_categories if selected_categories else None
    return search_articles(keyword, cats)


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

    escaped = html.escape(snippet)
    highlighted = pattern.sub(
        lambda m: f'<mark style="background:#FFF176;padding:0 2px;border-radius:2px;">'
                  f'{html.escape(m.group())}</mark>',
        escaped,
    )
    return prefix + highlighted + suffix


def highlight_full_text(text: str, keyword: str) -> str:
    """
    전체 텍스트에서 키워드를 모두 하이라이트. 줄바꿈 보존.
    문서 뷰어 전용 — 내용을 잘라내지 않음.
    """
    escaped = html.escape(text)
    if keyword.strip():
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        escaped = pattern.sub(
            lambda m: f'<mark style="background:#FFF176;padding:0 2px;border-radius:2px;">'
                      f'{html.escape(m.group())}</mark>',
            escaped,
        )
    return escaped.replace("\n", "<br>")


def category_badge(category: str) -> str:
    color = CATEGORY_COLORS.get(category, "#555")
    return (
        f'<span style="background:{color};color:white;'
        f'padding:2px 8px;border-radius:3px;font-size:0.72rem;'
        f'font-weight:600;margin-left:6px;">{html.escape(category)}</span>'
    )
