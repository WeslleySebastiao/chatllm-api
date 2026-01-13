import inspect
from src.mcp.registry import get_all_tools
from src.core.config import settings
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent

class AgentRuntime:

    @staticmethod
    def _load_tools_for_agent(cfg):
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
    def run(user_prompt: str, cfg):
        """
        Executa um agente LangChain baseado na configuração (cfg) e input.
        """

        # 1. Criar LLM
        model = ChatOpenAI(
            model=cfg["model"],
            temperature=cfg["temperature"],
            max_tokens=cfg["max_tokens"],
            api_key=settings.OPENAI_API_KEY,
        )

        # 2. Carregar tools
        tools = AgentRuntime._load_tools_for_agent(cfg)

        # 3. Criar agente
        agent = create_agent(
            model=model,
            tools=tools,
            system_prompt=cfg["prompt"],
        )

        # 4. Executar
        state = agent.invoke({
            "messages": [
                {"role": "user", "content": user_prompt}
            ]
        })

        # 5. Pegar resposta final
        messages = state.get("messages", [])
        final_msg = messages[-1].content if messages else ""

        return final_msg
