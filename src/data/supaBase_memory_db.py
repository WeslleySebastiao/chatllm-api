import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from src.core.config import settings
import os

load_dotenv()

def get_conn():
    return psycopg2.connect(
        user=settings.SUPABASE_DB_USER,
        password=settings.SUPABASE_DB_PASSWORD,
        host=settings.SUPABASE_DB_HOST,
        port=settings.SUPABASE_DB_PORT,
        dbname=settings.SUPABASE_DB_NAME,
        sslmode="require",
    )

def get_or_create_session(user_id: str, session_id: str | None = None) -> str:
    conn = get_conn()
    cur = conn.cursor()

    if session_id:
        cur.execute("select id from public.chat_sessions where id = %s;", (session_id,))
        row = cur.fetchone()
        if row:
            cur.close(); conn.close()
            return session_id

    cur.execute(
        "insert into public.chat_sessions (user_id) values (%s) returning id;",
        (user_id,)
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close(); conn.close()
    return str(new_id)

def save_message(session_id: str, role: str, content: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        insert into public.chat_messages (session_id, role, content)
        values (%s, %s, %s);
        """,
        (session_id, role, content)
    )
    conn.commit()
    cur.close(); conn.close()

def load_history(session_id: str, limit: int = 20):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """
        select role, content, created_at
        from public.chat_messages
        where session_id = %s
        order by created_at desc
        limit %s;
        """,
        (session_id, limit)
    )
    rows = cur.fetchall()
    cur.close(); conn.close()

    # retorna em ordem cronológica
    return list(reversed(rows))
