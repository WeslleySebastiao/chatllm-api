from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from src.core.config import settings


def run_agent(prompt: str, system: str) -> dict:
    llm = ChatOpenAI(
        model=settings.MODEL_NAME,
        openai_api_key=settings.OPENAI_API_KEY,
        temperature=0.7,
    )

    # Cria o template do prompt com system + human
    template = ChatPromptTemplate.from_messages([
        ("system", system),
        ("human", "{user_input}")
    ])

    # Preenche o template dinamicamente
    messages = template.format_messages(user_input=prompt)

    # Envia pro modelo
    response = llm.invoke(messages)

    return {"response": response.content}