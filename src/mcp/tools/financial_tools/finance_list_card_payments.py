from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from typing_extensions import Annotated

from src.mcp.request_context import get_request_context
from src.data.supaBase.supabase_financial_db import SupaBaseFinanceDB


class Args(BaseModel):
    card_name: Optional[str] = Field(
        None, description="Filtrar por nome do cartão (ex: 'Nubank'). Opcional."
    )

    status: Optional[Literal["pending", "paid"]] = Field(
        None, description="Filtrar por status: pending ou paid. Opcional."
    )

    ref_month_start_from: Optional[date] = Field(
        None, description="Mês inicial do filtro (YYYY-MM-DD)."
    )

    ref_month_start_to: Optional[date] = Field(
        None, description="Mês final do filtro (YYYY-MM-DD)."
    )

    limit: Annotated[int, Field(ge=1, le=100)] = 24
    offset: Annotated[int, Field(ge=0)] = 0


async def _run(
    card_name: Optional[str] = None,
    status: Optional[str] = None,
    ref_month_start_from: Optional[date] = None,
    ref_month_start_to: Optional[date] = None,
    limit: int = 24,
    offset: int = 0,
) -> Dict[str, Any]:
    user_id = get_request_context().user_id

    card_id = None
    if card_name:
        card_id = SupaBaseFinanceDB.resolve_card_id(
            user_id=user_id,
            name=card_name,
            auto_create=False,
        )
        if not card_id:
            return {"error": f"Cartão '{card_name}' não encontrado.", "payments": []}

    rows = SupaBaseFinanceDB.list_card_payments(
        user_id=user_id,
        card_id=card_id,
        status=status,
        ref_month_start_from=ref_month_start_from,
        ref_month_start_to=ref_month_start_to,
        limit=limit,
        offset=offset,
    )

    return {
        "count": len(rows),
        "payments": rows,
    }


TOOL = StructuredTool.from_function(
    name="finance_list_card_payments",
    description=(
        "Lista pagamentos de faturas de cartão. "
        "Filtre por nome do cartão, status (pending/paid) e período. "
        "Útil para ver faturas pendentes ou histórico de pagamentos."
    ),
    args_schema=Args,
    coroutine=_run,
)