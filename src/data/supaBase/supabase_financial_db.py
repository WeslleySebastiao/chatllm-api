from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from src.data.supaBase.supaBase_db import DB


def _uuid(v: str | UUID) -> str:
    return str(v)


class SupaBaseFinanceDB:

    @staticmethod
    def create_transaction(
        *,
        user_id: str | UUID,
        type: str,  # 'expense' | 'income'
        amount_cents: int,
        currency: str,
        txn_date: date,
        description: str,
        payment_method: str,  # enum
        account_id: Optional[str | UUID] = None,
        card_id: Optional[str | UUID] = None,
        category_id: Optional[str | UUID] = None,
        merchant: Optional[str] = None,
        notes: Optional[str] = None,
        is_transfer: bool = False,
        installment_total: Optional[int] = None,
        installment_current: Optional[int] = None,
        installment_group_id: Optional[str | UUID] = None,
    ) -> Dict[str, Any]:
        sql = """
        insert into public.finance_transactions
            (user_id, type, amount_cents, currency, txn_date, description, merchant, notes,
             category_id, payment_method, account_id, card_id,
             installment_total, installment_current, installment_group_id,
             is_transfer)
        values
            (%s, %s, %s, %s, %s, %s, %s, %s,
             %s, %s, %s, %s,
             %s, %s, %s,
             %s)
        returning id, created_at;
        """
        params = (
            _uuid(user_id), type, int(amount_cents), currency, txn_date, description, merchant, notes,
            _uuid(category_id) if category_id else None,
            payment_method,
            _uuid(account_id) if account_id else None,
            _uuid(card_id) if card_id else None,
            installment_total, installment_current,
            _uuid(installment_group_id) if installment_group_id else None,
            bool(is_transfer),
        )
        row = DB.fetch_one(sql, params)
        return dict(row)

    @staticmethod
    def soft_delete_transaction(*, user_id: str | UUID, transaction_id: str | UUID) -> bool:
        sql = """
        update public.finance_transactions
           set deleted_at = now(),
               updated_at = now()
         where id = %s
           and user_id = %s
           and deleted_at is null;
        """
        rows = DB.execute(sql, (_uuid(transaction_id), _uuid(user_id)))
        return rows > 0

    @staticmethod
    def update_transaction(
        *,
        user_id: str | UUID,
        transaction_id: str | UUID,
        patch: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        patch permitido (ex): amount_cents, txn_date, description, merchant, notes, category_id,
        payment_method, account_id, card_id.
        OBS: se mexer em payment_method/account_id/card_id, o check constraint pode falhar.
        """
        allowed = {
            "type", "amount_cents", "currency", "txn_date", "description", "merchant", "notes",
            "category_id", "payment_method", "account_id", "card_id", "is_transfer"
        }
        keys = [k for k in patch.keys() if k in allowed]
        if not keys:
            return None

        sets = []
        params: List[Any] = []
        for k in keys:
            sets.append(f"{k} = %s")
            v = patch[k]
            if k in {"category_id", "account_id", "card_id"} and v is not None:
                v = _uuid(v)
            params.append(v)

        sql = f"""
        update public.finance_transactions
           set {", ".join(sets)},
               updated_at = now()
         where id = %s
           and user_id = %s
           and deleted_at is null
        returning *;
        """
        params.extend([_uuid(transaction_id), _uuid(user_id)])
        row = DB.fetch_one(sql, tuple(params))
        return dict(row) if row else None

    @staticmethod
    def get_transaction(*, user_id: str | UUID, transaction_id: str | UUID) -> Optional[Dict[str, Any]]:
        sql = """
        select *
          from public.finance_transactions
         where id = %s and user_id = %s;
        """
        row = DB.fetch_one(sql, (_uuid(transaction_id), _uuid(user_id)))
        return dict(row) if row else None

    @staticmethod
    def list_transactions(
        *,
        user_id: str | UUID,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        type: Optional[str] = None,
        payment_method: Optional[str] = None,
        account_id: Optional[str | UUID] = None,
        card_id: Optional[str | UUID] = None,
        category_id: Optional[str | UUID] = None,
        q: Optional[str] = None,
        include_deleted: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        where = ["user_id = %s"]
        params: List[Any] = [_uuid(user_id)]

        if not include_deleted:
            where.append("deleted_at is null")
        if date_from:
            where.append("txn_date >= %s"); params.append(date_from)
        if date_to:
            where.append("txn_date <= %s"); params.append(date_to)
        if type:
            where.append("type = %s"); params.append(type)
        if payment_method:
            where.append("payment_method = %s"); params.append(payment_method)
        if account_id:
            where.append("account_id = %s"); params.append(_uuid(account_id))
        if card_id:
            where.append("card_id = %s"); params.append(_uuid(card_id))
        if category_id:
            where.append("category_id = %s"); params.append(_uuid(category_id))
        if q:
            where.append("(description ilike %s or merchant ilike %s or notes ilike %s)")
            like = f"%{q}%"
            params.extend([like, like, like])

        sql = f"""
        select *
          from public.finance_transactions
         where {" and ".join(where)}
         order by txn_date desc, created_at desc
         limit %s offset %s;
        """
        params.extend([int(limit), int(offset)])
        rows = DB.fetch_all(sql, tuple(params))
        return [dict(r) for r in rows]

    @staticmethod
    def create_credit_installments(
        *,
        user_id: str | UUID,
        card_id: str | UUID,
        type: str,
        total_amount_cents: int,
        currency: str,
        txn_date: date,
        description: str,
        installment_total: int,
        category_id: Optional[str | UUID] = None,
        merchant: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Cria N transações credit com installment_current=1..N, mesmo installment_group_id.
        Regra de centavos: distribui o resto nas primeiras parcelas.
        """
        n = int(installment_total)
        total = int(total_amount_cents)
        if n < 1:
            raise ValueError("installment_total must be >= 1")
        if total <= 0:
            raise ValueError("total_amount_cents must be > 0")

        group_id = uuid4()

        base = total // n
        rem = total % n

        created: List[Dict[str, Any]] = []
        # transação/parcelas: data pode ser a mesma (data da compra) ou avançar mês a mês.
        # MVP simples: mantém txn_date como data da compra. Se quiser avançar, dá pra somar meses aqui.
        for i in range(1, n + 1):
            amt = base + (1 if i <= rem else 0)
            row = SupaBaseFinanceDB.create_transaction(
                user_id=user_id,
                type=type,
                amount_cents=amt,
                currency=currency,
                txn_date=txn_date,
                description=description,
                merchant=merchant,
                notes=notes,
                category_id=category_id,
                payment_method="credit",
                account_id=None,
                card_id=card_id,
                installment_total=n,
                installment_current=i,
                installment_group_id=group_id,
            )
            created.append({"id": row["id"], "installment_current": i, "amount_cents": amt, "txn_date": str(txn_date)})

        return {
            "installment_group_id": str(group_id),
            "transactions_created": created,
        }


    @staticmethod
    def get_account_balances(*, user_id: str | UUID) -> List[Dict[str, Any]]:
        sql = """
        select *
          from public.vw_finance_account_balance
         where user_id = %s
         order by name asc;
        """
        rows = DB.fetch_all(sql, (_uuid(user_id),))
        return [dict(r) for r in rows]

    @staticmethod
    def list_card_invoices(
        *,
        user_id: str | UUID,
        card_id: Optional[str | UUID] = None,
        ref_month_start_from: Optional[date] = None,
        ref_month_start_to: Optional[date] = None,
        limit: int = 24,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        where = ["user_id = %s"]
        params: List[Any] = [_uuid(user_id)]

        if card_id:
            where.append("card_id = %s"); params.append(_uuid(card_id))
        if ref_month_start_from:
            where.append("ref_month_start >= %s"); params.append(ref_month_start_from)
        if ref_month_start_to:
            where.append("ref_month_start <= %s"); params.append(ref_month_start_to)

        sql = f"""
        select *
          from public.vw_finance_card_invoices
         where {" and ".join(where)}
         order by ref_month_start desc
         limit %s offset %s;
        """
        params.extend([int(limit), int(offset)])
        rows = DB.fetch_all(sql, tuple(params))
        return [dict(r) for r in rows]

    @staticmethod
    def list_card_invoice_items(
        *,
        user_id: str | UUID,
        card_id: str | UUID,
        ref_month_start: date,
        limit: int = 500,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        sql = """
        select *
          from public.vw_finance_card_invoice_items
         where user_id = %s
           and card_id = %s
           and ref_month_start = %s
         order by txn_date asc, transaction_id asc
         limit %s offset %s;
        """
        rows = DB.fetch_all(
            sql,
            (_uuid(user_id), _uuid(card_id), ref_month_start, int(limit), int(offset)),
        )
        return [dict(r) for r in rows]
