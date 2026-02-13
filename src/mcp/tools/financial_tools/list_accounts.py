from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool

from src.mcp.request_context import get_request_context
from src.data.supaBase.supabase_financial_db import SupaBaseFinanceDB


class Args(BaseModel):
    include_closed: bool = Field(
        False, description="Se true, inclui contas com status 'closed'. Padrão: apenas ativas."
    )


async def _run(include_closed: bool = False) -> List[Dict[str, Any]]:
    user_id = get_request_context().user_id
    return SupaBaseFinanceDB.list_accounts(user_id=user_id, include_closed=include_closed)


TOOL = StructuredTool.from_function(
    name="finance_list_accounts",
    description=(
        "Lista todas as contas bancárias do usuário (nome, tipo, moeda, status). "
        "Por padrão retorna apenas contas ativas."
    ),
    args_schema=Args,
    coroutine=_run,
)