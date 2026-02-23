# PRD: DS투자증권 규정 검색 플랫폼 v2.0

## 프로젝트 개요

**프로젝트명:** DS투자증권 규정 검색 플랫폼  
**버전:** v2.0 (법제처 오픈API 연동 예정)  
**기술 스택:** Python, Streamlit, pdfplumber, pymupdf(fitz), SQLite, 법제처 오픈API  
**실행 환경:** 로컬 PC, 팀원은 PC IP로 접속  
**대상 사용자:** DS투자증권 리스크관리팀 전체  
**목표:** 법령·감독규정은 법제처 오픈API로 자동 수집·최신화하고, 사규·모범규준은 PDF 업로드로 관리하는 하이브리드 구조의 조문 단위 키워드 검색 시스템

---

## 실행 방법

```bash
cd C:\Users\opus6\Desktop\VibeCoding\reg_platform\regulation_search
streamlit run app.py
```
접속: http://localhost:8501  
팀원 접속: http://[PC_IP]:8501 (실행 시 `--server.address 0.0.0.0` 추가)

---

## 프로젝트 구조

```
regulation_search/
├── app.py                   # 진입점, 전역 CSS, 상단바, 라우팅
├── db.py                    # SQLite (documents + articles 테이블)
├── parser.py                # PDF → 조문 파싱, 시행일 추출
├── search.py                # 검색 로직, highlight_text, category_badge
├── highlighter.py           # pymupdf로 키워드 하이라이트 PDF 생성 (캐시)
├── law_api.py               # 법제처 오픈API 호출, XML 파싱 (신규 추가 예정)
├── views/
│   ├── search_page.py       # 검색 UI (히스토리, 필터, 카드, 페이지네이션)
│   └── docs.py              # 문서 관리 (업로드 + 등록 목록, 삭제, API 업데이트)
├── static/
│   ├── uploads/             # 업로드된 원본 PDF
│   └── highlighted/         # 하이라이트 처리된 PDF 캐시
├── data/
│   └── regulations.db
├── .env                     # API 키 (Git 제외)
├── .env.example             # 환경변수 템플릿
└── .streamlit/
    └── config.toml
```

---

## UI / 디자인

### 색상 팔레트 (파란색 테마)

| 요소 | 색상 |
|------|------|
| 상단바 | `#0f2744` (딥 네이비) |
| 버튼 (primary) | `#2563eb` (블루) |
| 카테고리 뱃지 — 법령 | `#1e40af` |
| 카테고리 뱃지 — 모범규준 | `#0369a1` |
| 카테고리 뱃지 — 사규 | `#0891b2` |
| 카테고리 뱃지 — 감독규정 | `#6366f1` |
| 카드 테두리 | `#dde9ff` |
| 카드 호버 | `#93c5fd` |
| Streamlit primaryColor | `#2563eb` |
| Streamlit textColor | `#0f2744` |

### 레이아웃

- **사이드바 없음** — CSS로 완전히 숨김
- **상단바** — `#0f2744` 딥 네이비 배경, 우측 링크로 페이지 전환
- **네비게이션** — URL 쿼리 파라미터 방식 (`?page=search` / `?page=docs`)
- **`pages/` 폴더 미사용** — `views/` 폴더로 수동 라우팅 (Streamlit 자동 네비 방지)

---

## 핵심 기능

### 1. 키워드 검색 (search_page.py)

- 검색창 입력 → 조문 단위 검색 결과 카드 표시
- **카테고리 필터**: 법령 / 모범규준 / 사규 / 감독규정
- **페이지네이션**: 결과 다량 시 페이지 분할
- **검색 히스토리**: 최근 6개 저장, 클릭 시 재검색
  - `session_state` 저장 + URL 파라미터(`hist_kw`)로 클릭 처리
- **카드 클릭** → pymupdf 하이라이트 PDF 새 탭 오픈
- **TOC 필터링**: `_is_toc_entry()`로 목차 조문 제외

### 2. 하이라이트 PDF (highlighter.py)

- pymupdf(fitz)로 원본 PDF에 키워드 하이라이트 처리
- `static/highlighted/{doc_id}_{keyword_hash}.pdf` 형태로 캐시 저장
- 동일 키워드 재검색 시 캐시 파일 재사용

### 3. 문서 관리 (docs.py)

- **PDF 업로드** — 사규·모범규준 전용
  - PDF → 조문 파싱 → DB 저장
  - 시행일 자동 추출 (parser.py)
- **등록 목록** — 등록된 규정 탭에서 목록 확인 및 삭제
- **API 업데이트 버튼** (신규 추가 예정) — 법령·감독규정 대상

### 4. 법제처 API 연동 (law_api.py — 신규 추가 예정)

- 문서 관리(docs.py) 화면에 "전체 법령 업데이트" 및 개별 "업데이트" 버튼 추가
- API 대상 문서: 자본시장법, 자본시장법 시행령, 금융투자업규정, 금융투자업 감독규정
- API 키는 `.env` 파일로 관리

**사용 API 엔드포인트:**
```
# 법령 조문 조회 (법률/시행령)
GET https://open.law.go.kr/LSO/openApi/getMOLSLaw.do
  ?OC={API_KEY}&target=law&type=XML&query={법령명}

# 행정규칙 조문 조회 (금융투자업규정 등 고시)
GET https://open.law.go.kr/LSO/openApi/getMOLSAdmRul.do
  ?OC={API_KEY}&target=admrul&type=XML&query={행정규칙명}
```

**파싱 예시:**
```python
import xml.etree.ElementTree as ET
import requests
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("LAW_API_KEY")

def fetch_law_articles(law_name: str) -> list[dict]:
    url = "https://open.law.go.kr/LSO/openApi/getMOLSLaw.do"
    params = {"OC": API_KEY, "target": "law", "type": "XML", "query": law_name}
    response = requests.get(url, params=params, timeout=30)
    root = ET.fromstring(response.content)
    articles = []
    for article in root.iter("조문"):
        articles.append({
            "article_number": article.findtext("조문번호"),
            "article_title":  article.findtext("조문제목"),
            "article_text":   article.findtext("조문내용"),
        })
    return articles
```

---

## DB 스키마

```sql
-- 문서 테이블
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_name TEXT NOT NULL,
    doc_category TEXT NOT NULL,   -- '법령', '모범규준', '사규', '감독규정'
    source_type TEXT NOT NULL,    -- 'api' | 'pdf'
    effective_date TEXT,          -- 시행일자 (API 수신 또는 parser 추출)
    filename TEXT,                -- PDF 업로드 시에만 사용
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
    page_number INTEGER           -- API 수신 시 NULL
);
```

---

## 문서 소스 전략

| 분류 | 소스 | 업데이트 방식 | 주요 문서 |
|------|------|-------------|---------|
| 법령 | 법제처 오픈API | 버튼 클릭 자동 수신 | 자본시장법, 시행령 |
| 감독규정 | 법제처 오픈API | 버튼 클릭 자동 수신 | 금융투자업규정, 감독규정 |
| 모범규준 | PDF 업로드 | 수동 재업로드 | 리스크관리 모범규준 |
| 사규 | PDF 업로드 | 수동 재업로드 | NCR관리규정 등 |

---

## 의존성

```
streamlit
pdfplumber
pymupdf          # fitz, 하이라이트 PDF 생성
requests         # 법제처 API 호출
python-dotenv    # .env API 키 관리
sqlite3          # Python 내장
```

설치 방법:
```bash
py -m pip install streamlit pdfplumber pymupdf requests python-dotenv
```

---

## API 키 발급 및 설정

1. `https://open.law.go.kr` 회원가입 후 오픈API 신청 (1~2 영업일)
2. 프로젝트 루트에 `.env` 파일 생성:
   ```
   LAW_API_KEY=발급받은키값
   ```
3. `.gitignore`에 `.env` 추가 (필수)
4. 사내 방화벽에서 `open.law.go.kr` 외부 접근 허용 여부 IT 확인

---

## 남은 작업 (v2.0)

1. `law_api.py` 신규 작성 — 법제처 API 호출 및 XML 파싱
2. `db.py` 수정 — `source_type`, `effective_date` 컬럼 추가
3. `views/docs.py` 수정 — "전체 법령 업데이트" / 개별 "업데이트" 버튼 추가, API 문서 행 구분
4. `views/search_page.py` 수정 — source 배지(API/PDF), 시행일자 표시 추가
5. `.env.example` 생성
6. `requirements.txt` 업데이트

---

## 제외 범위 (v2.0)

- HWP, Word 문서 지원
- 사용자 권한 관리 / 로그인
- 의미 기반 검색 (벡터 유사도)
- 개정 이력 추적 / 신구 조문 비교
- 법령 개정 자동 감지 및 알림
