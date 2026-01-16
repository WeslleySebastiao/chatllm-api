# src/db/memory_repo.py
from typing import List, Dict, Any, Optional
from src.data.supaBase_db import DB


class SupaBaseMemoryDB:

    @staticmethod
    def get_or_create_session(user_id: str, agent_id: str, session_id: str | None = None) -> str:
        # Se vier session_id, valida se existe e pertence ao user/agent
        if session_id:
            check_sql = """
            select id from public.chat_sessions
            where id=%s and user_id=%s and agent_id=%s;
            """
            row = DB.fetch_one(check_sql, (session_id, user_id, agent_id))
            if row:
                return session_id

        # Cria nova sessão
        insert_sql = """
        insert into public.chat_sessions (user_id, agent_id)
        values (%s, %s)
        returning id;
        """
        row = DB.fetch_one(insert_sql, (user_id, agent_id))
        return str(row["id"])

    @staticmethod
    def save_message(session_id: str, role: str, content: str) -> None:
        sql = """
        insert into public.chat_messages (session_id, role, content)
        values (%s, %s, %s);
        """
        DB.execute(sql, (session_id, role, content))

    @staticmethod
    def load_history(session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        sql = """
        select role, content
        from public.chat_messages
        where session_id=%s
        order by created_at desc
        limit %s;
        """
        rows = DB.fetch_all(sql, (session_id, limit))
        return list(reversed(rows))  # cronológico
