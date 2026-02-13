from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4
from dateutil.relativedelta import relativedelta
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
        Cria N transações credit avançando o txn_date mês a mês.
        Parcela 1 → mês da compra
        Parcela 2 → mês seguinte
        ...e assim por diante.
        Isso garante que cada parcela cai na fatura correta.
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

        for i in range(1, n + 1):
            amt = base + (1 if i <= rem else 0)

            # avança o mês a cada parcela mantendo o mesmo dia
            # ex: compra em 15/02 → parcela 1: 15/02, parcela 2: 15/03, etc.
            installment_date = txn_date + relativedelta(months=i - 1)

            row = SupaBaseFinanceDB.create_transaction(
                user_id=user_id,
                type=type,
                amount_cents=amt,
                currency=currency,
                txn_date=installment_date,
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
                is_transfer=False,
            )
            created.append({
                "id": row["id"],
                "installment_current": i,
                "amount_cents": amt,
                "txn_date": str(installment_date),
            })

        return {
            "installment_group_id": str(group_id),
            "installment_total": n,
            "amount_per_installment_cents": base,
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

    @staticmethod
    def create_card(
        user_id: str,
        name: str,
        closing_day: int,
        due_day: int,
        brand: str = "other",
        limit_cents: Optional[int] = None,
        currency: str = "BRL",
    ) -> dict:
        sql = """
        insert into public.finance_cards
            (user_id, name, brand, closing_day, due_day, limit_cents, currency)
        values
            (%s, %s, %s, %s, %s, %s, %s)
        returning
            id, user_id, name, brand, closing_day, due_day, limit_cents, currency, status, created_at;
        """
        row = DB.fetch_one(
            sql,
            (_uuid(user_id), name, brand, closing_day, due_day, limit_cents, currency),
        )
        if row:
            row["id"] = str(row["id"])
            row["user_id"] = str(row["user_id"])
        return dict(row)

    @staticmethod
    def update_account(user_id: str, account_id: str, patch: dict) -> dict:
        allowed = {"name", "type", "starting_balance_cents", "currency"}
        sets = []
        values = []

        for k, v in patch.items():
            if k not in allowed:
                continue
            sets.append(f"{k} = %s")
            values.append(v)

        if not sets:
            return {"error": "Nenhum campo válido para atualizar."}

        sets.append("updated_at = now()")

        sql = f"""
        update public.finance_accounts
           set {", ".join(sets)}
         where id = %s
           and user_id = %s
           and status = 'active'
        returning
            id, user_id, name, type, starting_balance_cents, currency, status, created_at, updated_at;
        """
        values.extend([account_id, user_id])

        row = DB.fetch_one(sql, tuple(values))
        if not row:
            return {"error": "Conta não encontrada ou encerrada."}
        row["id"] = str(row["id"])
        row["user_id"] = str(row["user_id"])
        return dict(row)

    @staticmethod
    def get_account_txn_sum(*, user_id: str | UUID, account_id: str) -> int:
        """
        Soma líquida das transações de uma conta (income - expense).
        Usado para recalcular starting_balance_cents quando o usuário informa o saldo real.
        """
        sql = """
        select coalesce(sum(
            case when type = 'income' then amount_cents else -amount_cents end
        ), 0)::bigint as net_cents
          from public.finance_transactions
         where user_id = %s
           and account_id = %s
           and payment_method in ('pix', 'debit', 'transfer')
           and deleted_at is null;
        """
        row = DB.fetch_one(sql, (_uuid(user_id), account_id))
        return int(row["net_cents"]) if row else 0

    @staticmethod
    def create_card(
        user_id: str,
        name: str,
        closing_day: int,
        due_day: int,
        brand: str = "other",
        limit_cents: Optional[int] = None,
        currency: str = "BRL",
    ) -> dict:
        sql = """
        insert into public.finance_cards
            (user_id, name, brand, closing_day, due_day, limit_cents, currency)
        values
            (%s, %s, %s, %s, %s, %s, %s)
        returning
            id, user_id, name, brand, closing_day, due_day, limit_cents, currency, status, created_at;
        """
        row = DB.fetch_one(
            sql,
            (_uuid(user_id), name, brand, closing_day, due_day, limit_cents, currency),
        )
        if row:
            row["id"] = str(row["id"])
            row["user_id"] = str(row["user_id"])
        return dict(row)

    @staticmethod
    def update_card(user_id: str, card_id: str, patch: dict) -> dict:
        allowed = {"name", "brand", "closing_day", "due_day", "limit_cents"}
        sets = []
        values = []

        for k, v in patch.items():
            if k not in allowed:
                continue
            sets.append(f"{k} = %s")
            values.append(v)

        if not sets:
            return {"error": "Nenhum campo válido para atualizar."}

        sets.append("updated_at = now()")

        sql = f"""
        update public.finance_cards
           set {", ".join(sets)}
         where id = %s
           and user_id = %s
           and status = 'active'
        returning
            id, user_id, name, brand, closing_day, due_day, limit_cents, currency,
            status, created_at, updated_at;
        """
        values.extend([card_id, user_id])

        row = DB.fetch_one(sql, tuple(values))
        if not row:
            return {"error": "Cartão não encontrado ou encerrado."}
        row["id"] = str(row["id"])
        row["user_id"] = str(row["user_id"])
        return dict(row)

    
    @staticmethod
    def resolve_account_id(
        *,
        user_id: str | UUID,
        name: str,
        auto_create: bool = True,
    ) -> Optional[str]:
        sql = """
        select id
          from public.finance_accounts
         where user_id = %s
           and lower(name) = lower(%s)
           and status = 'active'
         limit 1;
        """
        row = DB.fetch_one(sql, (_uuid(user_id), name))
        if row:
            return str(row["id"])
        if not auto_create:
            return None
        created = SupaBaseFinanceDB.create_account(
            user_id=_uuid(user_id),
            name=name,
            type="checking",
            starting_balance_cents=0,
            currency="BRL",
        )
        return str(created["id"])
    
    @staticmethod
    def resolve_card_id(
        *,
        user_id: str | UUID,
        name: str,
        auto_create: bool = False,
        closing_day: int = 1,
        due_day: int = 10,
    ) -> Optional[str]:
        sql = """
        select id
          from public.finance_cards
         where user_id = %s
           and lower(name) = lower(%s)
           and status = 'active'
         limit 1;
        """
        row = DB.fetch_one(sql, (_uuid(user_id), name))
        if row:
            return str(row["id"])
        if not auto_create:
            return None
        created = SupaBaseFinanceDB.create_card(
            user_id=_uuid(user_id),
            name=name,
            brand="other",
            closing_day=closing_day,
            due_day=due_day,
            limit_cents=None,
            currency="BRL",
        )
        return str(created["id"])

    @staticmethod
    def list_accounts(
        *,
        user_id: str | UUID,
        include_closed: bool = False,
    ) -> List[Dict[str, Any]]:
        params: list = [_uuid(user_id)]
        status_filter = "" if include_closed else "and status = 'active'"

        sql = f"""
        select id, user_id, name, institution, type, currency,
               starting_balance_cents, status, created_at, updated_at
          from public.finance_accounts
         where user_id = %s
           {status_filter}
         order by name asc;
        """
        rows = DB.fetch_all(sql, tuple(params))
        return [dict(r) for r in rows]

    # ----------------------------------------------------------
    # CARDS — listagem
    # ----------------------------------------------------------

    @staticmethod
    def list_cards(
        *,
        user_id: str | UUID,
        include_closed: bool = False,
    ) -> List[Dict[str, Any]]:
        params: list = [_uuid(user_id)]
        status_filter = "" if include_closed else "and status = 'active'"

        sql = f"""
        select id, user_id, name, brand, currency,
               limit_cents, closing_day, due_day, status, created_at, updated_at
          from public.finance_cards
         where user_id = %s
           {status_filter}
         order by name asc;
        """
        rows = DB.fetch_all(sql, tuple(params))
        return [dict(r) for r in rows]
    # ----------------------------------------------------------
    # RESUMO MENSAL
    # ----------------------------------------------------------

    @staticmethod
    def get_monthly_summary(
        *,
        user_id: str | UUID,
        year: int,
        month: int,
    ) -> Dict[str, Any]:
        date_from = date(year, month, 1)
        # último dia do mês
        if month == 12:
            date_to = date(year + 1, 1, 1)
        else:
            date_to = date(year, month + 1, 1)

        # totais gerais
        sql_totals = """
        select
            type,
            sum(amount_cents) as total_cents,
            count(*)::int      as count
          from public.finance_transactions
         where user_id = %s
           and txn_date >= %s
           and txn_date < %s
           and deleted_at is null
         group by type;
        """
        rows_totals = DB.fetch_all(sql_totals, (_uuid(user_id), date_from, date_to))

        income_cents = 0
        expense_cents = 0
        for r in rows_totals:
            if r["type"] == "income":
                income_cents = r["total_cents"]
            elif r["type"] == "expense":
                expense_cents = r["total_cents"]

        # breakdown por categoria
        sql_by_cat = """
        select
            coalesce(c.name, 'Sem categoria') as category,
            t.type,
            sum(t.amount_cents) as total_cents,
            count(*)::int        as count
          from public.finance_transactions t
          left join public.finance_categories c on c.id = t.category_id
         where t.user_id = %s
           and t.txn_date >= %s
           and t.txn_date < %s
           and t.deleted_at is null
         group by c.name, t.type
         order by total_cents desc;
        """
        rows_by_cat = DB.fetch_all(sql_by_cat, (_uuid(user_id), date_from, date_to))

        # breakdown por método de pagamento
        sql_by_method = """
        select
            payment_method,
            sum(amount_cents) as total_cents,
            count(*)::int      as count
          from public.finance_transactions
         where user_id = %s
           and txn_date >= %s
           and txn_date < %s
           and deleted_at is null
           and type = 'expense'
         group by payment_method
         order by total_cents desc;
        """
        rows_by_method = DB.fetch_all(sql_by_method, (_uuid(user_id), date_from, date_to))

        return {
            "year": year,
            "month": month,
            "period": {"from": str(date_from), "to": str(date_to)},
            "income_cents": income_cents,
            "expense_cents": expense_cents,
            "balance_cents": income_cents - expense_cents,
            "by_category": [dict(r) for r in rows_by_cat],
            "by_payment_method": [dict(r) for r in rows_by_method],
        }
    

    @staticmethod
    def get_card_invoice(
        *,
        user_id: str | UUID,
        card_id: str,
        ref_month_start: date,
    ) -> Optional[Dict[str, Any]]:
        """Busca o total de uma fatura específica na view."""
        sql = """
        select
            card_id,
            ref_month_start,
            total_cents,
            items_count,
            period_start,
            period_end
          from public.vw_finance_card_invoices
         where user_id = %s
           and card_id = %s
           and ref_month_start = %s
         limit 1;
        """
        row = DB.fetch_one(sql, (_uuid(user_id), card_id, ref_month_start))
        return dict(row) if row else None

    @staticmethod
    def pay_card_invoice(
        *,
        user_id: str | UUID,
        card_id: str,
        account_id: str,
        ref_month_start: date,
        amount_cents: int,
        currency: str,
        paid_at: date,
        card_name: str,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Registra pagamento de fatura:
        1. Cria transação de despesa (pix) na conta debitada
        2. Upsert na finance_card_payments com status=paid e FK para a transação
        """
        # 1) Cria a transação de débito na conta
        description = f"Pagamento fatura {card_name} {ref_month_start.strftime('%m/%Y')}"

        txn = SupaBaseFinanceDB.create_transaction(
            user_id=user_id,
            type="expense",
            amount_cents=amount_cents,
            currency=currency,
            txn_date=paid_at,
            description=description,
            payment_method="pix",
            account_id=account_id,
            card_id=None,
            notes=notes,
            is_transfer=False,
        )
        transaction_id = txn["id"]

        # 2) Upsert na finance_card_payments
        sql = """
        insert into public.finance_card_payments
            (user_id, card_id, ref_month_start, amount_cents, currency,
             status, paid_at, transaction_id, account_id, notes)
        values
            (%s, %s, %s, %s, %s, 'paid', %s, %s, %s, %s)
        on conflict (card_id, ref_month_start)
        do update set
            status         = 'paid',
            amount_cents   = excluded.amount_cents,
            paid_at        = excluded.paid_at,
            transaction_id = excluded.transaction_id,
            account_id     = excluded.account_id,
            notes          = excluded.notes,
            updated_at     = now()
        returning
            id, card_id, ref_month_start, amount_cents, currency,
            status, paid_at, transaction_id, account_id, created_at, updated_at;
        """
        payment = DB.fetch_one(sql, (
            _uuid(user_id),
            card_id,
            ref_month_start,
            amount_cents,
            currency,
            paid_at,
            transaction_id,
            account_id,
            notes,
        ))

        return {
            "payment_id": str(payment["id"]),
            "card_id": str(payment["card_id"]),
            "ref_month_start": str(payment["ref_month_start"]),
            "amount_cents": payment["amount_cents"],
            "status": payment["status"],
            "paid_at": str(payment["paid_at"]),
            "transaction_id": str(payment["transaction_id"]),
            "account_id": str(payment["account_id"]),
        }

    @staticmethod
    def list_card_payments(
        *,
        user_id: str | UUID,
        card_id: Optional[str] = None,
        status: Optional[str] = None,
        ref_month_start_from: Optional[date] = None,
        ref_month_start_to: Optional[date] = None,
        limit: int = 24,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        where = ["p.user_id = %s"]
        params: List[Any] = [_uuid(user_id)]

        if card_id:
            where.append("p.card_id = %s")
            params.append(card_id)
        if status:
            where.append("p.status = %s")
            params.append(status)
        if ref_month_start_from:
            where.append("p.ref_month_start >= %s")
            params.append(ref_month_start_from)
        if ref_month_start_to:
            where.append("p.ref_month_start <= %s")
            params.append(ref_month_start_to)

        sql = f"""
        select
            p.id,
            p.card_id,
            c.name as card_name,
            p.ref_month_start,
            p.amount_cents,
            p.currency,
            p.status,
            p.paid_at,
            p.transaction_id,
            p.account_id,
            a.name as account_name,
            p.notes,
            p.created_at
          from public.finance_card_payments p
          join public.finance_cards c on c.id = p.card_id
          left join public.finance_accounts a on a.id = p.account_id
         where {" and ".join(where)}
         order by p.ref_month_start desc
         limit %s offset %s;
        """
        params.extend([limit, offset])

        rows = DB.fetch_all(sql, tuple(params))
        return [dict(r) for r in rows]