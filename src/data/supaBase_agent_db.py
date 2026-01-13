# supaBase_agent_db.py
import os
import json
from typing import Any, Dict, List, Optional
from uuid import UUID

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from src.core.config import settings

load_dotenv()

class SupaBaseAgentDB:
    """
    CRUD de configurações de agentes no Supabase/Postgres.
    Usa Pooler (transaction mode) recomendado no seu cenário.
    """

    @staticmethod
    def _get_conn():
        return psycopg2.connect(
            user=settings.SUPABASE_DB_USER,
            password=settings.SUPABASE_DB_PASSWORD,
            host=settings.SUPABASE_DB_HOST,
            port=settings.SUPABASE_DB_PORT,
            dbname=settings.SUPABASE_DB_NAME,
            sslmode="require",
        )

    @staticmethod
    def create_agent(
        name: str,
        description: Optional[str],
        provider: str,
        model: str,
        tools: List[str],
        prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> Dict[str, Any]:
        conn = SupaBaseAgentDB._get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute(
                """
                insert into public.agents
                    (name, description, provider, model, tools, prompt, temperature, max_tokens)
                values
                    (%s, %s, %s, %s, %s::jsonb, %s, %s, %s)
                returning
                    id, name, description, provider, model, tools, prompt, temperature, max_tokens,
                    created_at, updated_at;
                """,
                (name, description, provider, model, json.dumps(tools), prompt, temperature, max_tokens),
            )
            row = cur.fetchone()
            conn.commit()
            return row
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def list_agents() -> List[Dict[str, Any]]:
        conn = SupaBaseAgentDB._get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute(
                """
                select
                    id, name, description, provider, model, tools, prompt, temperature, max_tokens,
                    created_at, updated_at
                from public.agents
                order by created_at desc;
                """
            )
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_agent(agent_id: str | UUID) -> Optional[Dict[str, Any]]:
        connection = SupaBaseAgentDB._get_conn()
        cur = connection.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute(
                """
                select
                    id, name, description, provider, model, tools, prompt, temperature, max_tokens,
                    created_at, updated_at
                from public.agents
                where id = %s;
                """,
                (str(agent_id),),
            )
            return cur.fetchone()
        finally:
            cur.close()
            connection.close()

    @staticmethod
    def update_agent(agent_id: str | UUID, patch: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Atualização parcial. Ex.: patch={"prompt": "...", "temperature": 0.2, "tools": ["x"]}
        """
        allowed = {"name", "description", "provider", "model", "prompt", "temperature", "max_tokens", "tools"}
        sets = []
        values = []

        for k, v in patch.items():
            if k not in allowed:
                continue
            if k == "tools":
                sets.append("tools = %s::jsonb")
                values.append(json.dumps(v))
            else:
                sets.append(f"{k} = %s")
                values.append(v)

        if not sets:
            return SupaBaseAgentDB.get_agent(agent_id)

        conn = SupaBaseAgentDB._get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            values.append(str(agent_id))
            cur.execute(
                f"""
                update public.agents
                set {", ".join(sets)}
                where id = %s
                returning
                    id, name, description, provider, model, tools, prompt, temperature, max_tokens,
                    created_at, updated_at;
                """,
                tuple(values),
            )
            row = cur.fetchone()
            conn.commit()
            return row
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def delete_agent(agent_id: str | UUID) -> bool:
        conn = SupaBaseAgentDB._get_conn()
        cur = conn.cursor()
        try:
            cur.execute("delete from public.agents where id = %s;", (str(agent_id),))
            deleted = cur.rowcount > 0
            conn.commit()
            return deleted
        finally:
            cur.close()
            conn.close()
