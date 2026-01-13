from pydantic import BaseModel
from dataclasses import dataclass
from typing import Any
from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID

class AgentConfig(BaseModel):
    name: str
    provider: str
    model: str
    prompt: str
    id: Optional[UUID] = None
    description: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1024
    tools: List[str] = Field(default_factory=list)

class AgentRunRequest(BaseModel):
    user_prompt: str
    id: str

class AgentRequest(BaseModel):
    system: str = "Você é um assistente útil e responde em português."
    prompt: str

class AgentResponse(BaseModel):
    response: str