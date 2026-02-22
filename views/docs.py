import os
import io

import streamlit as st

from db import (
    upsert_document, insert_articles, update_article_count,
    get_all_documents, delete_document,
)
from parser import parse_pdf, extract_enacted_date

CATEGORIES = ["법령", "모범규준", "사규", "감독규정"]
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "uploads")

# 모노톤 배지 색상
CATEGORY_COLORS = {
    "법령":    "#1e40af",
    "모범규준": "#0369a1",
    "사규":    "#0891b2",
    "감독규정": "#6366f1",
}


def render():
    st.markdown(
        '<p style="font-size:0.85rem;font-weight:600;color:#0f2744;margin:0 0 14px;">'
        '문서 관리</p>',
        unsafe_allow_html=True,
    )

    tab_upload, tab_list = st.tabs(["규정 업로드", "등록된 규정"])

    # ── 업로드 섹션 ────────────────────────────────────────────────────────
    with tab_upload:
        st.markdown(
            '<p style="font-size:0.85rem;color:#888;margin-bottom:16px;">'
            'PDF 파일을 업로드하면 조문 단위로 파싱하여 저장합니다.</p>',
            unsafe_allow_html=True,
        )
        with st.form("upload_form", clear_on_submit=True):
            col_name, col_cat = st.columns([3, 2])
            with col_name:
                doc_name = st.text_input("문서명", placeholder="예: NCR관리규정")
            with col_cat:
                doc_category = st.selectbox("분류", CATEGORIES)

            uploaded_file = st.file_uploader("PDF 파일", type=["pdf"])
            submitted = st.form_submit_button("업로드 및 인덱싱", type="primary")

        if submitted:
            if not doc_name.strip():
                st.error("문서명을 입력해주세요.")
            elif uploaded_file is None:
                st.error("PDF 파일을 선택해주세요.")
            else:
                with st.spinner("PDF 파싱 중..."):
                    try:
                        pdf_bytes = io.BytesIO(uploaded_file.read())
                        articles = parse_pdf(pdf_bytes)
                        enacted_date = extract_enacted_date(pdf_bytes)
                    except ValueError as e:
                        st.error(f"오류: {e}")
                        st.stop()

                if not articles:
                    st.warning("조문을 인식하지 못했습니다. 텍스트 레이어가 없거나 조문 형식이 다를 수 있습니다.")
                else:
                    with st.spinner("저장 중..."):
                        os.makedirs(UPLOAD_DIR, exist_ok=True)
                        save_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
                        pdf_bytes.seek(0)
                        with open(save_path, "wb") as f:
                            f.write(pdf_bytes.read())

                        doc_id = upsert_document(
                            doc_name.strip(), doc_category, uploaded_file.name, enacted_date
                        )
                        insert_articles(doc_id, articles)
                        update_article_count(doc_id, len(articles))

                    st.success(f'"{doc_name}" 업로드 완료 — {len(articles)}개 조문 인식')
                    st.rerun()

    # ── 등록 문서 목록 ────────────────────────────────────────────────────
    with tab_list:
        docs = get_all_documents()
        if not docs:
            st.markdown(
                '<p style="font-size:0.85rem;color:#999;">등록된 문서가 없습니다.</p>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<p style="font-size:0.8rem;color:#999;margin-bottom:12px;">'
                f'총 {len(docs)}개 문서</p>',
                unsafe_allow_html=True,
            )

            # HTML 테이블
            rows_html = ""
            for i, doc in enumerate(docs):
                color = CATEGORY_COLORS.get(doc["doc_category"], "#666")
                badge = (
                    f'<span style="background:{color};color:#fff;'
                    f'padding:2px 8px;border-radius:3px;font-size:0.72rem;'
                    f'font-weight:500;letter-spacing:0.02em;white-space:nowrap;">'
                    f'{doc["doc_category"]}</span>'
                )
                enacted  = doc.get("enacted_date") or "—"
                uploaded = doc["uploaded_at"][:10] if doc["uploaded_at"] else "—"
                bg = "#fff" if i % 2 == 0 else "#fafafa"

                rows_html += (
                    f'<tr style="background:{bg};">'
                    f'<td style="padding:10px 14px;font-size:0.85rem;font-weight:600;color:#1a1a1a;">'
                    f'{doc["doc_name"]}</td>'
                    f'<td style="padding:10px 14px;text-align:center;">{badge}</td>'
                    f'<td style="padding:10px 14px;text-align:center;font-size:0.82rem;color:#555;">'
                    f'{doc["article_count"]}</td>'
                    f'<td style="padding:10px 14px;text-align:center;font-size:0.82rem;color:#555;">'
                    f'{enacted}</td>'
                    f'<td style="padding:10px 14px;text-align:center;font-size:0.82rem;color:#999;">'
                    f'{uploaded}</td>'
                    f'</tr>'
                )

            table_html = f"""
            <style>
                .reg-table {{
                    width: 100%;
                    border-collapse: collapse;
                    border: 1px solid #dde9ff;
                    border-radius: 6px;
                    overflow: hidden;
                    font-family: inherit;
                }}
                .reg-table th {{
                    background: #0f2744;
                    color: #fff;
                    padding: 10px 14px;
                    font-size: 0.78rem;
                    font-weight: 600;
                    letter-spacing: 0.04em;
                    text-align: center;
                }}
                .reg-table th:first-child {{ text-align: left; }}
                .reg-table td {{ border-top: 1px solid #e0e7ff; }}
                .reg-table tr:hover td {{ background: #f0f6ff !important; }}
            </style>
            <table class="reg-table">
                <thead>
                    <tr>
                        <th style="width:36%;">문서명</th>
                        <th style="width:13%;">분류</th>
                        <th style="width:9%;">조문 수</th>
                        <th style="width:16%;">시행일</th>
                        <th style="width:16%;">업로드일</th>
                    </tr>
                </thead>
                <tbody>{rows_html}</tbody>
            </table>
            """
            st.markdown(table_html, unsafe_allow_html=True)

            # 삭제 섹션
            st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
            with st.expander("문서 삭제"):
                doc_options = {
                    f"{d['doc_name']}  [{d['doc_category']}]": d["id"] for d in docs
                }
                selected = st.selectbox(
                    "삭제할 문서", list(doc_options.keys()), label_visibility="collapsed"
                )
                if st.button("삭제", type="primary"):
                    st.session_state["confirm_del_id"]   = doc_options[selected]
                    st.session_state["confirm_del_name"] = selected

            if "confirm_del_id" in st.session_state:
                st.warning(f'"{st.session_state["confirm_del_name"]}" 를 삭제하시겠습니까?')
                c1, c2, _ = st.columns([1, 1, 6])
                with c1:
                    if st.button("확인", type="primary"):
                        delete_document(st.session_state["confirm_del_id"])
                        st.session_state.pop("confirm_del_id", None)
                        st.session_state.pop("confirm_del_name", None)
                        st.rerun()
                with c2:
                    if st.button("취소"):
                        st.session_state.pop("confirm_del_id", None)
                        st.session_state.pop("confirm_del_name", None)
                        st.rerun()
