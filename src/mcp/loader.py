import importlib
import json
import os
from pathlib import Path
from . .mcp.registry import register_tool

TOOLS_DIR = Path(__file__).parent / "tools"

def load_all_tools():
    for tool_dir in TOOLS_DIR.iterdir():
        if not tool_dir.is_dir():
            continue
        
        func_path = tool_dir / "function.py"
        schema_path = tool_dir / "schema.json"

        if not func_path.exists() or not schema_path.exists():
            continue

        module_name = f"src.mcp.tools.{tool_dir.name}.function"
        module = importlib.import_module(module_name)

        # Pega a primeira função pública
        func = next(
            (getattr(module, attr) for attr in dir(module)
             if not attr.startswith("_") and callable(getattr(module, attr))),
            None
        )

        if func is None:
            continue

        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)

        register_tool(tool_dir.name, func, schema)
