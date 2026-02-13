from __future__ import annotations

from datetime import date
from typing import Any, Dict, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from typing_extensions import Annotated
from src.mcp.request_context import get_request_context
from src.data.supaBase.supabase_financial_db import SupaBaseFinanceDB


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

    account_name: Optional[str] = Field(
        None,
        description="Nome da conta (ex: 'Itaú'). Obrigatório para pix/debit/transfer. Não usar com credit.",
    )

    card_name: Optional[str] = Field(
        None,
        description="Nome do cartão (ex: 'Nubank'). Obrigatório para credit. Não usar com pix/debit/transfer.",
    )


async def _run(**kwargs) -> Dict[str, Any]:
    user_id = get_request_context().user_id

    payment_method = kwargs["payment_method"]

    # Resolve account_name → UUID
    account_id = None
    account_name = kwargs.get("account_name")
    if account_name:
        account_id = SupaBaseFinanceDB.resolve_account_id(
            user_id=user_id,
            name=account_name,
            auto_create=True,
        )

    # Resolve card_name → UUID
    card_id = None
    card_name = kwargs.get("card_name")
    if card_name:
        card_id = SupaBaseFinanceDB.resolve_card_id(
            user_id=user_id,
            name=card_name,
            auto_create=False,
        )
        if not card_id:
            return {"error": f"Cartão '{card_name}' não encontrado. Crie-o antes com finance_create_card."}

    row = SupaBaseFinanceDB.create_transaction(
        user_id=user_id,
        type=kwargs["type"],
        amount_cents=kwargs["amount_cents"],
        currency=kwargs.get("currency", "BRL"),
        txn_date=kwargs["txn_date"],
        description=kwargs["description"],
        merchant=kwargs.get("merchant"),
        notes=kwargs.get("notes"),
        category_id=kwargs.get("category_id"),
        payment_method=payment_method,
        account_id=account_id,
        card_id=card_id,
        installment_total=None,
        installment_current=None,
        installment_group_id=None,
        is_transfer=(payment_method == "transfer"),
    )
    return row


TOOL = StructuredTool.from_function(
    name="finance_create_transaction",
    description=(
        "Cria uma transação financeira (pix/debit/cash/transfer/credit sem parcelamento). "
        "Use account_name para pix/debit/transfer (ex: 'Itaú') "
        "e card_name para credit (ex: 'Nubank'). "
        "Para cash, não informe account_name nem card_name. "
        "Valor em centavos (ex: R$ 50,00 → 5000)."
    ),
    args_schema=Args,
    coroutine=_run,
)