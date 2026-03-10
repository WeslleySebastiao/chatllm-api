"""
A2A Protocol Models — Pydantic v2
Baseado na spec: https://google.github.io/A2A/

Modelos do protocolo Agent-to-Agent para o ChatLLM API.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Any, Literal, Optional, Union

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Parts — blocos de conteúdo dentro de mensagens e artefatos
# ---------------------------------------------------------------------------

class TextPart(BaseModel):
    type: Literal["text"] = "text"
    text: str
    metadata: Optional[dict[str, Any]] = None


class FileContent(BaseModel):
    name: Optional[str] = None
    mime_type: Optional[str] = Field(None, alias="mimeType")
    bytes: Optional[str] = None  # base64-encoded
    uri: Optional[str] = None

    model_config = {"populate_by_name": True}


class FilePart(BaseModel):
    type: Literal["file"] = "file"
    file: FileContent
    metadata: Optional[dict[str, Any]] = None


class DataPart(BaseModel):
    type: Literal["data"] = "data"
    data: dict[str, Any]
    metadata: Optional[dict[str, Any]] = None


Part = Annotated[
    Union[TextPart, FilePart, DataPart],
    Field(discriminator="type"),
]


# ---------------------------------------------------------------------------
# Message
# ---------------------------------------------------------------------------

class Message(BaseModel):
    role: Literal["user", "agent"]
    parts: list[Part]
    metadata: Optional[dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Task State Machine
# ---------------------------------------------------------------------------

class TaskState(str, Enum):
    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class TaskStatus(BaseModel):
    state: TaskState
    message: Optional[Message] = None
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ---------------------------------------------------------------------------
# Artifact — resultado produzido pelo agente
# ---------------------------------------------------------------------------

class Artifact(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parts: list[Part]
    index: int = 0
    append: Optional[bool] = None
    last_chunk: Optional[bool] = Field(None, alias="lastChunk")
    metadata: Optional[dict[str, Any]] = None

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Task — unidade central de trabalho
# ---------------------------------------------------------------------------

class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: Optional[str] = Field(None, alias="sessionId")
    status: TaskStatus
    artifacts: list[Artifact] = Field(default_factory=list)
    history: list[Message] = Field(default_factory=list)
    metadata: Optional[dict[str, Any]] = None

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# JSON-RPC 2.0 — params para cada método
# ---------------------------------------------------------------------------

class TaskSendParams(BaseModel):
    id: Optional[str] = None
    session_id: Optional[str] = Field(None, alias="sessionId")
    message: Message
    history_length: Optional[int] = Field(None, alias="historyLength")
    metadata: Optional[dict[str, Any]] = None
    skill_id: Optional[str] = Field(None, alias="skillId")

    model_config = {"populate_by_name": True}


class TaskGetParams(BaseModel):
    id: str
    history_length: Optional[int] = Field(None, alias="historyLength")

    model_config = {"populate_by_name": True}


class TaskCancelParams(BaseModel):
    id: str
    metadata: Optional[dict[str, Any]] = None


# ---------------------------------------------------------------------------
# JSON-RPC 2.0 — request / response / error
# ---------------------------------------------------------------------------

class JSONRPCRequest(BaseModel):
    jsonrpc: Literal["2.0"] = "2.0"
    id: Optional[Union[str, int]] = None
    method: str
    params: Optional[Any] = None


class JSONRPCError(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None


class JSONRPCResponse(BaseModel):
    jsonrpc: Literal["2.0"] = "2.0"
    id: Optional[Union[str, int]] = None
    result: Optional[Any] = None
    error: Optional[JSONRPCError] = None


# ---------------------------------------------------------------------------
# Agent Card — apresentação do servidor A2A
# ---------------------------------------------------------------------------

class AgentCapabilities(BaseModel):
    streaming: bool = False
    push_notifications: bool = Field(False, alias="pushNotifications")
    state_transition_history: bool = Field(True, alias="stateTransitionHistory")

    model_config = {"populate_by_name": True}


class AgentAuthentication(BaseModel):
    schemes: list[str] = Field(default_factory=lambda: ["Bearer"])
    credentials: Optional[str] = None


class AgentSkill(BaseModel):
    id: str
    name: str
    description: str
    tags: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)
    input_modes: list[str] = Field(
        default_factory=lambda: ["text"], alias="inputModes"
    )
    output_modes: list[str] = Field(
        default_factory=lambda: ["text"], alias="outputModes"
    )

    model_config = {"populate_by_name": True}


class AgentCard(BaseModel):
    name: str
    description: str
    url: str
    version: str = "1.0.0"
    capabilities: AgentCapabilities = Field(default_factory=AgentCapabilities)
    authentication: AgentAuthentication = Field(default_factory=AgentAuthentication)
    skills: list[AgentSkill] = Field(default_factory=list)
    default_input_modes: list[str] = Field(
        default_factory=lambda: ["text"], alias="defaultInputModes"
    )
    default_output_modes: list[str] = Field(
        default_factory=lambda: ["text"], alias="defaultOutputModes"
    )

    model_config = {"populate_by_name": True}