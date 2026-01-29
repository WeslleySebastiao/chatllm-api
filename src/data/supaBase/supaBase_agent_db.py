import json
from typing import Any, Dict, List, Optional
from uuid import UUID

from src.data.supaBase.supaBase_db import DB


class SupaBaseAgentDB:

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
        sql = """
        insert into public.agents
            (name, description, provider, model, tools, prompt, temperature, max_tokens)
        values
            (%s, %s, %s, %s, %s::jsonb, %s, %s, %s)
        returning
            id, name, description, provider, model, tools, prompt, temperature, max_tokens,
            created_at, updated_at;
        """
        return DB.fetch_one(sql, (name, description, provider, model, json.dumps(tools), prompt, temperature, max_tokens))

    @staticmethod
    def list_agents() -> List[Dict[str, Any]]:
        sql = """
        select
            id, name, description, provider, model, tools, prompt, temperature, max_tokens,
            created_at, updated_at
        from public.agents
        order by created_at desc;
        """
        return DB.fetch_all(sql)

    @staticmethod
    def get_agent(agent_id: str | UUID) -> Optional[Dict[str, Any]]:
        sql = """
        select
            id, name, description, provider, model, tools, prompt, temperature, max_tokens,
            created_at, updated_at
        from public.agents
        where id = %s;
        """
        return DB.fetch_one(sql, (str(agent_id),))

    @staticmethod
    def update_agent(agent_id: str | UUID, patch: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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

        sql = f"""
        update public.agents
        set {", ".join(sets)}
        where id = %s
        returning
            id, name, description, provider, model, tools, prompt, temperature, max_tokens,
            created_at, updated_at;
        """
        values.append(str(agent_id))
        return DB.fetch_one(sql, tuple(values))

    @staticmethod
    def delete_agent(agent_id: str | UUID) -> bool:
        sql = "delete from public.agents where id = %s;"
        rows = DB.execute(sql, (str(agent_id),))
        return rows > 0