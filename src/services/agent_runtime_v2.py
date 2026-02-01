import inspect
import time
from src.mcp.registry import get_tools_by_names
from src.core.config import settings
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_community.callbacks import get_openai_callback
from src.data.supaBase.supaBase_memory_db import SupaBaseMemoryDB 
class AgentRuntimeV2:


    @staticmethod
    def _load_tools_for_agent_v2(cfg):
        allowed = cfg.get("tools", [])
        return get_tools_by_names(allowed)



    @staticmethod
    async def run_v2(user_prompt: str, cfg, user_id: str, agent_id: str, session_id: str | None = None, history_limit: int = 20):
        """
        Executa um agente LangChain baseado na configuração (cfg) e input.
        """

        session_id = SupaBaseMemoryDB.get_or_create_session(
            user_id=user_id,
            agent_id=agent_id,
            session_id=session_id,
        )


        SupaBaseMemoryDB.save_message(session_id, "user", user_prompt)

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

        invoke_start = time.perf_counter()
        with get_openai_callback() as cb:
            state = await agent.ainvoke({"messages": messages})
        invoke_ms = int((time.perf_counter() - invoke_start) * 1000)

        usage = {
            "prompt_tokens": cb.prompt_tokens,
            "completion_tokens": cb.completion_tokens,
            "total_tokens": cb.total_tokens,
            "cost_usd": float(getattr(cb, "total_cost", 0.0) or 0.0),
            "invoke_ms": invoke_ms,
            "model": cfg["model"],
        }
        
        #Pegar resposta final
        messages = state.get("messages", [])
        final_msg = messages[-1].content if messages else ""

        #salvar resposta
        SupaBaseMemoryDB.save_message(session_id, "assistant", final_msg)


        return {"session_id": session_id, "answer": final_msg, "usage": usage}
