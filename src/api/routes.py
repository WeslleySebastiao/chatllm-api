from fastapi import APIRouter, Depends, Request
import asyncio
from fastapi.responses import JSONResponse
import logging
from src.data.db_control import *
from src.core.config import settings
from src.models.agent_models import AgentRequest, AgentResponse, AgentConfig, AgentRunRequest
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

@router.get("/agent")
async def list_agent():
   agent =  DBControl.list_agents()
   return agent

@router.post("/agent/run")
async def run_agent_endpoint(run_request: AgentRunRequest):
    return AgentManager.run_agent(run_request.user_prompt, run_request.id)

# # @router.get("/list_tools")
# # async def list_tools_endpoint(

# # #     mcp_client: MCPClient = Depends(get_global_mcp_client)
# # # ):
# # #     """
# # #     Lista as tools utilizando a conexão SSE global e persistente.
# # #     """
# # #     try:

# # #         tools = await asyncio.to_thread(mcp_client.listar_tools)
# # #         return {"tools": tools}

#     except Exception as e:
#         # É uma boa prática lidar com possíveis erros
#         return {"error": f"Falha ao listar tools: {str(e)}"}

# @router.post("/mcp")
# async def mcp_entrypoint(request: dict):
#     """
#     Recebe o JSON-RPC e envia para o modulo de MCP responsável
#     """
#     return await handle_mcp_request(request)