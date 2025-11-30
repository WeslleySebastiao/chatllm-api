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
        """
            Pega do MCP só as tools permitidas na config do agente.
        """

        all_tools = get_all_tools()  # precisa ver o formato real

        tools = []
        for name in cfg.tools:  # ex: ["hello_world"]
            t = all_tools.get(name)  # ou lista/loop, depende da sua implementação
            if not t:
                continue

            func = t["func"]  # função Python carregada lá no load_all_tools

            # Opcional: usar schema pra descrição
            schema = t.get("schema", {})
            desc = schema.get("description")
            if desc and not getattr(func, "__doc__", None):
                func.__doc__ = desc

            tools.append(func)

        return tools
  
    
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