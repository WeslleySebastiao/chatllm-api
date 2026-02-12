from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from typing_extensions import Annotated

from src.mcp.request_context import get_request_context
from src.data.supaBase.supabase_financial_db import SupaBaseFinanceDB


FinanceCardBrand = Literal["visa", "mastercard", "elo", "amex", "hipercard", "other"]


class Args(BaseModel):
    name: Annotated[
        str,
        Field(min_length=1, max_length=100, description="Nome do cartão (ex: 'Nubank', 'C6 Gold').")
    ]

    closing_day: Annotated[
        int,
        Field(ge=1, le=28, description="Dia do fechamento da fatura (1-28).")
    ]

    due_day: Annotated[
        int,
        Field(ge=1, le=28, description="Dia do vencimento da fatura (1-28).")
    ]

    brand: Annotated[
        FinanceCardBrand,
        Field(description="Bandeira: visa, mastercard, elo, amex, hipercard, other.")
    ] = "other"

    limit_cents: Optional[int] = Field(
        None,
        ge=0,
        description="Limite em centavos (ex: R$ 5.000,00 → 500000). Deixe vazio se não souber.",
    )

    currency: str = Field(
        default="BRL",
        min_length=3,
        max_length=3,
        description="Moeda (ex: BRL).",
    )


async def _run(**kwargs) -> Dict[str, Any]:
    user_id = get_request_context().user_id

    row = SupaBaseFinanceDB.create_card(
        user_id=user_id,
        name=kwargs["name"],
        brand=kwargs.get("brand", "other"),
        closing_day=kwargs["closing_day"],
        due_day=kwargs["due_day"],
        limit_cents=kwargs.get("limit_cents"),
        currency=kwargs.get("currency", "BRL"),
    )
    return row


TOOL = StructuredTool.from_function(
    name="finance_create_card",
    description=(
        "Cria um cartão de crédito. "
        "Use o nome como o usuário se refere (ex: 'Nubank', 'C6 Gold'). "
        "Informe closing_day (fechamento) e due_day (vencimento), ambos entre 1 e 28. "
        "Limite em centavos (ex: R$ 5.000,00 → 500000). Bandeira: visa, mastercard, elo, amex, hipercard, other."
    ),
    args_schema=Args,
    coroutine=_run,
)