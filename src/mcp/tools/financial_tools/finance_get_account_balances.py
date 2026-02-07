from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool

from src.mcp.request_context import get_request_context
from src.data.supaBase.supabase_financial_db import SupaBaseFinanceDB


class Args(BaseModel):
    currency: Optional[str] = Field(None, description="Filtrar por moeda (ex: BRL).")


async def _run(currency: Optional[str] = None) -> List[Dict[str, Any]]:
    user_id = get_request_context().user_id
    rows = SupaBaseFinanceDB.get_account_balances(user_id=user_id)
    if currency:
        rows = [r for r in rows if r.get("currency") == currency]
    return rows


TOOL = StructuredTool.from_function(
    name="finance_get_account_balances",
    description="Retorna saldo por conta (vw_finance_account_balance).",
    args_schema=Args,
    coroutine=_run,
)
