import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "regulations.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_name TEXT NOT NULL,
                doc_category TEXT NOT NULL,
                filename TEXT NOT NULL,
                uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                article_count INTEGER DEFAULT 0,
                enacted_date TEXT
            );

            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
                article_number TEXT,
                article_title TEXT,
                article_text TEXT NOT NULL,
                page_number INTEGER
            );

            CREATE INDEX IF NOT EXISTS idx_articles_doc_id ON articles(doc_id);
        """)
        # 기존 DB에 컬럼이 없는 경우 마이그레이션
        cols = [r[1] for r in conn.execute("PRAGMA table_info(documents)").fetchall()]
        if "enacted_date" not in cols:
            conn.execute("ALTER TABLE documents ADD COLUMN enacted_date TEXT")
        if "source_type" not in cols:
            conn.execute("ALTER TABLE documents ADD COLUMN source_type TEXT NOT NULL DEFAULT 'pdf'")


# ── 문서 CRUD ──────────────────────────────────────────────────────────────

def upsert_document(
    doc_name: str, doc_category: str, filename: str,
    enacted_date: str | None = None, source_type: str = "pdf",
) -> int:
    """동일 문서명+분류가 있으면 기존 조문 삭제 후 재삽입, 없으면 신규 삽입."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM documents WHERE doc_name = ? AND doc_category = ?",
            (doc_name, doc_category),
        ).fetchone()
        if row:
            doc_id = row["id"]
            conn.execute("DELETE FROM articles WHERE doc_id = ?", (doc_id,))
            conn.execute(
                "UPDATE documents SET filename = ?, uploaded_at = ?, enacted_date = ?, source_type = ? WHERE id = ?",
                (filename, datetime.now().isoformat(), enacted_date, source_type, doc_id),
            )
        else:
            cur = conn.execute(
                "INSERT INTO documents (doc_name, doc_category, filename, enacted_date, source_type) VALUES (?, ?, ?, ?, ?)",
                (doc_name, doc_category, filename, enacted_date, source_type),
            )
            doc_id = cur.lastrowid
    return doc_id


def update_article_count(doc_id: int, count: int):
    with get_conn() as conn:
        conn.execute(
            "UPDATE documents SET article_count = ? WHERE id = ?", (count, doc_id)
        )


def insert_articles(doc_id: int, articles: list[dict]):
    with get_conn() as conn:
        conn.executemany(
            """INSERT INTO articles (doc_id, article_number, article_title, article_text, page_number)
               VALUES (:doc_id, :article_number, :article_title, :article_text, :page_number)""",
            [{"doc_id": doc_id, **a} for a in articles],
        )


def get_all_documents() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM documents ORDER BY uploaded_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def delete_document(doc_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))


def get_document_by_id(doc_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM documents WHERE id = ?", (doc_id,)
        ).fetchone()
    return dict(row) if row else None


def get_articles_by_doc_id(doc_id: int) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM articles WHERE doc_id = ? ORDER BY id", (doc_id,)
        ).fetchall()
    return [dict(r) for r in rows]


# ── 검색 ───────────────────────────────────────────────────────────────────

def search_articles(keyword: str, categories: list[str] | None = None) -> list[dict]:
    if not keyword.strip():
        return []

    placeholders = ""
    params: list = [f"%{keyword}%"]

    if categories:
        ph = ",".join("?" * len(categories))
        placeholders = f" AND d.doc_category IN ({ph})"
        params += categories

    sql = f"""
        SELECT a.id, a.doc_id, a.article_number, a.article_title, a.article_text, a.page_number,
               d.doc_name, d.doc_category, d.filename, d.source_type, d.enacted_date
        FROM articles a
        JOIN documents d ON a.doc_id = d.id
        WHERE a.article_text LIKE ?{placeholders}
        ORDER BY d.doc_name, a.id
    """
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]
