"""
pymupdf를 사용해 PDF에 키워드 하이라이트를 추가하는 모듈.
동일한 (doc_id, keyword) 조합은 캐시 파일을 재사용하여 중복 생성을 방지.
"""
import os
import hashlib

import fitz  # pymupdf

UPLOAD_DIR      = os.path.join(os.path.dirname(__file__), "static", "uploads")
HIGHLIGHTED_DIR = os.path.join(os.path.dirname(__file__), "static", "highlighted")


def get_highlighted_pdf_url(filename: str, keyword: str, doc_id: int, page_number: int) -> str:
    """
    하이라이트가 적용된 PDF의 static URL을 반환.
    캐시 파일이 있으면 재사용, 없으면 새로 생성.
    """
    os.makedirs(HIGHLIGHTED_DIR, exist_ok=True)

    kw_hash      = hashlib.md5(keyword.encode("utf-8")).hexdigest()[:10]
    out_filename = f"{doc_id}_{kw_hash}.pdf"
    out_path     = os.path.join(HIGHLIGHTED_DIR, out_filename)

    if not os.path.exists(out_path):
        src_path = os.path.join(UPLOAD_DIR, filename)
        if not os.path.exists(src_path):
            # 원본 없으면 원본 URL 반환
            return f"/app/static/uploads/{_quote(filename)}#page={page_number}"
        _generate(src_path, keyword, out_path)

    return f"/app/static/highlighted/{out_filename}#page={page_number}"


def _generate(src_path: str, keyword: str, out_path: str):
    """PDF 전체를 순회하며 키워드를 모두 노란색으로 하이라이트."""
    doc = fitz.open(src_path)
    for page in doc:
        hits = page.search_for(keyword, quads=True)
        for quad in hits:
            annot = page.add_highlight_annot(quad)
            # 노란색 하이라이트
            annot.set_colors(stroke=[1, 1, 0])
            annot.update()
    doc.save(out_path, garbage=4, deflate=True)
    doc.close()


def _quote(s: str) -> str:
    import urllib.parse
    return urllib.parse.quote(s)
