from pydantic import BaseModel, Field
from typing import Optional, Literal
from uuid import UUID
from datetime import date

TxnType = Literal["expense", "income"]
PaymentMethod = Literal["pix", "debit", "credit", "cash", "transfer"]

class InstallmentsIn(BaseModel):
    total: int = Field(ge=1)
    current: int = Field(ge=1)

class PaymentIn(BaseModel):
    method: PaymentMethod
    account_id: Optional[UUID] = None
    card_id: Optional[UUID] = None

class TransactionUpsertIn(BaseModel):
    id: Optional[UUID] = None
    type: TxnType
    amount_cents: int = Field(gt=0)
    currency: str = Field(default="BRL", min_length=3, max_length=3)
    txn_date: date
    description: str = Field(min_length=1)
    merchant: Optional[str] = None
    notes: Optional[str] = None
    category_id: Optional[UUID] = None
    payment: PaymentIn
    installments: Optional[InstallmentsIn] = None