import time
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import os
from dotenv import load_dotenv

load_dotenv()
# dependendo da sua versão do LangChain:
from langchain_community.callbacks import get_openai_callback

def quick_token_test():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))

    start = time.perf_counter()
    with get_openai_callback() as cb:
        resp = llm.invoke([HumanMessage(content="Me diga um haiku sobre logs e métricas.")])
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    print("Resposta:", resp.content)
    print("latency_ms:", elapsed_ms)
    print("prompt_tokens:", cb.prompt_tokens)
    print("completion_tokens:", cb.completion_tokens)
    print("total_tokens:", cb.total_tokens)
    

quick_token_test()