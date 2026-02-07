from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel
from typing_extensions import Annotated
from pydantic import Field
from langchain_core.tools import StructuredTool

from src.mcp.request_context import get_request_context
from src.data.supaBase.supabase_financial_db import SupaBaseFinanceDB

class Args(BaseModel):
    card_id: Optional[UUID] = Field(None, description="Filtrar por cartão (opcional).")
    ref_month_start_from: Optional[date] = Field(None, description="ref_month_start >= (YYYY-MM-DD).")
    ref_month_start_to: Optional[date] = Field(None, description="ref_month_start <= (YYYY-MM-DD).")

    # Se informado, retorna detalhe dessa fatura (e opcionalmente itens)
    ref_month_start: Optional[date] = Field(
        None,
        description="Mês de referência da fatura (YYYY-MM-DD, ex: 2026-02-01).",
    )
    include_items: bool = Field(False, description="Se true e ref_month_start informado, inclui itens da fatura.")

    limit: Annotated[int, Field(ge=1, le=200, description="Paginação (lista de faturas).")] = 24
    offset: Annotated[int, Field(ge=0, description="Paginação (lista de faturas).")] = 0


async def _run(
    card_id: Optional[UUID] = None,
    ref_month_start_from: Optional[date] = None,
    ref_month_start_to: Optional[date] = None,
    ref_month_start: Optional[date] = None,
    include_items: bool = False,
    limit: int = 24,
    offset: int = 0,
) -> Dict[str, Any]:
    user_id = get_request_context().user_id

    invoices = SupaBaseFinanceDB.list_card_invoices(
        user_id=user_id,
        card_id=card_id,
        ref_month_start_from=ref_month_start_from,
        ref_month_start_to=ref_month_start_to,
        limit=limit,
        offset=offset,
    )

    if not ref_month_start:
        return {"invoices": invoices}

    header = next((i for i in invoices if i.get("ref_month_start") == ref_month_start), None)
    if header is None:
        only = SupaBaseFinanceDB.list_card_invoices(
            user_id=user_id,
            card_id=card_id,
            ref_month_start_from=ref_month_start,
            ref_month_start_to=ref_month_start,
            limit=1,
            offset=0,
        )
        header = only[0] if only else None

    if not header:
        return {"invoices": invoices, "invoice": None, "items": []}

    items: List[Dict[str, Any]] = []
    if include_items:
        use_card_id = header.get("card_id") or card_id
        if not use_card_id:
            return {"invoices": invoices, "invoice": header, "items": [], "warning": "card_id necessário para carregar itens"}
        items = SupaBaseFinanceDB.list_card_invoice_items(
            user_id=user_id,
            card_id=use_card_id,
            ref_month_start=ref_month_start,
            limit=500,
            offset=0,
        )

    return {"invoices": invoices, "invoice": header, "items": items}


TOOL = StructuredTool.from_function(
    name="finance_card_invoices",
    description="Lista faturas do cartão (vw_finance_card_invoices) e opcionalmente detalha itens (vw_finance_card_invoice_items).",
    args_schema=Args,
    coroutine=_run,
)
