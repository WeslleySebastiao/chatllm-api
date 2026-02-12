from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from typing_extensions import Annotated

from src.mcp.request_context import get_request_context
from src.data.supaBase.supabase_financial_db import SupaBaseFinanceDB


FinanceCardBrand = Literal["visa", "mastercard", "elo", "amex", "hipercard", "other"]


class Args(BaseModel):
    card_name: Annotated[
        str,
        Field(min_length=1, description="Nome atual do cartão (ex: 'Nubank').")
    ]

    new_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Novo nome (opcional).")
    new_brand: Optional[FinanceCardBrand] = Field(None, description="Nova bandeira (opcional).")
    new_closing_day: Optional[int] = Field(None, ge=1, le=28, description="Novo dia de fechamento (1-28) (opcional).")
    new_due_day: Optional[int] = Field(None, ge=1, le=28, description="Novo dia de vencimento (1-28) (opcional).")
    new_limit_cents: Optional[int] = Field(None, ge=0, description="Novo limite em centavos (opcional).")


async def _run(**kwargs) -> Dict[str, Any]:
    user_id = get_request_context().user_id

    card_id = SupaBaseFinanceDB.resolve_card_id(
        user_id=user_id,
        name=kwargs["card_name"],
        auto_create=False,
    )

    if not card_id:
        return {"error": f"Cartão '{kwargs['card_name']}' não encontrado."}

    patch: Dict[str, Any] = {}
    if kwargs.get("new_name") is not None:
        patch["name"] = kwargs["new_name"]
    if kwargs.get("new_brand") is not None:
        patch["brand"] = kwargs["new_brand"]
    if kwargs.get("new_closing_day") is not None:
        patch["closing_day"] = kwargs["new_closing_day"]
    if kwargs.get("new_due_day") is not None:
        patch["due_day"] = kwargs["new_due_day"]
    if kwargs.get("new_limit_cents") is not None:
        patch["limit_cents"] = kwargs["new_limit_cents"]

    if not patch:
        return {"error": "Nenhum campo para atualizar foi informado."}

    row = SupaBaseFinanceDB.update_card(
        user_id=user_id,
        card_id=card_id,
        patch=patch,
    )
    return row


TOOL = StructuredTool.from_function(
    name="finance_edit_card",
    description=(
        "Edita um cartão existente identificado pelo nome. "
        "Informe apenas os campos que deseja alterar: nome, bandeira, "
        "dia de fechamento, dia de vencimento ou limite."
    ),
    args_schema=Args,
    coroutine=_run,
)