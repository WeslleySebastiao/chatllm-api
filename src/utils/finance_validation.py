def validate_payment(payload: TransactionUpsertIn) -> None:
    m = payload.payment.method
    acc = payload.payment.account_id
    card = payload.payment.card_id

    if m in ("pix", "debit", "transfer"):
        if not acc or card is not None:
            raise ValueError("For pix/debit/transfer, account_id is required and card_id must be null.")
    elif m == "credit":
        if not card:
            raise ValueError("For credit, card_id is required.")
        # no MVP: account_id pode ser null mesmo
    elif m == "cash":
        if acc is not None or card is not None:
            raise ValueError("For cash, account_id and card_id must be null.")

    inst = payload.installments
    if m != "credit" and inst is not None:
        raise ValueError("Installments only allowed for credit method.")
    if inst is not None and inst.current > inst.total:
        raise ValueError("installments.current cannot be greater than installments.total.")
