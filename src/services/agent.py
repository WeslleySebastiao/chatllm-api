from langchain_openai import ChatOpenAI
# Para o Agente
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from src.data.db_control import DBControl
from src.models.agent_models import AgentConfig
from src.services.agent_runtime import AgentRuntime
from src.mcp.registry import get_all_tools
import os


class AgentManager:
    @staticmethod
    def recover_agent( id: str):
        return DBControl.load_agent(id)

    @staticmethod
    def run_agent(user_prompt: str, id: str) -> dict:
        # 1. Carrega a config persistida do agente
        try:
            cfg = AgentManager.recover_agent(id)
        except Exception as e:
            return {"error": f"Failed to load agent config: {e}", "agent_id": id}

        # 2. Executa o agente usando o runtime cognitivo
        try:
            final_output = AgentRuntime.run(user_prompt, cfg)
        except Exception as e:
            return {"error": f"Agent execution error: {e}", "agent_id": id}

        # 3. Retorna resultado padronizado
        return {"result": final_output, "agent_id": id}
    

    def _load_tools_for_agent(cfg) -> list:
        """Pega do MCP só as tools permitidas na config do agente."""

        all_tools = get_all_tools()

        allowed = set(cfg.tools)
        tool_objects = []

        for name, info in all_tools.items():
            if name not in allowed:
                continue
            
            tool_objects.append(info["func"])

        return tool_objects

    
    def _create_agent(self, agent: AgentConfig, **kwargs) -> ChatOpenAI:
        """
        Cria e retorna um AgentExecutor.
        """
        llm = ChatOpenAI(
            model=agent.model,
            temperature=agent.temperature,
            max_tokens=agent.max_tokens
        )
        
        return llm