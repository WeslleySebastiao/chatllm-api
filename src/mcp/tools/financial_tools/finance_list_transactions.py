from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from typing_extensions import Annotated

from src.mcp.request_context import get_request_context
from src.data.supaBase.supabase_financial_db import SupaBaseFinanceDB


class Args(BaseModel):
    date_from: Optional[date] = Field(None, description="Data inicial (YYYY-MM-DD).")
    date_to: Optional[date] = Field(None, description="Data final (YYYY-MM-DD).")

    type: Optional[Literal["expense", "income"]] = Field(
        None, description="Filtrar por tipo: expense ou income."
    )
    payment_method: Optional[Literal["pix", "debit", "credit", "cash", "transfer"]] = Field(
        None, description="Filtrar por método de pagamento."
    )

    account_name: Optional[str] = Field(
        None, description="Filtrar por nome da conta (ex: 'Itaú'). Resolvido automaticamente."
    )
    card_name: Optional[str] = Field(
        None, description="Filtrar por nome do cartão (ex: 'Nubank'). Resolvido automaticamente."
    )

    q: Optional[str] = Field(
        None, description="Busca por texto em descrição, merchant ou notes."
    )

    limit: Annotated[int, Field(ge=1, le=200, description="Quantidade de resultados.")] = 50
    offset: Annotated[int, Field(ge=0, description="Paginação.")] = 0


async def _run(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    type: Optional[str] = None,
    payment_method: Optional[str] = None,
    account_name: Optional[str] = None,
    card_name: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    user_id = get_request_context().user_id

    # Resolve nomes → UUIDs sem auto_create (só filtra se existir)
    account_id = None
    if account_name:
        account_id = SupaBaseFinanceDB.resolve_account_id(
            user_id=user_id,
            name=account_name,
            auto_create=False,
        )
        if not account_id:
            return {"error": f"Conta '{account_name}' não encontrada.", "transactions": []}

    card_id = None
    if card_name:
        card_id = SupaBaseFinanceDB.resolve_card_id(
            user_id=user_id,
            name=card_name,
            auto_create=False,
        )
        if not card_id:
            return {"error": f"Cartão '{card_name}' não encontrado.", "transactions": []}

    rows = SupaBaseFinanceDB.list_transactions(
        user_id=user_id,
        date_from=date_from,
        date_to=date_to,
        type=type,
        payment_method=payment_method,
        account_id=account_id,
        card_id=card_id,
        q=q,
        limit=limit,
        offset=offset,
    )

    return {
        "count": len(rows),
        "limit": limit,
        "offset": offset,
        "transactions": rows,
    }


TOOL = StructuredTool.from_function(
    name="finance_list_transactions",
    description=(
        "Lista transações com filtros opcionais: período, tipo (expense/income), "
        "método de pagamento, conta, cartão ou busca por texto. "
        "Use account_name e card_name pelo nome (ex: 'Itaú', 'Nubank')."
    ),
    args_schema=Args,
    coroutine=_run,
)