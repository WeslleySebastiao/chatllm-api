from fastapi import APIRouter
from fastapi import HTTPException
from uuid import UUID
from src.core.config import settings
from src.models.agent_models import AgentConfig, AgentRunRequest, AgentRunRequestV2, AgentUpdate
from src.services.agent_v2 import AgentManagerV2
from src.mcp.registry import get_all_tools
from src.data.supaBase.supaBase_agent_db import SupaBaseAgentDB
from fastapi.encoders import jsonable_encoder

router = APIRouter(tags=['Agent Operation'])


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

    return {
            "message": "Agente criado com sucesso",
            "agent_id": agent["id"],
            "agent": agent,
        }

@router.patch("/agent/{agent_id}")
async def update_agent(agent_id: UUID, payload: AgentUpdate):
    existing = SupaBaseAgentDB.get_agent(agent_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Agente não encontrado")

    patch = payload.model_dump(exclude_unset=True)

    if not patch:
        return {
            "message": "Nenhum campo enviado para atualização",
            "agent": jsonable_encoder(existing),
        }

    updated = SupaBaseAgentDB.update_agent(agent_id, patch)
    if not updated:
        raise HTTPException(status_code=404, detail="Agente não encontrado")

    return {
        "message": "Agente atualizado com sucesso",
        "agent": jsonable_encoder(updated),
    }

@router.delete("/agent/{agent_id}", status_code=204)
async def delete_agent(agent_id: UUID):
    deleted = SupaBaseAgentDB.delete_agent(agent_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Agente não encontrado")

    return

@router.get("/agent/{agent_id}")
async def list_especific_agent(agent_id: UUID):
    agent = SupaBaseAgentDB.get_agent(agent_id)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent["id"] = str(agent["id"])
    if agent.get("created_at"):
        agent["created_at"] = agent["created_at"].isoformat()
    if agent.get("updated_at"):
        agent["updated_at"] = agent["updated_at"].isoformat()

    return agent

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
    return await AgentManagerV2.run_agent_v2(run_request)