# src/db/runs_repo.py
from typing import Any, Dict, Optional
from psycopg2.extras import Json
from src.data.supaBase_db import DB


class SupaBaseRunsDB:

    @staticmethod
    def insert_run(row: dict) -> None:
        sql = """
        insert into public.runs
            (id, created_at, status, agent_id, agent_version, user_id, session_id, provider, model, metadata)
        values
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb);
        """
        DB.execute(sql, (
            row["id"],
            row["created_at"],
            row["status"],
            row["agent_id"],
            row.get("agent_version"),
            row.get("user_id"),
            row.get("session_id"),
            row.get("provider", "openai"),
            row.get("model"),
            Json(row.get("metadata", {})),   # ✅ aqui
        ))

    @staticmethod
    def update_run(run_id: str, patch: Dict[str, Any]) -> None:
        allowed = {
            "finished_at", "duration_ms", "status", "session_id",
            "provider", "model",
            "prompt_tokens", "completion_tokens", "total_tokens",
            "prompt_tokens_cached", "reasoning_tokens",
            "cost_usd",
            "error_type", "error_message", "error_hash",
            "metadata",
        }

        sets = []
        values = []

        for k, v in patch.items():
            if k not in allowed:
                continue

            if k == "metadata":
                #sempre adaptar dict/list pra JSON
                sets.append("metadata = %s::jsonb")
                values.append(Json(v if v is not None else {}))
            else:
                sets.append(f"{k} = %s")
                values.append(v)

        if not sets:
            return

        sql = f"update public.runs set {', '.join(sets)} where id = %s;"
        values.append(run_id)

        DB.execute(sql, tuple(values))