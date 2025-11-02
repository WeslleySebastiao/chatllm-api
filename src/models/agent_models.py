from pydantic import BaseModel

class AgentRequest(BaseModel):
    system: str = "Você é um assistente útil e responde em português."
    prompt: str

class AgentResponse(BaseModel):
    response: str