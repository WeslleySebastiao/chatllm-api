from fastapi import APIRouter
from fastapi.responses import JSONResponse
import logging
from src.data.db_control import *
from src.core.config import settings
from src.models.agent_models import AgentRequest, AgentResponse, AgentConfig
from src.services.agent import AgentManager

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/health")
def health():
    """Verifica se a API está viva"""
    logger.info("Verificação de saúde OK.")
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}

@router.post("/agent")
async def create_agent(agent: AgentConfig):
    a = DBControl.create(
        name=agent.name,
        description=agent.description,
        provider=agent.provider,
        model=agent.model,
        tools=agent.tools,
        prompt=agent.prompt,
        temperature=agent.temperature,
        max_tokens=agent.max_tokens
    )
    DBControl.save_agent(a)
    return JSONResponse(
        content={"message": "Agente criado com sucesso", "agent_id": a.id},
        status_code=201
    )

@router.post("/agent/run")
async def run_agent_endpoint(user_prompt: str, id: str):
    return AgentManager.run_agent(user_prompt, id)

@router.get("/lsit_tools")
async def list_tools_endpoint():
    from src.services.mcp import MCPClient
    mcp = MCPClient(base_url="http://localhost:8000")
    tools = mcp.listar_tools()
    return {"tools": tools}