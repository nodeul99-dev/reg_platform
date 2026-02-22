"""
전체 조문 뷰어 — 새 탭에서 열리는 독립 뷰어.
- 문서의 모든 조문을 순서대로 표시
- 검색 키워드가 있는 조문에만 노란 배경 + 키워드 강조
- 페이지 로드 후 해당 조문이 화면 중앙에 오도록 자동 스크롤
"""
import html as html_lib

import streamlit as st
import streamlit.components.v1 as components

from db import get_document_by_id, get_articles_by_doc_id
from search import category_badge, highlight_full_text


def render(doc_id: int, target_article_id: int, keyword: str = ""):
    doc = get_document_by_id(doc_id)
    if not doc:
        st.error("문서를 찾을 수 없습니다.")
        return

    articles = get_articles_by_doc_id(doc_id)

    # ── 헤더 ──────────────────────────────────────────────────────────────
    badge = category_badge(doc["doc_category"])
    st.markdown(
        f'<div style="margin-bottom:4px;">'
        f'<span style="font-size:1.1rem;font-weight:700;">📄 {html_lib.escape(doc["doc_name"])}</span>'
        f' {badge}</div>',
        unsafe_allow_html=True,
    )
    kw_label = f" · 검색어: **{keyword}**" if keyword else ""
    st.caption(f"총 {len(articles)}개 조문{kw_label}")
    st.divider()

    # ── 조문 렌더링 ────────────────────────────────────────────────────────
    for article in articles:
        _render_article(article, target_article_id, keyword)

    # ── 자동 스크롤: 대상 조문을 화면 중앙으로 ────────────────────────────
    components.html(
        f"""
        <script>
        (function() {{
            function scrollToTarget() {{
                var el = window.parent.document.getElementById('art-{target_article_id}');
                if (el) {{
                    el.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                }} else {{
                    setTimeout(scrollToTarget, 150);
                }}
            }}
            // DOM이 완전히 그려진 뒤 실행
            setTimeout(scrollToTarget, 600);
        }})();
        </script>
        """,
        height=0,
    )


def _render_article(article: dict, target_article_id: int, keyword: str):
    is_target = article["id"] == target_article_id

    art_num   = html_lib.escape(article["article_number"] or "")
    art_title = html_lib.escape(article["article_title"] or "")
    title_str = f" ({art_title})" if art_title else ""

    # 본문 HTML
    if is_target and keyword:
        body_html = highlight_full_text(article["article_text"], keyword)
    else:
        body_html = html_lib.escape(article["article_text"]).replace("\n", "<br>")

    # 스타일
    if is_target:
        bg     = "#FFFDE7"
        border = "#F9A825"
        label  = (
            '<div style="color:#E65100;font-size:0.72rem;font-weight:700;margin-bottom:6px;">'
            '📍 검색 결과 위치</div>'
        )
    else:
        bg     = "#ffffff"
        border = "#e8e8e8"
        label  = ""

    st.markdown(
        f"""<div id="art-{article['id']}" style="
                border:1px solid {border};
                border-radius:8px;
                padding:14px 18px;
                margin-bottom:10px;
                background:{bg};
            ">
            {label}
            <div style="font-weight:700;color:#1a237e;margin-bottom:8px;font-size:0.95rem;">
                {art_num}{title_str}
            </div>
            <div style="color:#333;font-size:0.9rem;line-height:1.85;word-break:keep-all;">
                {body_html}
            </div>
            <div style="text-align:right;color:#ccc;font-size:0.78rem;margin-top:8px;">
                p.{article['page_number']}
            </div>
        </div>""",
        unsafe_allow_html=True,
    )
