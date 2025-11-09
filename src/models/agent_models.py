from pydantic import BaseModel
from dataclasses import dataclass
from typing import Any

@dataclass
class AgentConfig:
    id: str
    name: str
    description: str
    provider: str
    model: str
    prompt: str
    temperature: float
    max_tokens: int
    tools: Any

class AgentRequest(BaseModel):
    system: str = "Você é um assistente útil e responde em português."
    prompt: str

class AgentResponse(BaseModel):
    response: str