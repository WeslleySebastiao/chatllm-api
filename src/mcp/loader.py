import importlib
from pathlib import Path

from src.mcp.registry import register_tool

TOOLS_DIR = Path(__file__).parent / "tools"


def load_all_tools():
    """
    Carrega tools determinísticamente:
    src.mcp.tools.<tool_dir>.tool deve exportar TOOL (BaseTool).
    """
    for tool_dir in TOOLS_DIR.iterdir():
        if not tool_dir.is_dir():
            continue

        module_name = f"src.mcp.tools.{tool_dir.name}.tool"

        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError:
            # se a pasta não tiver tool.py, ignora
            continue

        tool_obj = getattr(module, "TOOL", None)
        if tool_obj is None:
            # Sem TOOL, ignora (ou você pode dar erro aqui)
            continue

        register_tool(tool_obj)
