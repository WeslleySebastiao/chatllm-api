from langchain_openai import ChatOpenAI
# Para o Agente
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from src.models.agent_models import AgentConfig, AgentRunRequestV2
from src.services.agent_runtime_v2 import AgentRuntimeV2
from src.mcp.registry import get_all_tools
from src.data.supaBase.supaBase_agent_db import SupaBaseAgentDB
from src.utils.log import start_run, finish_run_error, finish_run_success
import os


class AgentManagerV2:

    @staticmethod
    def run_agent_v2(run_request: AgentRunRequestV2) -> dict:

        run_ctx = start_run(
            agent_id=run_request.agent_id,
            user_id=run_request.user_id,
            session_id=run_request.session_id,
            agent_version=None,  
            model=None,    
            metadata={
                "route": "/agent/run/v2",
            },
        )

    
        try:
            cfg = SupaBaseAgentDB.get_agent(run_request.agent_id)
        except Exception as e:
            finish_run_error(
                run_id=run_ctx["run_id"],
                start_perf=run_ctx["start_perf"],
                error_type="ConfigLoadError",
                error_message=str(e),
                session_id=run_request.session_id,
            )
            return {"error": f"Failed to load agent config: {e}", "agent_id": id}

    
        try:
            final_output = AgentRuntimeV2.run_v2(user_prompt = run_request.message, 
                                                cfg=cfg, 
                                                user_id=run_request.user_id, 
                                                agent_id=run_request.agent_id, 
                                                session_id=run_request.session_id )
        except Exception as e:
            finish_run_error(
                run_id=run_ctx["run_id"],
                start_perf=run_ctx["start_perf"],
                error_type="AgentExecutionError",
                error_message=str(e),
                session_id=run_request.session_id,
                model=cfg.get("model"),
            )
            return {"error": f"Agent execution error: {e}", "agent_id": run_request.agent_id}
        
        usage = final_output.get("usage") or {}
        finish_run_success(
            run_id=run_ctx["run_id"],
            start_perf=run_ctx["start_perf"],
            session_id=final_output.get("session_id"),
            model=usage.get("model") or cfg.get("model"),
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            total_tokens=usage.get("total_tokens"),
            cost_usd=usage.get("cost_usd"),
            metadata_patch={
                "invoke_ms": usage.get("invoke_ms"),
            },
        )

        # 3. Retorna resultado padronizado
        return {"response": final_output["answer"], "session_id": final_output["session_id"]}
