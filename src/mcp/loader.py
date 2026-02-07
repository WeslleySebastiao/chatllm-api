import importlib
from pathlib import Path
from src.mcp.registry import register_tool

TOOLS_DIR = Path(__file__).parent / "tools"


def load_all_tools():
    """
    Carrega tools determinísticamente:
    - Cada subpasta em src/mcp/tools é um "grupo" (ex: financial_tools)
    - Dentro do grupo, carrega todos os .py (exceto __init__.py e _*.py)
    - Cada arquivo deve exportar TOOL (BaseTool/StructuredTool)
    """

    for tool_dir in sorted([p for p in TOOLS_DIR.iterdir() if p.is_dir()], key=lambda p: p.name):
        # Ordena arquivos para determinismo
        py_files = sorted(
            [f for f in tool_dir.glob("*.py") if f.is_file() and f.name != "__init__.py" and not f.name.startswith("_")],
            key=lambda f: f.name,
        )

        for py_file in py_files:
            module_name = f"src.mcp.tools.{tool_dir.name}.{py_file.stem}"

            try:
                module = importlib.import_module(module_name)
            except Exception as e:
                print(f"[TOOLS] Erro ao importar {module_name}: {type(e).__name__}: {e}")
                continue

            tool_obj = getattr(module, "TOOL", None)
            if tool_obj is None:
                continue

            register_tool(tool_obj)
            print(f"[TOOLS] Registrada: {tool_obj.name} ({module_name})")