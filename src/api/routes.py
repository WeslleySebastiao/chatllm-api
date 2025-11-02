from fastapi import APIRouter
import logging
from src.core.config import settings
from src.services.agent import run_agent 
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/health")
def health():
    """Verifica se a API está viva"""
    logger.info("Verificação de saúde OK.")
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}

class AgentRequest(BaseModel):
    prompt: str

@router.post("/agent/run")
async def run_agent_endpoint(request: AgentRequest):
    return run_agent(request.prompt)