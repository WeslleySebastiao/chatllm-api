from langchain_openai import ChatOpenAI
# Para o Agente
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from src.data.db_control import DBControl
from src.models.agent_models import AgentConfig
from src.core.config import settings
import os


class AgentManager:
    @staticmethod
    def recover_agent( id: str):
        return DBControl.load_agent(id)

    @staticmethod
    def run_agent(user_prompt: str, id: str) -> dict:
        # Recuperar config do agente

        try:
            cfg = AgentManager.recover_agent(id)

        except Exception as e:
            return {"error": f"Failed to load agent config: {e}", "agent_id": id}
        
        model = ChatOpenAI(model=cfg.model, 
                           temperature=cfg.temperature, 
                           max_tokens=cfg.max_tokens,
                           openai_api_key=settings.OPENAI_API_KEY
                           )
        
        messages = [
            {"role": "system", "content": cfg.prompt},
            {"role": "user", "content": user_prompt}
        ]

        result = model.invoke(messages)
        return {"result": result, "agent_id": id}
  
    
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