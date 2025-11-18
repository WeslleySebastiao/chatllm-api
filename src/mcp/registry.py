"""Arquivo responsável por registrar, organizar e executar as tools"""

TOOLS = {}

def register_tool(name, func, schema):
    TOOLS[name] = {
        "func": func,
        "schema": schema
    }

def get_openai_format_tools():
    return [
        {
            "type": "function",
            "function": {
                "name": name,
                "description": schema["description"],
                "parameters": schema["parameters"]
            }
        }
        for name, schema in TOOLS.items()
    ]

async def invoke_tool(name, arguments):
    tool = TOOLS[name]
    return await tool["func"](**arguments)
