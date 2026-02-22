import os
import streamlit as st
import io

from db import upsert_document, insert_articles, update_article_count
from parser import parse_pdf

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "uploads")

CATEGORIES = ["법령", "모범규준", "사규", "감독규정"]


def render():
    st.title("⬆️ 문서 업로드")
    st.markdown("PDF 파일을 업로드하면 조문 단위로 파싱하여 DB에 저장합니다.")

    with st.form("upload_form", clear_on_submit=True):
        doc_name = st.text_input(
            "문서명",
            placeholder="예: NCR관리규정",
            help="DB에 저장될 문서의 이름을 입력하세요.",
        )
        doc_category = st.radio(
            "분류",
            CATEGORIES,
            horizontal=True,
        )
        uploaded_file = st.file_uploader(
            "PDF 파일 선택",
            type=["pdf"],
            help="한 번에 하나의 PDF 파일을 업로드할 수 있습니다.",
        )
        submitted = st.form_submit_button("업로드 및 인덱싱 시작", type="primary")

    if submitted:
        if not doc_name.strip():
            st.error("문서명을 입력해주세요.")
            return
        if uploaded_file is None:
            st.error("PDF 파일을 선택해주세요.")
            return

        with st.spinner("PDF 파싱 중..."):
            try:
                pdf_bytes = io.BytesIO(uploaded_file.read())
                articles = parse_pdf(pdf_bytes)
            except ValueError as e:
                st.error(f"❌ {e}")
                return

        if not articles:
            st.warning(
                "조문을 인식하지 못했습니다. "
                "PDF 텍스트 레이어가 없거나 조문 형식이 다를 수 있습니다."
            )
            return

        with st.spinner("DB 저장 중..."):
            # PDF 원본 파일 저장
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            save_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
            pdf_bytes.seek(0)
            with open(save_path, "wb") as f:
                f.write(pdf_bytes.read())

            doc_id = upsert_document(
                doc_name.strip(), doc_category, uploaded_file.name
            )
            insert_articles(doc_id, articles)
            update_article_count(doc_id, len(articles))

        st.success(
            f'✅ **"{doc_name}"** 인식 완료 — 총 **{len(articles)}개** 조문이 저장되었습니다.'
        )

        with st.expander("인식된 조문 미리보기 (처음 10개)"):
            for a in articles[:10]:
                title_str = f" ({a['article_title']})" if a["article_title"] else ""
                st.markdown(
                    f"**{a['article_number']}{title_str}** — p.{a['page_number']}"
                )
                preview = a["article_text"][:200]
                if len(a["article_text"]) > 200:
                    preview += "..."
                st.caption(preview)
                st.divider()
