from fastapi import APIRouter
import logging
from src.core.config import settings
from src.models.agent_models import AgentRequest, AgentResponse
from src.services.agent import run_agent 

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/health")
def health():
    """Verifica se a API está viva"""
    logger.info("Verificação de saúde OK.")
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@router.post("/agent/run")
async def run_agent_endpoint(request: AgentRequest):
    return run_agent(request.prompt, request.system)

@router.get("/lsit_tools")
async def list_tools_endpoint():
    from src.services.mcp import MCPClient
    mcp = MCPClient(base_url="http://localhost:8000")
    tools = mcp.listar_tools()
    return {"tools": tools}