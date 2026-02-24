# DS투자증권 규정 검색 플랫폼 — 프로젝트 메모리

## 실행 방법
```bash
cd C:\projects_openclaw\reg_platform\regulation_search
streamlit run app.py
```
접속: http://localhost:8501  
팀원 접속: `streamlit run app.py --server.address 0.0.0.0 --server.port 8501` 후 http://[PC_IP]:8501

---

## 현재 프로젝트 구조 (v2.0 완성)
```
reg_platform/                # 실제 작동 루트
├── app.py                   # 진입점, 전역 CSS, 상단바, URL 라우팅
├── db.py                    # SQLite (documents + articles, source_type, enacted_date)
├── parser.py                # PDF → 조문 파싱, 시행일 추출 (메모리 처리)
├── search.py                # 검색 로직, highlight_text, category_badge
├── crawler.py               # 법제처 오픈API 연동 (crawl_single_law)
├── views/
│   ├── search_page.py       # 검색 UI (히스토리, 필터, 카드, 페이지네이션, 조문 전문 expander)
│   └── docs.py              # 문서 관리 (업로드[모범규준/사규] + 크롤링 업데이트 + 목록)
├── data/regulations.db
└── .streamlit/config.toml
```

---

## v2.0 구조 (완성)
- `crawler.py` 신규 작성 완료 (crawl_single_law, MANAGED_LAWS)
- `views/search_page.py`: PDF 뷰어 제거, st.expander 기반 조문 전문 뷰
- `views/docs.py`: PDF 저장 제거, 업로드 분류 모범규준/사규만, crawler.py 연동
- `highlighter.py` 삭제, `static/uploads/` PDF 삭제 완료

---

## 핵심 설계 결정 (최종 확정)

### 문서 소스 전략
| 분류 | 입력 방식 | 저장 | PDF 보관 |
|------|---------|------|---------|
| 법령 / 감독규정 | 법령정보센터 크롤링 (www.law.go.kr) | 로컬 DB | ❌ 없음 |
| 사규 / 모범규준 | 암호해제 PDF 1회 업로드 → 파싱 후 즉시 삭제 | 로컬 DB | ❌ 없음 |

### PDF 보관 금지 이유
- 회사 PC에서 파일 자동 암호화 정책 적용
- 암호화된 PDF는 pymupdf/pdfplumber가 읽지 못함
- 따라서 시스템 내부에 PDF 파일 일절 보관하지 않음
- 파싱 완료 즉시 원본 PDF 삭제

### PDF 뷰어 폐기 이유
- PDF 파일 미보관으로 뷰어 호출 불가
- highlighter.py, static/ 폴더 전체 제거
- 대체: 카드 클릭 시 DB 텍스트 기반 조문 상세 표시 (확장 카드 또는 모달)

### 크롤링 방식
- 대상: www.law.go.kr (법령정보센터)
- 법령/감독규정: 업데이트 버튼 클릭 시 1회 크롤링 → 로컬 DB 저장
- 버튼 클릭 전까지 DB 변경 없음, 검색은 항상 로컬 DB만 사용

### 네비게이션 (v3 레이아웃으로 변경)
- URL 쿼리 파라미터: `?page=search` / `?page=docs`
- pages/ 폴더 미사용 → views/ 수동 라우팅
- 사이드바 토글: `?page=X&sb_exp={0|1}` URL 파라미터 → session_state["sb_expanded"] 갱신

### 사이드바 (v4 커스텀 fixed div)
- `st.sidebar` 미사용 → `st.markdown(<div style="position:fixed">...)` 으로 직접 렌더링
- 이모지 → 인라인 SVG (Lucide 스타일, stroke="currentColor")
- 아이콘: 쉴드(로고) / 돋보기(검색) / 폴더(문서관리) / 쉐브론(토글)
- 내비게이션: `<a href="/?page=X" target="_self">` — 클릭 시 세션상태 초기화됨 (trade-off 수용)
- 활성 상태: 색상 `#bef264` + `font-weight:700` 만 (배경색 변경 없음)
- 토글 버튼: `flex:1` 스페이서로 사이드바 하단 고정
- 아이콘 배치: 로고 → 구분선 → 내비 아이콘 (상단) → 스페이서 → 토글 (하단)
- **수정 팁**: 사이드바 내부는 fixed div 안의 순수 HTML → padding/margin만 바꾸면 됨

### 레이아웃 구조 (v4)
- **상단바**: `position:fixed; top:8px; left:8px; right:8px; height:68px`
- **사이드바**: `position:fixed; top:84px; left:8px; height:calc(100vh-92px)` (커스텀 div)
  - 축소(68px): 아이콘만 / 확장(154px): 아이콘+메뉴명, 토글 버튼
- **stMain**: `position:fixed; top:84px; left:{sb_total_w}; right:8px; bottom:0; overflow-y:auto`
- **sb_total_w**: 84px(축소=8+68+8) / 170px(확장=8+154+8)
- **block-container**: `padding: 0 0 2rem 0`
- **메인 레이아웃**: `st.columns([2.2, 1.1])` → col_main | col_side
- **보조 패널 컬럼**: `position:sticky; top:0; align-self:flex-start`

### CSS 특이도 주의사항 (Streamlit 1.53.1)
- `section[data-testid="stMain"] > div:first-child` 가 block-container를 직접 타겟 → `padding-top:0`을 절대 쓰면 안 됨 (`.block-container` 규칙을 덮어씀)
- Streamlit Emotion 클래스: `st-emotion-cache-*`, block-container 클래스: `stMainBlockContainer block-container e1td4qo64`
- 레이아웃 디버깅: playwright `bounding_box()` + `getComputedStyle()` 사용

---

## 현재 색상 팔레트 (v4 그린 테마)
- 배경: `#eaf2eb` (소프트 그린)
- 상단바: `#ffffff` (흰색)
- 사이드바: `#0f172a` (딥 다크) ← 변경 없음
- 라임 액센트: `#a3e635` (포인트), `#84cc16` (호버), `#bef264` (다크 bg 위 텍스트)
- 버튼(primary): `#a3e635` bg / `#14532d` text
- 버튼(secondary): `#ffffff` bg / `#a3e635` border / `#14532d` text
- 카드 버튼: `.card-btn` 래퍼 → 별도 CSS (흰 bg, `#d1e8d4` border, 카드 형태)
- 카드 테두리: `#d1e8d4` / 호버: `#a3e635`
- 탭 활성: `#84cc16` 보더 / `#4d7c0f` 텍스트
- 카테고리 뱃지: 법령 `#15803d` / 모범규준 `#047857` / 사규 `#0f766e` / 감독규정 `#4d7c0f`
- 헤딩 텍스트: `#14532d` (다크 그린)
- 히스토리 링크: `#16a34a` / 점선: `#4ade80`
- 테이블 헤더: `#14532d` / 테두리: `#d1e8d4` / hover: `#f0f9f2`
- HR: `#c8dfc9`

---

## 구현 완료 기능 (v2.0)
- 키워드 검색 → 조문 카드 표시 (source_type 배지, 시행일 표시)
- 카테고리 필터 (법령 / 모범규준 / 사규 / 감독규정)
- 페이지네이션 (10/30/50/100건 선택)
- 검색 히스토리 (최근 6개, URL 파라미터 방식)
- 조문 전문 확장 뷰 (st.expander, PDF 뷰어 없음)
- PDF 업로드 (모범규준/사규 전용, 파싱 후 원본 즉시 삭제)
- 법령/감독규정 크롤링 업데이트 (전체/개별, .env LAW_API_KEY 필요)
- 문서 목록 (소스 배지: 크롤링/PDF) / 삭제
- URL 쿼리 파라미터 라우팅 (?page=search / ?page=docs), 사이드바 없음
- 파란색 테마 레이아웃 (딥 네이비 상단바)

---

## 상단바 구조 (v4)
- 로고: `sentinel.DS` (2.1rem, underline) + 바로 오른쪽에 `DS투자증권 리스크관리팀` (0.72rem, flex-end 정렬)
- 메뉴 필: `규정검색 / 재무건전성비율 / 위원회` — 모두 기본 비활성(회색), hover 시 라임 활성
- CSS 클래스: `.menu-pill-inactive` hover → `#f3ffe0` bg / `#4d7c0f` text / `#a3e635` border

## 사이드바 구조 (v4)
- 방패 로고 제거, 아이콘만 (search, docs, chevron)
- stroke-width: 검색/폴더 `3`, 쉐브론 `3.75`
- 링크 CSS 클래스: `.sb-link` — 기본 `#64748b`, hover `#a3e635`
- 구분선 제거, 상단 `padding-top:8px`으로 시작

## 다음 작업
- 없음. 추가 UI 작업 있으면 기록 예정.

---

## 의존성
```
streamlit
pdfplumber
requests          # 크롤러용 (신규)
beautifulsoup4    # 크롤러용 (신규)
sqlite3           # Python 내장
```

설치:
```bash
py -m pip install streamlit pdfplumber requests beautifulsoup4
```

---

## 참고
- 전체 스펙: `PRD_v2.md` 참조
- pymupdf(fitz)는 더 이상 사용하지 않음 (highlighter.py 제거로 불필요)
