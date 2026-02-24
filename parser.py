"""
PDF에서 텍스트를 추출하고 조문 단위로 파싱하는 모듈.
조문 패턴: 제X조, 제X조의X
조문 제목 패턴: 제X조(제목) 또는 제X조 (제목)
"""
import re
from typing import IO

import pdfplumber

# 조문 시작 패턴 (전체 줄이 조문 번호로 시작하는 경우)
ARTICLE_PATTERN = re.compile(r"^(제\s*\d+조(?:의\s*\d+)?)")
# 조문 제목 포함 패턴
TITLE_PATTERN = re.compile(r"제\s*\d+조(?:의\s*\d+)?\s*[（(]([^）)\n]+)[）)]")
# 목차 항목 판별: 점선(...··) 또는 탭+숫자(페이지번호) 패턴
TOC_PATTERN = re.compile(r"[.·‥…]{3,}|\.{2,}\s*\d+\s*$")
# 단락 구분자: 항/호/목 번호로 시작하는 줄 → 앞에 줄바꿈 삽입
PARAGRAPH_START = re.compile(r"^[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮]|^\d+\.\s|^[가나다라마바사아자차카타파하]\.\s")


def extract_text_by_page(pdf_file: IO[bytes]) -> list[tuple[int, str]]:
    """PDF 파일 객체에서 (page_number, text) 리스트 반환."""
    pages = []
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                pages.append((i, text))
    except Exception as e:
        raise ValueError(f"PDF 텍스트 추출 실패: {e}") from e
    return pages


def _normalize_article_number(raw: str) -> str:
    """공백 제거하여 '제3조의2' 형태로 정규화."""
    return re.sub(r"\s+", "", raw)


def parse_articles(pages: list[tuple[int, str]]) -> list[dict]:
    """
    페이지별 텍스트를 받아 조문 단위 dict 리스트 반환.
    각 dict: {article_number, article_title, article_text, page_number}
    """
    # 전체 텍스트를 (page_number, line) 형태로 펼침
    all_lines: list[tuple[int, str]] = []
    for page_num, text in pages:
        for line in text.splitlines():
            all_lines.append((page_num, line))

    articles: list[dict] = []
    current: dict | None = None

    for page_num, line in all_lines:
        stripped = line.strip()
        if not stripped:
            if current:
                current["article_text"] += "\n"
            continue

        m = ARTICLE_PATTERN.match(stripped)
        if m:
            # 이전 조문 저장
            if current:
                current["article_text"] = current["article_text"].strip()
                articles.append(current)

            raw_number = m.group(1)
            article_number = _normalize_article_number(raw_number)

            # 제목 추출 시도
            title_m = TITLE_PATTERN.search(stripped)
            article_title = title_m.group(1).strip() if title_m else None

            current = {
                "article_number": article_number,
                "article_title": article_title,
                "article_text": stripped + "\n",
                "page_number": page_num,
            }
        else:
            if current:
                # 항/호/목 번호로 시작하면 단락 구분 (줄바꿈)
                # 그 외 일반 연속 줄은 공백으로 연결 (PDF 레이아웃 행바꿈 제거)
                if PARAGRAPH_START.match(stripped):
                    current["article_text"] += "\n" + stripped
                else:
                    # 직전 텍스트가 하이픈으로 끝나면 (단어 분리) 하이픈 제거 후 연결
                    if current["article_text"].endswith("-"):
                        current["article_text"] = current["article_text"][:-1] + stripped
                    else:
                        current["article_text"] += " " + stripped
            # 조문 시작 전 텍스트는 무시

    # 마지막 조문 저장
    if current:
        current["article_text"] = current["article_text"].strip()
        articles.append(current)

    # 목차 항목 제거: 점선 패턴이 있거나 본문이 극히 짧은 항목
    return [a for a in articles if not _is_toc_entry(a)]


def _is_toc_entry(article: dict) -> bool:
    """
    목차 항목 여부 판단.
    - 점선(......) 패턴이 포함된 경우
    - 첫 번째 줄 이후 실질 본문이 거의 없는 경우 (30자 미만)
    """
    text = article["article_text"]

    # 점선 패턴 → 목차
    if TOC_PATTERN.search(text):
        return True

    # 첫 줄(조문 번호+제목 줄) 제거 후 본문 길이 확인
    lines = [l for l in text.splitlines() if l.strip()]
    body = " ".join(lines[1:]).strip()  # 첫 줄 이후
    if len(body) < 30:
        return True

    return False


def parse_pdf(pdf_file: IO[bytes]) -> list[dict]:
    """PDF 파일 객체 → 조문 리스트."""
    pages = extract_text_by_page(pdf_file)
    return parse_articles(pages)


# 시행일 추출 패턴 (우선순위 순)
_ENACTED_PATTERNS = [
    # "2026년 2월 3일부터 시행" / "2026년 2월 3일 시행"
    re.compile(r"(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일\s*(?:부터\s*)?시행"),
    # "시행일 : 2026. 2. 3" / "시행일: 2026.2.3"
    re.compile(r"시행일?\s*[：:\s]\s*(\d{4})[.\s]\s*(\d{1,2})[.\s]\s*(\d{1,2})"),
    # "2026. 2. 3. 시행" / "2026.2.3 시행"
    re.compile(r"(\d{4})[.]\s*(\d{1,2})[.]\s*(\d{1,2})[.]?\s*시행"),
]


def extract_enacted_date(pdf_file: IO[bytes]) -> str | None:
    """
    PDF 전체 텍스트에서 시행일을 추출하여 'YYYY-MM-DD' 형식으로 반환.
    부칙(附則) 근처를 우선 탐색하고, 없으면 전체 텍스트에서 탐색.
    """
    pdf_file.seek(0)
    pages = extract_text_by_page(pdf_file)
    full_text = "\n".join(text for _, text in pages)

    # 부칙 섹션 우선 탐색
    addendum_match = re.search(r"부\s*칙", full_text)
    search_text = full_text[addendum_match.start():] if addendum_match else full_text

    for pattern in _ENACTED_PATTERNS:
        m = pattern.search(search_text)
        if not m:
            # 부칙에 없으면 전체 재탐색
            m = pattern.search(full_text)
        if m:
            year, month, day = m.group(1), m.group(2), m.group(3)
            return f"{year}-{int(month):02d}-{int(day):02d}"

    return None
