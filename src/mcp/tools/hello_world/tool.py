from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool


class HelloArgs(BaseModel):
    name: str = Field(..., description="Nome da pessoa a ser saudada.")


async def _run(name: str) -> str:
    return f"Hello {name}"


TOOL = StructuredTool.from_function(
    name="hello_world",
    description="Retorna uma saudação personalizada.",
    args_schema=HelloArgs,
    coroutine=_run,
)
