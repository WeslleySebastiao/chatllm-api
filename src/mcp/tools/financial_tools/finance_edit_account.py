from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from typing_extensions import Annotated

from src.mcp.request_context import get_request_context
from src.data.supaBase.supabase_financial_db import SupaBaseFinanceDB


AccountType = Literal["checking", "savings", "investment", "wallet"]


class Args(BaseModel):
    account_name: Annotated[
        str,
        Field(min_length=1, description="Nome atual da conta a ser editada (ex: 'Itaú').")
    ]

    new_name: Optional[str] = Field(
        None, min_length=1, max_length=100,
        description="Novo nome da conta (opcional).",
    )

    new_type: Optional[AccountType] = Field(
        None,
        description="Novo tipo: checking, savings, investment, wallet (opcional).",
    )

    new_current_balance_cents: Optional[int] = Field(
        None,
        description=(
            "Saldo atual real da conta em centavos (opcional). "
            "Use quando o usuário informar o saldo real da conta. "
            "Ex: R$ 1.500,00 → 150000. "
            "Isso ajusta o starting_balance_cents para que o saldo calculado bata com o real."
        ),
    )

    new_currency: Optional[str] = Field(
        None, min_length=3, max_length=3,
        description="Nova moeda (ex: BRL) (opcional).",
    )


async def _run(**kwargs) -> Dict[str, Any]:
    user_id = get_request_context().user_id

    account_id = SupaBaseFinanceDB.resolve_account_id(
        user_id=user_id,
        name=kwargs["account_name"],
        auto_create=False,
    )

    if not account_id:
        return {"error": f"Conta '{kwargs['account_name']}' não encontrada."}

    patch: Dict[str, Any] = {}

    if kwargs.get("new_name") is not None:
        patch["name"] = kwargs["new_name"]
    if kwargs.get("new_type") is not None:
        patch["type"] = kwargs["new_type"]
    if kwargs.get("new_currency") is not None:
        patch["currency"] = kwargs["new_currency"]

    # Saldo atual informado pelo usuário:
    # recalcula starting_balance_cents = saldo_desejado - soma_das_transações
    if kwargs.get("new_current_balance_cents") is not None:
        txn_sum = SupaBaseFinanceDB.get_account_txn_sum(
            user_id=user_id,
            account_id=account_id,
        )
        patch["starting_balance_cents"] = kwargs["new_current_balance_cents"] - txn_sum

    if not patch:
        return {"error": "Nenhum campo para atualizar foi informado."}

    row = SupaBaseFinanceDB.update_account(
        user_id=user_id,
        account_id=account_id,
        patch=patch,
    )
    return row


TOOL = StructuredTool.from_function(
    name="finance_edit_account",
    description=(
        "Edita uma conta financeira existente identificada pelo nome (ex: 'Itaú'). "
        "Para corrigir o saldo, use new_current_balance_cents com o valor real atual em centavos. "
        "Também permite alterar nome, tipo e moeda."
    ),
    args_schema=Args,
    coroutine=_run,
)