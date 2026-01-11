from langchain_core.tools import tool


@tool
async def hello_world(name: str):
    """Retorna o hello + nome da pessoa"""
    return f"Hello {name}"
