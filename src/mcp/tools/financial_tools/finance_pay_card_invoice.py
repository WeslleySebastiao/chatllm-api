from __future__ import annotations

from datetime import date
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from typing_extensions import Annotated

from src.mcp.request_context import get_request_context
from src.data.supaBase.supabase_financial_db import SupaBaseFinanceDB


class Args(BaseModel):
    card_name: Annotated[
        str,
        Field(min_length=1, description="Nome do cartão (ex: 'Nubank').")
    ]

    ref_month_start: Annotated[
        date,
        Field(description="Mês de referência da fatura (YYYY-MM-DD, ex: 2026-02-01).")
    ]

    account_name: Annotated[
        str,
        Field(min_length=1, description="Nome da conta que vai debitar o pagamento (ex: 'Itaú').")
    ]

    paid_at: Optional[date] = Field(
        None,
        description="Data do pagamento (YYYY-MM-DD). Se não informado, usa a data de hoje.",
    )

    notes: Optional[str] = Field(None, description="Observação opcional.")


async def _run(**kwargs) -> Dict[str, Any]:
    user_id = get_request_context().user_id

    # Resolve cartão
    card_id = SupaBaseFinanceDB.resolve_card_id(
        user_id=user_id,
        name=kwargs["card_name"],
        auto_create=False,
    )
    if not card_id:
        return {"error": f"Cartão '{kwargs['card_name']}' não encontrado."}

    # Resolve conta
    account_id = SupaBaseFinanceDB.resolve_account_id(
        user_id=user_id,
        name=kwargs["account_name"],
        auto_create=False,
    )
    if not account_id:
        return {"error": f"Conta '{kwargs['account_name']}' não encontrada."}

    ref_month_start = kwargs["ref_month_start"]
    paid_at = kwargs.get("paid_at") or date.today()

    # Busca o total da fatura na view
    invoice = SupaBaseFinanceDB.get_card_invoice(
        user_id=user_id,
        card_id=card_id,
        ref_month_start=ref_month_start,
    )
    if not invoice:
        return {"error": f"Fatura de {ref_month_start} não encontrada para o cartão '{kwargs['card_name']}'."}

    amount_cents = invoice["total_cents"]
    if not amount_cents or amount_cents <= 0:
        return {"error": f"Fatura de {ref_month_start} está vazia (total = 0)."}

    # Registra o pagamento (cria/atualiza registro + gera transação na conta)
    result = SupaBaseFinanceDB.pay_card_invoice(
        user_id=user_id,
        card_id=card_id,
        account_id=account_id,
        ref_month_start=ref_month_start,
        amount_cents=amount_cents,
        currency=invoice.get("currency", "BRL"),
        paid_at=paid_at,
        notes=kwargs.get("notes"),
        card_name=kwargs["card_name"],
    )
    return result


TOOL = StructuredTool.from_function(
    name="finance_pay_card_invoice",
    description=(
        "Registra o pagamento de uma fatura de cartão de crédito. "
        "Busca automaticamente o total da fatura pela view e debita da conta informada. "
        "Informe o nome do cartão, o mês de referência (YYYY-MM-01) e a conta que vai pagar."
    ),
    args_schema=Args,
    coroutine=_run,
)