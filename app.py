import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st

from db import init_db
from views import search_page, docs

st.set_page_config(
    page_title="DS투자증권 리스크관리팀 규정검색",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

init_db()

# ── 전역 CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
section[data-testid="stSidebar"],
div[data-testid="collapsedControl"] { display: none !important; }
header[data-testid="stHeader"]      { display: none !important; }

.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
    max-width: 1100px;
    margin-left: auto !important;
    margin-right: auto !important;
}
div.stButton > button[kind="primary"] {
    background: #2563eb; color: #fff;
    border: none; border-radius: 4px;
}
div.stButton > button[kind="primary"]:hover { background: #1d4ed8; }
div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    border-bottom: 2px solid #2563eb !important;
    color: #2563eb !important; font-weight: 600;
}
hr { border-color: #e0e7ff !important; }
</style>
""", unsafe_allow_html=True)

# ── 현재 페이지 판단 (URL 파라미터) ──────────────────────────────────────
page = st.query_params.get("page", "search")
is_search = (page != "docs")

# ── 상단바 (순수 HTML + 네비 링크) ───────────────────────────────────────
nav_href  = "/?page=search" if not is_search else "/?page=docs"
nav_label = "검색으로" if not is_search else "문서관리"

st.markdown(
    f"""
    <div style="
        background:#0f2744;border-radius:6px;
        padding:18px 24px;margin-bottom:20px;
        display:flex;align-items:center;justify-content:space-between;
    ">
        <div>
            <span style="font-size:1.4rem;font-weight:700;color:#fff;letter-spacing:0.01em;">
                DS투자증권 규정 검색 플랫폼
            </span>
            <span style="
                font-size:0.58rem;font-weight:700;color:#fff;
                background:#3b82f6;padding:2px 7px;border-radius:3px;
                letter-spacing:0.07em;margin-left:10px;vertical-align:middle;
            ">BETA</span>
        </div>
        <a href="{nav_href}" target="_self" style="
            font-size:0.65rem;color:#93c5fd;
            border:1px solid #93c5fd;border-radius:3px;
            padding:3px 10px;text-decoration:none;
        "
        onmouseover="this.style.color='#fff';this.style.borderColor='#fff';"
        onmouseout="this.style.color='#93c5fd';this.style.borderColor='#93c5fd';">
            {nav_label}
        </a>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── 라우팅 ───────────────────────────────────────────────────────────────
if is_search:
    search_page.render()
else:
    docs.render()
