from __future__ import annotations

from datetime import date
from typing import Any, Dict, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from typing_extensions import Annotated
from src.mcp.request_context import get_request_context
from src.data.supaBase.supabase_financial_db import SupaBaseFinanceDB  # ajuste o import


FinanceTxnType = Literal["expense", "income"]
FinancePaymentMethod = Literal["pix", "debit", "credit", "cash", "transfer"]


class Args(BaseModel):
    type: Annotated[
        FinanceTxnType,
        Field(description="Tipo: expense ou income.")
    ]

    amount_cents: Annotated[
        int,
        Field(gt=0, description="Valor em centavos (inteiro > 0).")
    ]

    currency: Annotated[
        str,
        Field(min_length=3, max_length=3, description="Moeda (ex: BRL).")
    ] = "BRL"

    txn_date: Annotated[
        date,
        Field(description="Data (YYYY-MM-DD).")
    ]

    description: Annotated[
        str,
        Field(min_length=1, description="Descrição curta.")
    ]

    merchant: Optional[str] = Field(None, description="Comerciante (opcional).")
    notes: Optional[str] = Field(None, description="Observações (opcional).")

    category_id: Optional[UUID] = Field(None, description="ID da categoria (opcional).")

    payment_method: Annotated[
        FinancePaymentMethod,
        Field(description="pix/debit/credit/cash/transfer")
    ]

    account_id: Optional[UUID] = Field(
        None,
        description="Obrigatório para pix/debit/transfer. Não usar com credit.",
    )

    card_id: Optional[UUID] = Field(
        None,
        description="Obrigatório para credit. Não usar com pix/debit/transfer.",
    )


async def _run(**kwargs) -> Dict[str, Any]:
    user_id = get_request_context().user_id

    row = SupaBaseFinanceDB.create_transaction(
        user_id=user_id,
        type=kwargs["type"],
        amount_cents=kwargs["amount_cents"],
        currency=kwargs["currency"],
        txn_date=kwargs["txn_date"],
        description=kwargs["description"],
        merchant=kwargs.get("merchant"),
        notes=kwargs.get("notes"),
        category_id=kwargs.get("category_id"),
        payment_method=kwargs["payment_method"],
        account_id=kwargs.get("account_id"),
        card_id=kwargs.get("card_id"),
        installment_total=None,
        installment_current=None,
        installment_group_id=None,
        is_transfer=(kwargs["payment_method"] == "transfer"),
    )
    return row


TOOL = StructuredTool.from_function(
    name="finance_create_transaction",
    description="Cria uma transação (pix/debit/cash/transfer/credit sem parcelamento).",
    args_schema=Args,
    coroutine=_run,
)
