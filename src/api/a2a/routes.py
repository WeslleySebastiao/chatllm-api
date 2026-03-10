"""
Rotas A2A — Endpoints do protocolo Agent-to-Agent.

Fase 1: GET /.well-known/agent.json  (Agent Card / Discovery)
Fase 2: POST /a2a                     (JSON-RPC: tasks/send, tasks/get, tasks/cancel)
Fase 3: POST /a2a                     (JSON-RPC: tasks/sendSubscribe via SSE)
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from src.services.a2a.agent_card_builder import AgentCardBuilder

logger = logging.getLogger(__name__)

router_a2a = APIRouter(tags=["A2A Protocol"])


@router_a2a.get("/.well-known/agent.json")
async def get_agent_card(request: Request):
    """
    Agent Card — Discovery endpoint do protocolo A2A.

    Retorna um JSON descrevendo o servidor, suas capacidades
    e os agentes (skills) disponíveis.

    Este endpoint é público (sem autenticação) conforme a spec A2A.
    """
    # Reconstrói a base_url a partir do request, caso não esteja configurada
    base_url = str(request.base_url).rstrip("/")

    logger.info(
        "[A2A] Agent Card solicitado de %s",
        request.client.host if request.client else "unknown",
    )

    card = AgentCardBuilder.build(base_url=base_url)

    return JSONResponse(
        content=card.model_dump(by_alias=True, exclude_none=True),
        headers={
            # Cache por 5 minutos — evita queries ao banco a cada request
            "Cache-Control": "public, max-age=300",
        },
    )