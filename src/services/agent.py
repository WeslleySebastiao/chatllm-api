from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage 
from src.core.config import settings


def run_agent(prompt: str) -> dict:
    llm = ChatOpenAI(
        model=settings.MODEL_NAME,
        openai_api_key=settings.OPENAI_API_KEY,
        temperature=0.7,
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"response": response.content}