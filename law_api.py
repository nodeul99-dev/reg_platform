"""
법제처 국가법령정보 오픈API 연동 모듈.
법령(자본시장법/시행령) 및 행정규칙(감독규정)을 조문 단위로 수신.
"""
import os
import xml.etree.ElementTree as ET

import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("LAW_API_KEY", "")

# 자동 수신 대상 법령 목록
MANAGED_LAWS = [
    {"name": "자본시장과 금융투자업에 관한 법률", "category": "법령", "type": "law"},
    {"name": "자본시장과 금융투자업에 관한 법률 시행령", "category": "법령", "type": "law"},
    {"name": "금융투자업규정", "category": "감독규정", "type": "admrul"},
    {"name": "금융투자업 감독규정", "category": "감독규정", "type": "admrul"},
]


def fetch_law_articles(law_name: str, law_type: str = "law") -> tuple[list[dict], str | None]:
    """
    법제처 API로 조문 목록과 시행일을 수신.

    law_type: 'law' (법률/시행령) | 'admrul' (고시/행정규칙)
    Returns: (articles, effective_date)
    """
    if not API_KEY:
        raise ValueError("LAW_API_KEY가 설정되어 있지 않습니다. .env 파일을 확인해주세요.")

    if law_type == "law":
        endpoint = "https://open.law.go.kr/LSO/openApi/getMOLSLaw.do"
    else:
        endpoint = "https://open.law.go.kr/LSO/openApi/getMOLSAdmRul.do"

    params = {"OC": API_KEY, "target": law_type, "type": "XML", "query": law_name}
    resp = requests.get(endpoint, params=params, timeout=30)
    resp.raise_for_status()

    root = ET.fromstring(resp.content)

    effective_date = (
        root.findtext(".//시행일")
        or root.findtext(".//공포일")
        or root.findtext(".//법령정보/시행일")
    )

    articles = []
    for article in root.iter("조문"):
        text = article.findtext("조문내용") or ""
        if not text.strip():
            continue
        articles.append({
            "article_number": article.findtext("조문번호") or "",
            "article_title":  article.findtext("조문제목") or "",
            "article_text":   text,
            "page_number":    None,
        })

    return articles, effective_date


def update_single_law(law_info: dict) -> tuple[int, str | None]:
    """
    단일 법령을 API로 수신하여 DB에 upsert.
    Returns: (article_count, effective_date)
    """
    from db import upsert_document, insert_articles, update_article_count

    articles, effective_date = fetch_law_articles(law_info["name"], law_info["type"])
    doc_id = upsert_document(
        doc_name=law_info["name"],
        doc_category=law_info["category"],
        filename="",
        enacted_date=effective_date,
        source_type="api",
    )
    insert_articles(doc_id, articles)
    update_article_count(doc_id, len(articles))
    return len(articles), effective_date
