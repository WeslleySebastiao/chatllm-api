# supaBase_memory_db.py
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

class SupaBaseMemoryDB:

    @staticmethod
    def _get_conn():
        return psycopg2.connect(
            user=os.getenv("SUPABASE_DB_USER"),
            password=os.getenv("SUPABASE_DB_PASSWORD"),
            host=os.getenv("SUPABASE_DB_HOST"),
            port=os.getenv("SUPABASE_DB_PORT"),
            dbname=os.getenv("SUPABASE_DB_NAME"),
            sslmode="require",
        )

    @staticmethod
    def get_or_create_session(user_id: str, agent_id: str, session_id: str | None = None) -> str:
        conn = SupaBaseMemoryDB._get_conn()
        cur = conn.cursor()

        try:
            if session_id:
                cur.execute(
                    "select id from public.chat_sessions where id=%s and user_id=%s and agent_id=%s;",
                    (session_id, user_id, agent_id),
                )
                if cur.fetchone():
                    return session_id

            cur.execute(
                """
                insert into public.chat_sessions (user_id, agent_id)
                values (%s, %s)
                returning id;
                """,
                (user_id, agent_id),
            )
            new_id = cur.fetchone()[0]
            conn.commit()
            return str(new_id)
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def save_message(session_id: str, role: str, content: str):
        conn = SupaBaseMemoryDB._get_conn()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                insert into public.chat_messages (session_id, role, content)
                values (%s, %s, %s);
                """,
                (session_id, role, content),
            )
            conn.commit()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def load_history(session_id: str, limit: int = 20):
        conn = SupaBaseMemoryDB._get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute(
                """
                select role, content
                from public.chat_messages
                where session_id=%s
                order by created_at desc
                limit %s;
                """,
                (session_id, limit),
            )
            rows = cur.fetchall()
            return list(reversed(rows))  # cronológico
        finally:
            cur.close()
            conn.close()
