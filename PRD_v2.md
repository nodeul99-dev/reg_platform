# PRD: DS투자증권 규정 검색 플랫폼 v2.0

## 프로젝트 개요

**프로젝트명:** DS투자증권 규정 검색 플랫폼  
**버전:** v2.0  
**기술 스택:** Python, Streamlit, pdfplumber, requests, BeautifulSoup, SQLite  
**배포 환경:** 로컬 PC (Streamlit), 팀원은 PC IP로 접속  
**대상 사용자:** DS투자증권 리스크관리팀 전체

---

## 핵심 설계 원칙

1. **PDF 파일 미보관** — 회사 PC 자동 암호화 정책으로 인해 시스템 내부에 PDF 파일을 일절 저장하지 않는다. 업로드된 PDF는 파싱 즉시 삭제한다.
2. **로컬 DB 우선** — 모든 검색은 로컬 SQLite DB만 사용한다. 외부 호출은 업데이트 버튼 클릭 시에만 발생한다.
3. **하이브리드 소스** — 법령/감독규정은 크롤링, 사규/모범규준은 PDF 업로드(파싱 후 삭제).

---

## 문서 소스 전략

| 분류 | 입력 방식 | 저장 | PDF 보관 | 업데이트 |
|------|---------|------|---------|---------|
| 법령 | 법령정보센터 크롤링 | 로컬 DB | ❌ | 버튼 클릭 |
| 감독규정 | 법령정보센터 크롤링 | 로컬 DB | ❌ | 버튼 클릭 |
| 모범규준 | PDF 업로드 → 파싱 후 즉시 삭제 | 로컬 DB | ❌ | 재업로드 |
| 사규 | PDF 업로드 → 파싱 후 즉시 삭제 | 로컬 DB | ❌ | 재업로드 |

**크롤링 대상 문서 (www.law.go.kr):**
- 자본시장과 금융투자업에 관한 법률
- 자본시장과 금융투자업에 관한 법률 시행령
- 금융투자업규정
- 금융투자업 감독규정

---

## 기능 요구사항

### 1. 키워드 검색 (기존 유지)
- 검색창 → 조문 단위 전체 검색
- 카테고리 필터: 법령 / 감독규정 / 모범규준 / 사규
- 검색 결과 카드: 문서명·분류 뱃지·source 뱃지(크롤링/PDF)·조문번호·조문제목·전문(하이라이트)·시행일자
- 페이지네이션
- 검색 히스토리 (최근 6개, session_state + URL 파라미터)
- TOC 필터링 (_is_toc_entry()로 목차 조문 제외)

### 2. 조문 상세 뷰 (PDF 뷰어 대체)
- 카드 클릭 시 DB 텍스트 기반 조문 전문 표시
- 확장 카드 또는 모달 방식
- PDF 파일 호출 없음

### 3. 문서 업로드 (사규·모범규준 전용)
- 분류 선택: 모범규준 / 사규만 선택 가능
- PDF 업로드 → pdfplumber 텍스트 추출 → 조문 파싱 → DB 저장 → PDF 즉시 삭제
- 파싱 완료 후 인식 조문 수 표시
- 안내 문구: "법령·감독규정은 문서 관리 탭에서 업데이트하세요"

### 4. 크롤링 업데이트 (신규)
- 문서 관리 화면에 [전체 법령 업데이트] 버튼
- 법령/감독규정 행에 개별 [업데이트] 버튼
- 클릭 시 law.go.kr 크롤링 → 조문 파싱 → DB 덮어쓰기
- 실패 시 기존 DB 유지, 에러 메시지 표시
- 성공 시 수신 조문 수 및 시행일자 표시

### 5. 문서 관리
- 등록 문서 목록: 문서명·분류·source(크롤링/PDF)·조문 수·시행일자·업데이트/삭제 버튼
- 법령/감독규정 행: [업데이트] 버튼
- 사규/모범규준 행: [삭제] 버튼

---

## DB 스키마

```sql
-- 문서 테이블
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_name TEXT NOT NULL,
    doc_category TEXT NOT NULL,   -- '법령', '감독규정', '모범규준', '사규'
    source_type TEXT NOT NULL,    -- 'crawler' | 'pdf'
    effective_date TEXT,          -- 시행일자
    filename TEXT,                -- PDF 업로드 시 임시 사용 (파싱 후 NULL 처리)
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    article_count INTEGER DEFAULT 0
);

-- 조문 테이블
CREATE TABLE articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    article_number TEXT,          -- '제3조'
    article_title TEXT,           -- '순자본비율의 산출'
    article_text TEXT NOT NULL,
    page_number INTEGER           -- 크롤링 시 NULL
);
```

---

## 크롤러 설계 (crawler.py)

```python
import requests
from bs4 import BeautifulSoup

# 크롤링 대상 목록 (확장 가능)
CRAWL_TARGETS = [
    {"name": "자본시장과 금융투자업에 관한 법률", "category": "법령",    "query": "자본시장법"},
    {"name": "자본시장법 시행령",                 "category": "법령",    "query": "자본시장과+금융투자업에+관한+법률+시행령"},
    {"name": "금융투자업규정",                    "category": "감독규정", "query": "금융투자업규정"},
    {"name": "금융투자업 감독규정",               "category": "감독규정", "query": "금융투자업+감독규정"},
]

def crawl_law(query: str) -> list[dict]:
    """
    www.law.go.kr에서 법령 조문을 크롤링
    반환: [{article_number, article_title, article_text, effective_date}]
    """
    ...
```

---

## 파일 구조

```
regulation_search/
├── app.py                   # 진입점, 전역 CSS, 상단바, 라우팅
├── db.py                    # SQLite CRUD (source_type, effective_date 포함)
├── parser.py                # PDF 텍스트 추출 + 조문 파싱 + PDF 즉시 삭제
├── search.py                # 검색 로직, highlight_text, category_badge
├── crawler.py               # 법령정보센터 크롤링 (신규)
├── views/
│   ├── search_page.py       # 검색 UI + 조문 텍스트 상세 뷰
│   └── docs.py              # 문서 관리 (업로드 + 크롤링 업데이트 버튼)
├── data/
│   └── regulations.db
└── .streamlit/
    └── config.toml
```

**제거 대상:**
- `highlighter.py` — PDF 뷰어 폐기로 불필요
- `static/uploads/` — PDF 미보관 정책
- `static/highlighted/` — PDF 뷰어 폐기

---

## UI / 디자인 (기존 유지)

### 색상 팔레트
| 요소 | 색상 |
|------|------|
| 상단바 | `#0f2744` |
| 버튼 primary | `#2563eb` |
| 뱃지 — 법령 | `#1e40af` |
| 뱃지 — 모범규준 | `#0369a1` |
| 뱃지 — 사규 | `#0891b2` |
| 뱃지 — 감독규정 | `#6366f1` |
| 카드 테두리 | `#dde9ff` |
| 카드 호버 | `#93c5fd` |

### 레이아웃
- 사이드바 없음 (CSS로 숨김)
- URL 쿼리 파라미터 네비게이션 (`?page=search` / `?page=docs`)
- `pages/` 폴더 미사용 → `views/` 수동 라우팅

---

## 의존성

```
streamlit
pdfplumber
requests
beautifulsoup4
sqlite3          # Python 내장
```

```bash
py -m pip install streamlit pdfplumber requests beautifulsoup4
```

---

## 제외 범위 (v2.0)

- HWP, Word 문서 지원
- 사용자 권한 관리 / 로그인
- 의미 기반 검색 (벡터 유사도)
- 개정 이력 추적 / 신구 조문 비교
- 법령 개정 자동 감지 및 알림
- pymupdf (fitz) — highlighter.py 제거로 불필요
