from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool

from src.mcp.request_context import get_request_context
from src.data.supaBase.supabase_financial_db import SupaBaseFinanceDB


class Args(BaseModel):
    include_closed: bool = Field(
        False, description="Se true, inclui cartões com status 'closed'. Padrão: apenas ativos."
    )


async def _run(include_closed: bool = False) -> List[Dict[str, Any]]:
    user_id = get_request_context().user_id
    return SupaBaseFinanceDB.list_cards(user_id=user_id, include_closed=include_closed)


TOOL = StructuredTool.from_function(
    name="finance_list_cards",
    description=(
        "Lista todos os cartões de crédito do usuário (nome, bandeira, limite, "
        "dia de fechamento, dia de vencimento, status). "
        "Por padrão retorna apenas cartões ativos."
    ),
    args_schema=Args,
    coroutine=_run,
)