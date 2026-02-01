"""
Registry de tools (LangChain tools).
Guarda cada tool por nome e permite recuperar por lista de nomes (por agente).
"""

from __future__ import annotations
from typing import Dict, List
from langchain_core.tools import BaseTool

TOOLS: Dict[str, BaseTool] = {}


def register_tool(tool_obj: BaseTool):
    """
    Registra uma tool do LangChain.
    O nome é tool_obj.name (estável e usado no cfg["tools"]).
    """
    TOOLS[tool_obj.name] = tool_obj


def get_all_tools() -> Dict[str, BaseTool]:
    return TOOLS


def get_tools_by_names(names: List[str]) -> List[BaseTool]:
    """
    Retorna só as tools cujo nome está na lista.
    Mantém a ordem do cfg (bom pra debug e consistência).
    """
    out: List[BaseTool] = []
    for n in names:
        t = TOOLS.get(n)
        if t is not None:
            out.append(t)
    return out
