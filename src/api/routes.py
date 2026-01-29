from fastapi import APIRouter, Depends, Request
import asyncio
from fastapi.responses import JSONResponse
import logging
from src.core.config import settings
from src.models.agent_models import AgentConfig, AgentRunRequest, AgentRunRequestV2
from src.services.agent_v2 import AgentManagerV2
from src.mcp.registry import get_all_tools
from src.data.supaBase.supaBase_agent_db import SupaBaseAgentDB
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/health")
def health():
    """Verifica se a API está viva"""
    logger.info("Verificação de saúde OK.")
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}

@router.post("/agent")
async def create_agent(agent: AgentConfig):
    agent = SupaBaseAgentDB.create_agent(
        name=agent.name,
        description=agent.description,
        provider=agent.provider,
        model=agent.model,
        tools=agent.tools,
        prompt=agent.prompt,
        temperature=agent.temperature,
        max_tokens=agent.max_tokens,
    )

    return JSONResponse(
        content=jsonable_encoder({
            "message": "Agente criado com sucesso",
            "agent_id": agent["id"],
            "agent": agent,
        }),
        status_code=201
    )

@router.get("/agent")
async def list_agent():
    agents = SupaBaseAgentDB.list_agents()
    # converter UUID/datetime pra string se necessário (depende do seu JSON encoder)
    for a in agents:
        a["id"] = str(a["id"])
        if a.get("created_at"): a["created_at"] = a["created_at"].isoformat()
        if a.get("updated_at"): a["updated_at"] = a["updated_at"].isoformat()
    return agents

@router.post("/agent/run")
async def run_agent_endpoint(run_request: AgentRunRequest):
    return AgentManagerV2.run_agent_v2(run_request)

@router.get("/list_tools")
async def list_tools_endpoint():
    tools = get_all_tools()

    
    response = []
    for name, data in tools.items():
        response.append({
            "name": name,
            "schema": data["schema"],  # schema da tool (JSON)
        })

    return {"tools": response}

@router.post("/agent/run/v2")
async def run_agent_endpoint(run_request: AgentRunRequestV2):
    return AgentManagerV2.run_agent_v2(run_request)