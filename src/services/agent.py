from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from src.core.config import settings
from src.data.db_control import DBControl
from src.models.agent_models import *

class AgentManager:
    def recover_agent(id: str):
        return DBControl.load_agent(id)

    def run_agent(self, prompt: str, id: str) -> dict:
        #1
        agent = self.recover_agent(id)

        #2
        prompt = [
            {"role": "system", "content": f"{agent.promt}"},
            {"role": "user", "content": "Write a haiku about spring"},
            {"role": "assistant", "content": "Cherry blossoms bloom..."}
        ]

        #3
        response = agent.invoke(prompt)

        return response