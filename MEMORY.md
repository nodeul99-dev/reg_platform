# DS투자증권 규정 검색 플랫폼 — 프로젝트 메모리

## 실행 방법
```bash
cd C:\Users\홍승원\reg_platform
py -m streamlit run app.py
```
접속: http://localhost:8501

## 프로젝트 구조
```
reg_platform/
├── app.py                   # 진입점, 전역 CSS, 상단바, 라우팅
├── db.py                    # SQLite (documents + articles 테이블)
├── parser.py                # PDF → 조문 파싱, 시행일 추출
├── search.py                # 검색 로직, highlight_text, category_badge
├── highlighter.py           # pymupdf로 키워드 하이라이트 PDF 생성 (캐시)
├── law_api.py               # 법제처 오픈API 호출, XML 파싱 (v2 신규)
├── views/
│   ├── search_page.py       # 검색 UI (히스토리, 필터, 카드, 페이지네이션)
│   └── docs.py              # 문서 관리 (업로드 + 등록 목록, API 업데이트 버튼)
├── static/
│   ├── uploads/             # 업로드된 원본 PDF
│   └── highlighted/         # 하이라이트 처리된 PDF 캐시
├── data/regulations.db
├── .env                     # API 키 (Git 제외) ← 직접 생성 필요
├── .env.example             # 환경변수 템플릿
└── PRDv2.md                 # v2.0 기획서
```

## 현재 색상 팔레트 (파란색 테마)
- 상단바: `#0f2744` (딥 네이비)
- 버튼(primary): `#2563eb` (블루)
- 카테고리 뱃지: 법령 `#1e40af` / 모범규준 `#0369a1` / 사규 `#0891b2` / 감독규정 `#6366f1`
- 카드 테두리: `#dde9ff` / 호버: `#93c5fd`
- 소스 배지: API `#0f766e` / PDF `#6b7280`

## 주요 기능 (v2.0 현재)
- 키워드 검색 → 조문 카드 표시 (카테고리 필터, 페이지네이션)
- 검색 히스토리 (최근 6개, URL 파라미터 방식)
- 카드: 소스 배지(API/PDF), 시행일자 표시
- PDF 문서: 카드 클릭 → pymupdf 하이라이트 PDF 새 탭 오픈
- API 문서: PDF 링크 없음 (조문 텍스트만 표시)
- 문서 업로드 (사규·모범규준 전용, PDF → 파싱 → DB)
- 전체 법령 업데이트 버튼 (법제처 API → 자동 수신)
- 개별 법령 업데이트 버튼 (API 문서만)
- 문서 목록/삭제

## 네비게이션
- URL 쿼리 파라미터: `?page=search` / `?page=docs`
- 사이드바 없음 (CSS로 숨김)
- 상단바 우측 링크로 페이지 전환
- Streamlit `pages/` 폴더 미사용 → `views/` 폴더로 수동 라우팅

## DB 스키마 (현재)
```sql
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_name TEXT NOT NULL,
    doc_category TEXT NOT NULL,   -- '법령', '모범규준', '사규', '감독규정'
    filename TEXT NOT NULL,       -- API 문서는 빈 문자열 ''
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    article_count INTEGER DEFAULT 0,
    enacted_date TEXT,            -- 시행일자
    source_type TEXT DEFAULT 'pdf'  -- 'api' | 'pdf'  ← v2 추가
);

CREATE TABLE articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    article_number TEXT,
    article_title TEXT,
    article_text TEXT NOT NULL,
    page_number INTEGER            -- API 문서는 NULL
);
```

## 법제처 API (law_api.py)
```
# 법령 (법률/시행령)
GET https://open.law.go.kr/LSO/openApi/getMOLSLaw.do
  ?OC={API_KEY}&target=law&type=XML&query={법령명}

# 행정규칙 (고시/감독규정)
GET https://open.law.go.kr/LSO/openApi/getMOLSAdmRul.do
  ?OC={API_KEY}&target=admrul&type=XML&query={행정규칙명}
```
- API 키: `.env` 파일에 `LAW_API_KEY=키값` 형태로 저장
- 자동 수신 대상: 자본시장법, 자본시장법 시행령, 금융투자업규정, 금융투자업 감독규정

## 남은 작업
- [ ] API 키 발급 후 실제 수신 테스트 (open.law.go.kr 회원가입 → 오픈API 신청)
- [ ] XML 응답 실제 태그 확인 후 law_api.py 파싱 로직 보정 가능성 있음
- [ ] static/uploads/ 의 기존 PDF가 DRM 손상 파일임 → 정상 PDF로 교체 필요

## 알려진 이슈
- `static/uploads/자본시장과 금융투자업에 관한 법률...pdf` 파일이 손상(DRM)되어
  pymupdf로 열리지 않음. DB에는 조문 데이터가 있으나 PDF 하이라이트 기능 불가.
  → 법제처 API로 수신하면 해당 PDF 없이도 검색 가능 (source_type='api')

## 의존성 설치
```bash
py -m pip install streamlit pdfplumber pymupdf requests python-dotenv
```
※ `py -m pip` 방식 사용 (pip 직접 실행 안 됨)
