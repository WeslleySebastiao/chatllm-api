from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RequestContext:
    user_id: str  # uuid string


_request_ctx: ContextVar[Optional[RequestContext]] = ContextVar("request_ctx", default=None)


def set_request_context(ctx: RequestContext) -> None:
    _request_ctx.set(ctx)


def get_request_context() -> RequestContext:
    ctx = _request_ctx.get()
    if ctx is None:
        raise RuntimeError("RequestContext não definido. Defina user_id no início da request.")
    return ctx
