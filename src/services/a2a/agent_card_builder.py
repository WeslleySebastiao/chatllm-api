"""
Agent Card Builder — Monta o AgentCard A2A a partir dos agentes cadastrados no banco.

Este é o componente que conecta o mundo A2A com o chatllm-api:
os agentes persistidos no Supabase viram skills no Agent Card.
"""
from __future__ import annotations

import logging
from typing import Optional

from src.core.config import settings
from src.data.supaBase.supaBase_agent_db import SupaBaseAgentDB
from src.models.a2a.models import (
    AgentCard,
    AgentCapabilities,
    AgentAuthentication,
    AgentSkill,
)

logger = logging.getLogger(__name__)


class AgentCardBuilder:
    """
    Constrói o AgentCard consultando os agentes no banco.
    Cada agente cadastrado vira um AgentSkill.

    skill_id  = UUID do agente (identificador único e estável)
    name      = nome do agente (legível para humanos)
    """

    @staticmethod
    def build(base_url: Optional[str] = None) -> AgentCard:
        url = base_url or getattr(settings, "A2A_BASE_URL", "http://localhost:8080")

        try:
            agents = SupaBaseAgentDB.list_agents()
        except Exception as e:
            logger.error(f"[A2A] Erro ao listar agentes para Agent Card: {e}")
            agents = []

        skills: list[AgentSkill] = []
        for agent in agents:
            skill = AgentSkill(
                id=str(agent["id"]),
                name=agent.get("name", "Unnamed Agent"),
                description=agent.get("description") or agent.get("name", ""),
                tags=_derive_tags(agent),
                examples=[],
            )
            skills.append(skill)

        logger.info(f"[A2A] Agent Card montado com {len(skills)} skill(s)")

        return AgentCard(
            name=settings.APP_NAME,
            description=(
                "ChatLLM API — Servidor de agentes LLM orquestrados com LangChain. "
                "Suporta ferramentas MCP, memória conversacional e telemetria."
            ),
            url=url,
            version=settings.APP_VERSION,
            capabilities=AgentCapabilities(
                streaming=False,  # Fase 3
                push_notifications=False,
                state_transition_history=True,
            ),
            authentication=AgentAuthentication(
                schemes=["Bearer"],
            ),
            skills=skills,
        )


def _derive_tags(agent: dict) -> list[str]:
    """
    Gera tags básicas a partir da configuração do agente.
    Pode ser enriquecido depois com NLP ou campos explícitos.
    """
    tags: list[str] = []

    # Adiciona provider e modelo como tags
    if agent.get("provider"):
        tags.append(agent["provider"])
    if agent.get("model"):
        tags.append(agent["model"])

    # Se tem tools, marca
    tools = agent.get("tools") or []
    if tools:
        tags.append("tool-enabled")

    return tags