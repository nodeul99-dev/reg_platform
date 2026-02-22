# DS투자증권 규정 검색 플랫폼 — 프로젝트 메모리

## 실행 방법
```bash
cd C:\Users\opus6\Desktop\VibeCoding\reg_platform\regulation_search
streamlit run app.py
```
접속: http://localhost:8501

## 프로젝트 구조
```
regulation_search/
├── app.py                   # 진입점, 전역 CSS, 상단바, 라우팅
├── db.py                    # SQLite (documents + articles 테이블)
├── parser.py                # PDF → 조문 파싱, 시행일 추출
├── search.py                # 검색 로직, highlight_text, category_badge
├── highlighter.py           # pymupdf로 키워드 하이라이트 PDF 생성 (캐시)
├── views/
│   ├── search_page.py       # 검색 UI (히스토리, 필터, 카드, 페이지네이션)
│   └── docs.py              # 문서 관리 (업로드 + 등록 목록, 삭제)
├── static/
│   ├── uploads/             # 업로드된 원본 PDF
│   └── highlighted/         # 하이라이트 처리된 PDF 캐시
├── data/regulations.db
└── .streamlit/config.toml
```

## 현재 색상 팔레트 (파란색 테마)
- 상단바: `#0f2744` (딥 네이비)
- 버튼(primary): `#2563eb` (블루)
- 카테고리 뱃지: 법령 `#1e40af` / 모범규준 `#0369a1` / 사규 `#0891b2` / 감독규정 `#6366f1`
- 카드 테두리: `#dde9ff` / 호버: `#93c5fd`
- Streamlit 테마 primaryColor: `#2563eb`, textColor: `#0f2744`

## 주요 기능
- 키워드 검색 → 조문 카드 표시 (카테고리 필터, 페이지네이션)
- 검색 히스토리 (최근 6개, 클릭 시 재검색 — URL 파라미터 방식)
- 카드 클릭 → pymupdf 하이라이트 PDF 새 탭 오픈
- 문서 업로드 (PDF → 조문 파싱 → DB 저장)
- 문서 목록/삭제 (등록된 규정 탭)

## 네비게이션 방식
- URL 쿼리 파라미터: `?page=search` / `?page=docs`
- 사이드바 없음 (CSS로 숨김)
- 상단바 우측 링크로 페이지 전환

## 주요 설계 결정
- Streamlit `pages/` 폴더 미사용 → `views/` 폴더로 수동 라우팅 (Streamlit 자동 네비 방지)
- 하이라이트 PDF는 `static/highlighted/`에 `{doc_id}_{keyword_hash}.pdf`로 캐시
- 검색 히스토리: session_state 저장, URL param(`hist_kw`)으로 클릭 처리
- TOC 필터링: `_is_toc_entry()`로 목차 조문 제외

## 의존성
- streamlit, pdfplumber, pymupdf(fitz), sqlite3 (내장)
- `py -m pip install` 방식 사용 (pip 직접 실행 안 됨)
