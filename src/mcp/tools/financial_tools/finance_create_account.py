from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from typing_extensions import Annotated

from src.mcp.request_context import get_request_context
from src.data.supaBase.supabase_financial_db import SupaBaseFinanceDB


AccountType = Literal["checking", "savings", "cash", "investment", "other"]


class Args(BaseModel):
    name: Annotated[
        str,
        Field(min_length=1, max_length=100, description="Nome da conta (ex: Itaú, Nubank).")
    ]

    type: Annotated[
        AccountType,
        Field(description="Tipo: checking (corrente), savings (poupança), cash (dinheiro), investment, other.")
    ] = "checking"

    starting_balance_cents: Annotated[
        int,
        Field(description="Saldo inicial em centavos. Use 0 se não souber.")
    ] = 0

    currency: Annotated[
        str,
        Field(min_length=3, max_length=3, description="Moeda (ex: BRL).")
    ] = "BRL"


async def _run(**kwargs) -> Dict[str, Any]:
    user_id = get_request_context().user_id

    row = SupaBaseFinanceDB.create_account(
        user_id=user_id,
        name=kwargs["name"],
        type=kwargs["type"],
        starting_balance_cents=kwargs["starting_balance_cents"],
        currency=kwargs["currency"],
    )
    return row


TOOL = StructuredTool.from_function(
    name="finance_create_account",
    description=(
        "Cria uma conta financeira (corrente, poupança, dinheiro, etc). "
        "Use o nome como o usuário se refere (ex: 'Itaú', 'Nubank', 'Carteira'). "
        "Saldo inicial em centavos (ex: R$ 1.000,00 → 100000)."
    ),
    args_schema=Args,
    coroutine=_run,
)