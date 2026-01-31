from pydantic import BaseModel
from dataclasses import dataclass
from typing import Any
from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID

class AgentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=80)
    description: Optional[str] = Field(None, max_length=500)
    provider: Optional[str] = Field(None, min_length=1, max_length=40)
    model: Optional[str] = Field(None, min_length=1, max_length=80)
    tools: Optional[List[str]] = None
    prompt: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=200000)  # ajuste limite se quiser
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
class AgentRunRequestV2(BaseModel):
    agent_id: str
    user_id: str
    session_id: Optional[str] = None
    message: str
class AgentRequest(BaseModel):
    system: str = "Você é um assistente útil e responde em português."
    prompt: str

class AgentResponse(BaseModel):
    response: str

class AgentResponseV2(BaseModel):
    session_id: str
    response: str

