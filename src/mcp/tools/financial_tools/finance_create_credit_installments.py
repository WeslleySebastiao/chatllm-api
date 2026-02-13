from __future__ import annotations

from datetime import date
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from typing_extensions import Annotated

from src.mcp.request_context import get_request_context
from src.data.supaBase.supabase_financial_db import SupaBaseFinanceDB


FinanceTxnType = Literal["expense", "income"]


class Args(BaseModel):
    card_name: Annotated[
        str,
        Field(min_length=1, description="Nome do cartão (ex: 'Itaú', 'Nubank').")
    ]

    total_amount_cents: Annotated[
        int,
        Field(gt=0, description="Valor total em centavos (ex: R$ 124,50 → 12450).")
    ]

    installment_total: Annotated[
        int,
        Field(ge=1, description="Número de parcelas (ex: 10).")
    ]

    txn_date: Annotated[
        date,
        Field(description="Data da compra (YYYY-MM-DD).")
    ]

    description: Annotated[
        str,
        Field(min_length=1, description="Descrição da compra.")
    ]

    type: Annotated[
        FinanceTxnType,
        Field(description="Tipo: expense ou income. Normalmente expense.")
    ] = "expense"

    currency: Annotated[
        str,
        Field(min_length=3, max_length=3, description="Moeda (ex: BRL).")
    ] = "BRL"

    merchant: Optional[str] = Field(None, description="Comerciante (opcional).")
    notes: Optional[str] = Field(None, description="Observações (opcional).")


async def _run(**kwargs) -> Dict[str, Any]:
    user_id = get_request_context().user_id

    # Resolve card_name → UUID
    card_id = SupaBaseFinanceDB.resolve_card_id(
        user_id=user_id,
        name=kwargs["card_name"],
        auto_create=False,
    )
    if not card_id:
        return {"error": f"Cartão '{kwargs['card_name']}' não encontrado. Crie-o antes com finance_create_card."}

    result = SupaBaseFinanceDB.create_credit_installments(
        user_id=user_id,
        card_id=card_id,
        type=kwargs.get("type", "expense"),
        total_amount_cents=kwargs["total_amount_cents"],
        currency=kwargs.get("currency", "BRL"),
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
    description=(
        "Cria uma compra parcelada no cartão de crédito (gera N transações, uma por mês). "
        "Use card_name pelo nome do cartão (ex: 'Itaú', 'Nubank'). "
        "Valor total em centavos (ex: R$ 124,50 → 12450). "
        "Informe o número de parcelas em installment_total."
    ),
    args_schema=Args,
    coroutine=_run,
)