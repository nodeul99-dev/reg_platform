# PRD: 리스크관리팀 규정 검색 시스템

## 프로젝트 개요

**프로젝트명:** 리스크관리팀 내부 규정 검색 시스템  
**기술 스택:** Python, Streamlit, pdfplumber, SQLite  
**배포 환경:** 사내 서버 (Streamlit 서버 구동)  
**대상 사용자:** DS투자증권 리스크관리팀 전체  
**목표:** PDF 형태의 법령·모범규준·사규를 업로드하고, 조문(제XX조) 단위로 인덱싱하여 키워드 검색 시 해당 조문 내용을 즉시 확인할 수 있는 웹 애플리케이션 구축

---

## 핵심 기능 요구사항

### 1. 문서 업로드 및 파싱

- PDF 파일 업로드 (단일 또는 복수)
- 문서 분류 태그 지정 (예: 법령 / 모범규준 / 사규 / 감독규정)
- PDF에서 텍스트 추출 (`pdfplumber` 사용)
- 조문 단위 파싱: `제X조`, `제X조의X` 패턴 인식
- 조문 제목 추출: `제X조(제목)` 형태 파싱
- 파싱 결과 미리보기 제공 (업로드 후 인식된 조문 수 표시)

### 2. 인덱싱 및 저장

- SQLite DB에 다음 정보 저장:
  - 문서명 (파일명 또는 사용자 입력명)
  - 문서 분류 (법령/모범규준/사규/감독규정)
  - 조문 번호 (예: 제3조)
  - 조문 제목 (예: 순자본비율의 산출)
  - 조문 전문 텍스트
  - 페이지 번호
  - 업로드 일시
- 동일 문서 재업로드 시 덮어쓰기 처리

### 3. 키워드 검색

- 검색창에 단어 입력 → 해당 단어가 포함된 조문 목록 표시
- 검색 결과 항목 구성:
  - 문서명 + 분류 태그
  - 조문 번호 + 조문 제목
  - 조문 전문 (검색어 하이라이트 처리)
  - 해당 페이지 번호
- 문서 분류별 필터 (체크박스)
- 검색 결과 없을 시 명확한 안내 메시지

### 4. 문서 관리

- 등록된 문서 목록 조회
- 문서 삭제 (해당 문서의 모든 조문 인덱스 함께 삭제)
- 문서별 업로드 일시 및 조문 수 표시

---

## 기술 스택 상세

### 필수 라이브러리

```
streamlit
pdfplumber
sqlite3 (Python 내장)
re (Python 내장)
```

### DB 스키마

```sql
-- 문서 테이블
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_name TEXT NOT NULL,
    doc_category TEXT NOT NULL,  -- '법령', '모범규준', '사규', '감독규정'
    filename TEXT NOT NULL,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    article_count INTEGER DEFAULT 0
);

-- 조문 테이블
CREATE TABLE articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    article_number TEXT,       -- '제3조'
    article_title TEXT,        -- '순자본비율의 산출' (없으면 NULL)
    article_text TEXT NOT NULL, -- 조문 전문
    page_number INTEGER
);
```

### 조문 파싱 로직

```python
import re

# 조문 구분 패턴
ARTICLE_PATTERN = re.compile(r'제\s*\d+조(?:의\d+)?')

# 조문 제목 패턴 (괄호 안)
TITLE_PATTERN = re.compile(r'제\s*\d+조(?:의\d+)?\s*[（(]([^）)]+)[）)]')
```

---

## 화면 구성

### 사이드바

- 메뉴 선택: [🔍 검색] / [📁 문서 관리] / [⬆️ 문서 업로드]

### 검색 화면 (메인)

```
[검색어 입력창                    ] [검색 버튼]

필터: □ 법령  □ 모범규준  □ 사규  □ 감독규정

검색 결과 N건

┌────────────────────────────────────────┐
│ 📄 NCR관리규정  [사규]                  │
│ 제3조 (순자본비율의 산출)               │
│ 순자본비율은 영업용순자본을 총위험액으로 │
│ 나누어 산출한다. **순자본비율**이 100%  │
│ 미만인 경우...                          │
│                                  p.5   │
└────────────────────────────────────────┘
```

### 문서 업로드 화면

```
문서명: [_________________________]
분류:   ○ 법령  ○ 모범규준  ○ 사규  ○ 감독규정
파일:   [파일 선택 버튼]

[업로드 및 인덱싱 시작]

→ 완료: "NCR관리규정.pdf" 인식 완료 (총 47개 조문)
```

### 문서 관리 화면

| 문서명 | 분류 | 조문 수 | 업로드일 | 삭제 |
|--------|------|---------|---------|------|
| NCR관리규정 | 사규 | 47 | 2026-02-20 | [삭제] |

---

## 구현 순서 (Claude Code 작업 순서)

1. `app.py` — Streamlit 메인 앱, 사이드바 메뉴 라우팅
2. `db.py` — SQLite 초기화, CRUD 함수
3. `parser.py` — PDF 텍스트 추출 및 조문 파싱 로직
4. `search.py` — 키워드 검색, 필터링, 하이라이트
5. `pages/upload.py` — 업로드 UI
6. `pages/manage.py` — 문서 관리 UI
7. `pages/search.py` — 검색 결과 UI
8. `requirements.txt` — 의존성 목록

---

## 비기능 요구사항

- 사내 서버에서 `streamlit run app.py --server.port 8501` 명령으로 구동
- 외부 인터넷 연결 없이 완전 로컬 동작 (외부 API 호출 없음)
- PDF 파싱 실패 시 에러 메시지 표시 (앱 크래시 없음)
- 검색 응답 속도: SQLite FTS(Full-Text Search) 또는 LIKE 쿼리 기준 1초 이내

---

## 제외 범위 (v1.0)

- HWP, Word 문서 지원 (추후 확장)
- 사용자 권한 관리 / 로그인
- 의미 기반 검색 (벡터 유사도)
- 조문 간 상호 참조 링크

---

## 디렉토리 구조

```
regulation_search/
├── app.py
├── db.py
├── parser.py
├── search.py
├── pages/
│   ├── upload.py
│   ├── manage.py
│   └── search_page.py
├── data/
│   └── regulations.db
├── requirements.txt
└── README.md
```
