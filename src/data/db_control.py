 

from __future__ import annotations
import json, os
from . .models.agent_models import AgentConfig
from pathlib import Path
from typing import Any
from dataclasses import dataclass, asdict
from uuid import uuid4

# pasta base dos arquivos
DATA_DIR = Path("src/data/agents")
DATA_DIR.mkdir(parents=True, exist_ok=True)

class DBControl:

    @staticmethod
    def create(name: str, description: str, provider: str, model: str, tools: Any, prompt: str, temperature: float = 0.7, max_tokens: int = 2048) -> AgentConfig:
        """Cria um novo registro com id único."""
        return AgentConfig(
            id= f"{name}_{uuid4()}",  # gera um id único
            name=name,
            description=description,
            provider=provider,
            model=model,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max,
            tools=tools
        )

    # ---------- Funções utilitárias ----------
    def save_agent(agent: AgentConfig):
        """Salva o registro em JSON localmente."""
        path = DATA_DIR / f"{agent.id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(agent), f, ensure_ascii=False, indent=2)

    def load_agent(agent_id: str) -> AgentConfig | None:
        """Carrega um agente pelo ID."""
        path = DATA_DIR / f"{agent_id}.json"
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return AgentConfig(**data)

    def list_agents() -> list[AgentConfig]:
        """Lista todos os agentes salvos."""
        agents = []
        for file in DATA_DIR.glob("*.json"):
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                agents.append(AgentConfig(**data))
        return agents

# ---------- Exemplo de uso ----------
if __name__ == "__main__":
    # cria um agente
    agent = DBControl.create(
        name="Agente",
        description="Agente conversacional local",
        provider="OpenAI",
        model="gpt-4o-mini",
        prompt = "Você responde ta?",
        tools=["memory", "search"]
    )

    DBControl.save_agent(agent)
    print("✅ Agente salvo:", agent.id)

    loaded = DBControl.load_agent(agent.id)
    print("🔁 Agente carregado:", loaded)

    print("📜 Lista de todos:")
    for a in DBControl.list_agents():
        print("-", a.name, "->", a.id)