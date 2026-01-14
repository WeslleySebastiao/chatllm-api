from langchain_openai import ChatOpenAI
# Para o Agente
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from src.data.db_control import DBControl
from src.models.agent_models import AgentConfig, AgentRunRequestV2
from src.services.agent_runtime_v2 import AgentRuntimeV2
from src.mcp.registry import get_all_tools
from src.data.supaBase_agent_db import SupaBaseAgentDB
import os


class AgentManagerV2:

    @staticmethod
    def run_agent_v2(run_request: AgentRunRequestV2) -> dict:
        # 1. Carrega a config persistida do agente
        try:
            cfg = SupaBaseAgentDB.get_agent(run_request.agent_id)
        except Exception as e:
            return {"error": f"Failed to load agent config: {e}", "agent_id": id}

        # 2. Executa o agente usando o runtime cognitivo
        try:
            final_output = AgentRuntimeV2.run_v2(user_prompt = run_request.message, 
                                                cfg=cfg, 
                                                user_id=run_request.user_id, 
                                                agent_id=run_request.agent_id, 
                                                session_id=run_request.session_id )
        except Exception as e:
            return {"error": f"Agent execution error: {e}", "agent_id": id}

        # 3. Retorna resultado padronizado
        return {"response": final_output["answer"], "session_id": final_output["session_id"]}
