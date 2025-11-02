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