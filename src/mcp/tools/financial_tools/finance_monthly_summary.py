from __future__ import annotations

from datetime import date
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from typing_extensions import Annotated

from src.mcp.request_context import get_request_context
from src.data.supaBase.supabase_financial_db import SupaBaseFinanceDB


class Args(BaseModel):
    year: Annotated[int, Field(ge=2000, le=2100, description="Ano (ex: 2026).")]
    month: Annotated[int, Field(ge=1, le=12, description="Mês (1-12).")]


async def _run(year: int, month: int) -> Dict[str, Any]:
    user_id = get_request_context().user_id
    return SupaBaseFinanceDB.get_monthly_summary(user_id=user_id, year=year, month=month)


TOOL = StructuredTool.from_function(
    name="finance_monthly_summary",
    description=(
        "Retorna resumo financeiro de um mês: total de receitas, despesas, "
        "saldo do período e breakdown por categoria. "
        "Informe year e month (ex: year=2026, month=2)."
    ),
    args_schema=Args,
    coroutine=_run,
)