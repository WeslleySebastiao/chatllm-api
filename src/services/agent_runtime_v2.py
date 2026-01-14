import inspect
from src.mcp.registry import get_all_tools
from src.core.config import settings
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from src.data.supaBase_memory_db import SupaBaseMemoryDB 
class AgentRuntimeV2:

    @staticmethod
    def _load_tools_for_agent_v2(cfg):
        """
        Carrega as tools do MCP que estão permitidas na config do agente.
        Retorna uma lista de funções Python configuradas para o LangChain.
        """

        # Ex: {"hello_world": {"func": ..., "schema": ...}, ...}
        all_tools = get_all_tools()

        allowed = set(cfg["tools"]) 

        tool_functions = []

        for name, data in all_tools.items():

            # ignorar tools não permitidas na config
            if name not in allowed:
                continue

            func = data.get("func")
            schema = data.get("schema")

            # Se houver "description" no schema.json, injeta como docstring
            if schema and "description" in schema:
                if not inspect.getdoc(func):
                    func.__doc__ = schema["description"]

            tool_functions.append(func)

        print("cfg.tools =", cfg["tools"])

        print("tools carregadas =", [name for name in all_tools.keys()])

        print("tools finais =", tool_functions)

        return tool_functions



    @staticmethod
    def run_v2(user_prompt: str, cfg, user_id: str, agent_id: str, session_id: str | None = None, history_limit: int = 20):
        """
        Executa um agente LangChain baseado na configuração (cfg) e input.
        """

        #Teste incial da sessão
        session_id = SupaBaseMemoryDB.get_or_create_session(
            user_id=user_id,
            agent_id=agent_id,
            session_id=session_id,
        )

        # 1) salvar msg do user
        SupaBaseMemoryDB.save_message(session_id, "user", user_prompt)
        # 2) carregar histórico
        history = SupaBaseMemoryDB.load_history(session_id, limit=history_limit)

        #Criar LLM
        model = ChatOpenAI(
            model=cfg["model"],
            temperature=cfg["temperature"],
            max_tokens=cfg["max_tokens"],
            api_key=settings.OPENAI_API_KEY,
        )

        #Carregar tools
        tools = AgentRuntimeV2._load_tools_for_agent_v2(cfg)

        #Criar agente
        agent = create_agent(
            model=model,
            tools=tools,
            system_prompt=cfg["prompt"],
        )

        messages = [{"role": m["role"], "content": m["content"]} for m in history]

        #V2 Executar
        state = agent.invoke({"messages": messages})

        #Pegar resposta final
        messages = state.get("messages", [])
        final_msg = messages[-1].content if messages else ""

        #salvar resposta
        SupaBaseMemoryDB.save_message(session_id, "assistant", final_msg)


        return {"session_id": session_id, "answer": final_msg}
