import streamlit as st

from db import get_all_documents, delete_document

CATEGORY_COLORS = {
    "법령": "#1565C0",
    "모범규준": "#2E7D32",
    "사규": "#6A1B9A",
    "감독규정": "#B71C1C",
}


def render():
    st.title("📁 문서 관리")
    st.markdown("등록된 문서를 확인하고 삭제할 수 있습니다.")

    docs = get_all_documents()

    if not docs:
        st.info("등록된 문서가 없습니다. 먼저 문서를 업로드해주세요.")
        return

    st.markdown(f"**총 {len(docs)}개** 문서 등록됨")
    st.divider()

    for doc in docs:
        col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 2, 1])

        with col1:
            st.markdown(f"**{doc['doc_name']}**")
        with col2:
            color = CATEGORY_COLORS.get(doc["doc_category"], "#555")
            st.markdown(
                f'<span style="background:{color};color:white;'
                f'padding:2px 10px;border-radius:10px;font-size:0.8rem;">'
                f'{doc["doc_category"]}</span>',
                unsafe_allow_html=True,
            )
        with col3:
            st.markdown(f'{doc["article_count"]}조문')
        with col4:
            uploaded = doc["uploaded_at"][:10] if doc["uploaded_at"] else "-"
            st.caption(uploaded)
        with col5:
            if st.button("삭제", key=f"del_{doc['id']}", type="secondary"):
                st.session_state[f"confirm_del_{doc['id']}"] = True

        # 삭제 확인
        if st.session_state.get(f"confirm_del_{doc['id']}"):
            st.warning(
                f'**"{doc["doc_name"]}"** 문서와 모든 조문을 삭제합니다. 계속하시겠습니까?'
            )
            c1, c2, _ = st.columns([1, 1, 4])
            with c1:
                if st.button("확인 삭제", key=f"do_del_{doc['id']}", type="primary"):
                    delete_document(doc["id"])
                    st.session_state.pop(f"confirm_del_{doc['id']}", None)
                    st.success(f'"{doc["doc_name"]}" 삭제 완료')
                    st.rerun()
            with c2:
                if st.button("취소", key=f"cancel_del_{doc['id']}"):
                    st.session_state.pop(f"confirm_del_{doc['id']}", None)
                    st.rerun()

        st.divider()
