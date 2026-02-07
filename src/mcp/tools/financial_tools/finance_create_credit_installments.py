from __future__ import annotations

from datetime import date
from typing import Any, Dict, Literal, Optional
from uuid import UUID

from pydantic import BaseModel
from typing_extensions import Annotated
from pydantic import Field
from langchain_core.tools import StructuredTool

from src.mcp.request_context import get_request_context
from src.data.supaBase.supabase_financial_db import SupaBaseFinanceDB


FinanceTxnType = Literal["expense", "income"]


class Args(BaseModel):
    card_id: UUID = Field(..., description="ID do cartão de crédito.")

    type: Annotated[
        FinanceTxnType,
        Field(description="Normalmente expense.")
    ] = "expense"

    total_amount_cents: Annotated[
        int,
        Field(gt=0, description="Valor total em centavos (>0).")
    ]

    currency: Annotated[
        str,
        Field(min_length=3, max_length=3, description="Moeda (ex: BRL).")
    ] = "BRL"

    txn_date: date = Field(..., description="Data da compra (YYYY-MM-DD).")

    description: Annotated[
        str,
        Field(min_length=1, description="Descrição da compra.")
    ]

    installment_total: Annotated[
        int,
        Field(ge=1, description="Número de parcelas (>=1).")
    ]

    category_id: Optional[UUID] = Field(None, description="Categoria (opcional).")
    merchant: Optional[str] = Field(None, description="Comerciante (opcional).")
    notes: Optional[str] = Field(None, description="Observações (opcional).")


async def _run(**kwargs) -> Dict[str, Any]:
    user_id = get_request_context().user_id

    # IMPORTANTE: sua implementação no DB deve avançar o txn_date mês a mês para as parcelas,
    # senão sua view de fatura joga tudo na mesma fatura.
    result = SupaBaseFinanceDB.create_credit_installments(
        user_id=user_id,
        card_id=kwargs["card_id"],
        type=kwargs["type"],
        total_amount_cents=kwargs["total_amount_cents"],
        currency=kwargs["currency"],
        txn_date=kwargs["txn_date"],
        description=kwargs["description"],
        installment_total=kwargs["installment_total"],
        category_id=kwargs.get("category_id"),
        merchant=kwargs.get("merchant"),
        notes=kwargs.get("notes"),
    )
    return result


TOOL = StructuredTool.from_function(
    name="finance_create_credit_installments",
    description="Cria compra no crédito parcelada (gera N transações vinculadas).",
    args_schema=Args,
    coroutine=_run,
)
